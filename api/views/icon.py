import base64
import tempfile
import time
from io import BytesIO

from PIL import Image
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
from api.utils.rembg import rembg

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 1


def extract_icon(url: str, search_term_instance: SearchTerm, program_name: str) -> HttpResponse | Response:
    """
    Extract the required meta attribute from the URL and respond with the image.
    """
    start_time = time.time()
    # Update attempt count for the search term
    search_term_instance.attempts += 1
    search_term_instance.save()

    meta_search_criteria = {"name": "meta", "attrs": {"property": "og:image"}}
    meta_attribute = "content"
    meta_result = extract_html_element_attribute(url, meta_search_criteria, meta_attribute)
    execution_time = time.time() - start_time
    print(f"Extract icon execution time for {program_name}: {execution_time} seconds.")
    if isinstance(meta_result, list) and meta_result and isinstance(meta_result[0], dict) and "error" in meta_result[0]:
        return JsonResponse({'error': f'Could not parse from the url: {url} for program {program_name}'},
                            status=status.HTTP_200_OK)
    elif isinstance(meta_result, list) and not meta_result:
        return JsonResponse({'error': f'Could not parse from the url: {url} for program {program_name}'},
                            status=status.HTTP_200_OK)
    else:
        image_url = meta_result[0] if isinstance(meta_result, list) else meta_result
        content_type, image_data = download_image(image_url)
        if content_type and image_data:
            # Save the downloaded image to a temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file_path = temp_file.name
            with open(temp_file_path, 'wb') as file:
                file.write(image_data)

            # Open the temporary file with PIL to check for transparency
            icon = Image.open(temp_file_path)
            processed_image = rembg(temp_file_path)
            if processed_image:
                # Convert PIL Image to bytes
                img_byte_arr = BytesIO()
                # processed_image.save(img_byte_arr, format=content_type)
                base64_encoded_data = base64.b64encode(img_byte_arr.getvalue())
            else:
                # Fallback if processing failed
                base64_encoded_data = base64.b64encode(image_data)

            base64_string = base64_encoded_data.decode('utf-8')
            image_data_uri = f'data:{content_type};base64,{base64_string}'
            return JsonResponse({'image_data': image_data_uri}, status=status.HTTP_200_OK)


def search_icon(program_name: str, program_id: str) -> HttpResponse:
    """
    Perform a new search for the program and extract the required attribute.
    """
    start_time = time.time()
    sites = [
        {'site': 'computerbase.de', 'inurl': 'downloads', 'url_pattern': 'https://www.computerbase.de/downloads/*'},
        {'site': 'uptodown.com', 'inurl': 'windows', 'url_pattern': 'https://.*\\.uptodown\\.com/windows'},
    ]

    program_instance, _ = Program.objects.get_or_create(program_name=program_name, program_id=program_id)

    for site_info in sites:
        site = site_info.get('site')
        inurl = site_info.get('inurl')
        pattern = site_info.get('url_pattern')

        search_term_instance, _ = SearchTerm.objects.get_or_create(term=f"{program_name} site:{site} inurl:{inurl}")
        if search_term_instance.attempts > MAX_ATTEMPTS:
            execution_time = time.time() - start_time
            print(f"Extract icon execution time for {program_name}: {execution_time} seconds.")
            return JsonResponse({'error': f"Maximum number of google search attempts reached for {program_name}"},
                                status=status.HTTP_200_OK)

        search_term_instance.attempts += 1
        search_term_instance.save()

        search_term = f"{program_name} site:{site} inurl:{inurl}"
        google_response = fetch_google_search(search_term, 3)

        if not google_response or isinstance(google_response, list) and google_response[0].get("error"):
            logger.error(f"No links found in the Google API response for {search_term}")
            continue

        for item in google_response:
            print("this is the item link", item['link'])
            SearchResults.objects.create(
                search_term=search_term_instance,
                program_id=program_instance,
                position=item['position'],
                url=item['link']
            )

            if re.match(pattern, item['link']):
                extraction_response = extract_icon(item['link'], search_term_instance, program_name)
                if extraction_response.status_code in [status.HTTP_200_OK]:
                    return extraction_response  # Successfully found and extracted, or not found but processed
                else:
                    logger.error("Error during extraction, attempting next site if available.")

    execution_time = time.time() - start_time
    print(f"Extract icon execution time for {program_name}: {execution_time} seconds.")
    return JsonResponse({'error': f"No links found across all sites for {program_name}"}, status=status.HTTP_200_OK)


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
        provided_hash = request.headers.get("x-Hash")
        api_key = request.headers.get("api-key")

        # Validate api key
        if not api_key:
            return JsonResponse({"error": "API key is missing."}, status=status.HTTP_401_UNAUTHORIZED)

        if api_key != config('API_KEY') or len(api_key) != 41:
            return JsonResponse({"error": "Invalid API key."}, status=status.HTTP_401_UNAUTHORIZED)

        # Validate program name and program ID lengths
        if not program_name or not program_id or not provided_hash:
            return JsonResponse({"error": "Invalid input variables. Variables must not be null"},
                                status=status.HTTP_400_BAD_REQUEST)
        if not 0 < len(program_name.strip()) < 80:
            return JsonResponse(
                {"error": "Invalid input variables. 'program_name' length should be between 0 and 80"},
                status=status.HTTP_400_BAD_REQUEST)

        program_id_str = str(program_id)
        try:
            float(program_id_str)
            is_numeric = True
        except ValueError:
            is_numeric = False

        if not is_numeric:
            return JsonResponse({"error": "Invalid input variables. 'program_id' must be numeric."},
                                status=status.HTTP_400_BAD_REQUEST)

        salt = config('SECRET_KEY')

        hash_string = f"{program_name.strip()}{program_id}{salt.strip()}"
        expected_hash = hashlib.sha256(hash_string.encode()).hexdigest()
        print(expected_hash)

        if not provided_hash or provided_hash.strip() != expected_hash or len(provided_hash.strip()) != 64:
            return JsonResponse({"error": "Hash validation failed."}, status=status.HTTP_400_BAD_REQUEST)
        # Calculate the date one month ago
        one_month_ago = timezone.now() - timedelta(days=30)

        try:
            queryset = self.queryset.filter(
                program_id__program_id=program_id,
                program_id__program_name=program_name.strip(),
                last_updated__gte=one_month_ago
            ).first()
            if queryset and queryset.url:
                search_term_instance = queryset.search_term
                if queryset:
                    return extract_icon(queryset.url, search_term_instance, program_name)

            return search_icon(program_name, program_id)

        except Exception as e:
            print(e)
            return JsonResponse({'error': 'An unexpected error occurred.'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
