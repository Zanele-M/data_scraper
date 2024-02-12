from django.http import HttpResponse, JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
import logging
import re
from rest_framework.response import Response
import hashlib

from django.utils import timezone
from datetime import timedelta
from decouple import config


from api.models.program import Program
from api.models.search_results import SearchResults
from api.models.search_term import SearchTerm
from api.serializer.search_result import SearchResultsSerializer
from api.utils.google_search import fetch_google_search
from api.utils.html_content_parser import extract_html_element_attribute, download_image

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 50


def extract_icon(url: str, search_term_instance: SearchTerm) -> HttpResponse | Response:
    """
    Extract the required meta attribute from the URL and respond with the image.
    """

    if search_term_instance.attempts >= MAX_ATTEMPTS:
        return JsonResponse({'message': 'Maximum number of attempts reached for the given program name'},
                            status=status.HTTP_400_BAD_REQUEST)

    # Update attempt count for the search term
    search_term_instance.attempts += 1
    search_term_instance.save()

    meta_search_criteria = {"name": "meta", "attrs": {"property": "og:image"}}
    meta_attribute = "content"
    meta_result = extract_html_element_attribute(url, meta_search_criteria, meta_attribute)
    if meta_result:
        content_type, image_data = download_image(meta_result)
        if content_type and image_data:
            return HttpResponse(image_data, content_type=content_type)
        else:
            return JsonResponse({'message': 'Failed to download icon from downloading site'},
                                status=status.HTTP_404_NOT_FOUND)
    else:
        return JsonResponse({'message': 'Icon not found'}, status=status.HTTP_404_NOT_FOUND)


def search_icon(program_name: str, program_id: str) -> HttpResponse:
    """
    Perform a new search for the program and extract the required attribute.
    """
    sites = [
        {'site': 'computerbase.de', 'inurl': 'downloads', 'url_pattern': 'https://www.computerbase.de/downloads/*'},
        {'site': 'uptodown.com', 'inurl': 'windows', 'url_pattern': 'https://*.uptodown.com/windows'},
    ]

    program_instance, _ = Program.objects.get_or_create(program_name=program_name, program_id=program_id)

    for site_info in sites:
        site = site_info.get('site')
        inurl = site_info.get('inurl')
        pattern = site_info.get('url_pattern')

        search_term_instance, _ = SearchTerm.objects.get_or_create(term=f"{program_name} site:{site} inurl:{inurl}")
        if search_term_instance.attempts >= MAX_ATTEMPTS:
            return HttpResponse({'message': 'Maximum number of attempts reached for this search term'},
                                status=status.HTTP_400_BAD_REQUEST)

        search_term_instance.attempts += 1
        search_term_instance.save()

        search_term = f"{program_name} site:{site} inurl:{inurl}"
        google_response = fetch_google_search(search_term, 3)

        if not google_response or isinstance(google_response, list) and google_response[0].get("error"):
            logger.error(f"No links found in the Google API response for {search_term}")
            continue

        for item in google_response:
            SearchResults.objects.create(
                search_term=search_term_instance,
                program_id=program_instance,
                position=item['position'],
                url=item['link']
            )

            if re.match(pattern, item['link']):
                extraction_response = extract_icon(item['link'], search_term_instance)
                if extraction_response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]:
                    return extraction_response  # Successfully found and extracted, or not found but processed
                else:
                    # If the extraction failed, log and attempt the next site
                    logger.error("Error during extraction, attempting next site if available.")

    return JsonResponse({'message': 'No links found across all sites'}, status=status.HTTP_404_NOT_FOUND)


class IconViewSet(viewsets.ModelViewSet):
    serializer_class = SearchResultsSerializer
    queryset = SearchResults.objects.all()
    @action(detail=False, methods=['post'])
    def download_icon(self, request):

        """
        Custom action to fetch or search for an icon based on `program_name` and `program_id` from POST data.
        """
        program_name = request.data.get("program_name")
        program_id = request.data.get("program_id")
        provided_hash = request.headers.get("X-Hash")
        api_key = request.headers.get("api-key")

        #Validate api key
        if not api_key:
            return JsonResponse({"message": "API key is missing."}, status=status.HTTP_401_UNAUTHORIZED)

        if api_key != config('API_KEY'):
            return JsonResponse({"message": "Invalid API key."}, status=status.HTTP_401_UNAUTHORIZED)

        # Validate program name and program ID lengths
        if not program_name or not program_id:
            return JsonResponse({"message": "Missing program name or program Id."}, status=status.HTTP_400_BAD_REQUEST)
        if len(program_name) > 80:
            return JsonResponse({"message": "Program name is too long."}, status=status.HTTP_400_BAD_REQUEST)

        hash_string = f"{program_name}{program_id}{config('SECRET_KEY')}"
        expected_hash = hashlib.sha256(hash_string.encode()).hexdigest()

        if not provided_hash or provided_hash != expected_hash:
            return JsonResponse({"message": "Hash validation failed."}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate the date one month ago
        one_month_ago = timezone.now() - timedelta(days=30)

        # Filter the queryset directly within this action
        queryset = self.queryset.filter(
            program_id__program_id=program_id,
            program_id__program_name=program_name,
            last_updated__gte=one_month_ago
        ).first()
        try:
            if queryset and queryset.url:
                # Use the existing search result if it's found
                search_term_instance = queryset.search_term
                if queryset:
                    return extract_icon(queryset.url, search_term_instance)

            # Perform a new search and extraction if no existing result is found
            return search_icon(program_name, program_id)

        except Exception as e:
            print(e)
            return JsonResponse({'message': 'An unexpected error occurred.'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
