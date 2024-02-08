import requests
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
import logging
import re
from rest_framework.response import Response
from time import sleep
import hashlib


from django.utils import timezone
from datetime import timedelta
from rest_framework_api_key.permissions import HasAPIKey

from api.models.program import Program
from api.models.search_results import SearchResults
from api.models.search_term import SearchTerm
from api.serializer.search_result import SearchResultsSerializer
from api.utils.google_search import fetch_google_search
from api.utils.html_content_parser import extract_html_element_attribute

logger = logging.getLogger(__name__)


def extract_and_respond(url: str, search_term_instance: SearchTerm) -> HttpResponse | Response:
    """
    Extract the required meta attribute from the URL and respond with the image.
    """

    if search_term_instance.attempts >= 11:
        return Response({'message': 'Maximum number of attempts reached for the given program name'},
                        status=status.HTTP_400_BAD_REQUEST)

    # Update attempt count for the search term
    search_term_instance.attempts = 1
    search_term_instance.save()

    meta_search_criteria = {"name": "meta", "attrs": {"property": "og:image"}}
    meta_attribute = "content"
    meta_result = extract_html_element_attribute(url, meta_search_criteria, meta_attribute)
    if meta_result:
        content_type, image_data = download_image(meta_result)
        if content_type and image_data:
            return HttpResponse(image_data, content_type=content_type)
        else:
            return Response({'message': 'Failed to download icon from downloading site'}, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response({'message': 'Icon not found'}, status=status.HTTP_404_NOT_FOUND)


def perform_search_and_extraction(program_name: str, program_id: str) -> Response:
    """
    Perform a new search for the program and extract the required attribute.
    """
    # Define URL patterns for each site
    sites = [
        {'site': 'computerbase.de', 'inurl': 'downloads', 'url_pattern': 'https://www.computerbase.de/downloads/*'},
        {'site': 'uptodown.com', 'inurl': 'windows', 'url_pattern': 'https://*.uptodown.com/windows'},
    ]

    # Create or get the SearchTerm and Program instance once for all URLs
    program_instance, _ = Program.objects.get_or_create(program_name=program_name, program_Id=program_id)

    for site_info in sites:
        site = site_info.get('site')
        inurl = site_info.get('inurl')
        pattern = site_info.get('url_pattern')

        search_term_instance, _ = SearchTerm.objects.get_or_create(term=f"{program_name} site:{site} inurl:{inurl}")
        if search_term_instance.attempts >= 11:
            return Response({'message': 'Maximum number of attempts reached for this search term'},
                            status=status.HTTP_400_BAD_REQUEST)

        search_term_instance.attempts = 1
        search_term_instance.save()

        search_term = f"{program_name} site:{site} inurl:{inurl}"
        google_response = fetch_google_search(search_term, 3)

        first_match_found = False

        if isinstance(google_response, list) and google_response[0].get("error"):
            # Return the error message as a response
            return Response({'message': google_response[0]["error"]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        for item in google_response:
            # Save the URL regardless of match
            SearchResults.objects.create(
                search_term=search_term_instance,
                program_Id=program_instance,
                position=item['position'],
                url=item['link']
            )

            if not first_match_found and re.match(pattern, item['link']):
                return extract_and_respond(item['link'], search_term_instance)

        if not first_match_found:
            logger.info(f"No matching results found for {program_name} on the site {site}.")

    return Response({'message': 'No matching results found'}, status=status.HTTP_404_NOT_FOUND)


def download_image(url: str):
    """
    Download an image from the URL with up to 3 retries and exponential backoff.

    Args:
        url (str): The URL of the image to download.

    Returns:
        A tuple of (content_type, image_data) if successful, or (None, None) on failure.
    """
    attempts = 0
    backoff_factor = 1  # Start with 1 second
    max_attempts = 3
    while attempts < max_attempts:
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            content_type = response.headers.get('Content-Type')
            return content_type, response.content
        except requests.RequestException as e:
            attempts = 1
            sleep_time = backoff_factor * (2 ** (attempts - 1))  # Exponential backoff
            logger.error(
                f"Error downloading image on attempt {attempts}/{max_attempts}: {e}. Retrying in {sleep_time} seconds.")
            sleep(sleep_time)
    return None, None


class IconViewSet(viewsets.ModelViewSet):
    serializer_class = SearchResultsSerializer
    queryset = SearchResults.objects.all()

    @action(detail=False, methods=['post'], permission_classes=[HasAPIKey])
    def download_icon(self, request):
        """
        Custom action to fetch or search for an icon based on `program_name` and `program_id` from POST data.
        """
        program_name = request.data.get("program_name")
        program_id = request.data.get("program_id")
        provided_hash = request.headers.get("X-Hash")

        # Validate program name and program ID lengths
        if not program_name or not program_id:
            return Response({"message": "Missing program name or program ID."}, status=status.HTTP_400_BAD_REQUEST)
        if len(program_name) > 80:
            return Response({"message": "Program name is too long."}, status=status.HTTP_400_BAD_REQUEST)

        # Hash validation
        hash_string = f"{program_name}{program_id}"
        expected_hash = hashlib.sha256(hash_string.encode()).hexdigest()

        if not provided_hash or provided_hash != expected_hash:
            return Response({"message": "Hash validation failed."}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate the date one month ago
        one_month_ago = timezone.now() - timedelta(days=30)

        # Filter the queryset directly within this action
        queryset = self.queryset.filter(
            program_Id__program_Id=program_id,
            program_Id__program_name=program_name,
            last_updated__gte=one_month_ago
        ).first()
        try:
            if queryset and queryset.url:
                # Use the existing search result if it's found
                search_term_instance = queryset.search_term
                if queryset:
                    return extract_and_respond(queryset.url, search_term_instance)

            # Perform a new search and extraction if no existing result is found
            response = perform_search_and_extraction(program_name, program_id)
            # Check if response contains an error message
            if isinstance(response, list) and response[0].get("error"):
                # Return the error message as a response
                return Response({'message': response[0]["error"]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Return response normally
            return response

        except Exception as e:
            # Handle any unexpected exceptions
            return Response({'message': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
