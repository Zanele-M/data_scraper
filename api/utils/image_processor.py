import logging
import base64
import tempfile

from rest_framework import status

from api.utils.html_content_parser import download_image
from PIL import Image
from decouple import config
from django.http import JsonResponse
from api.utils.rembg import rembg

# Configure logging
logging.basicConfig(filename=config('log_path'), encoding='utf-8', level=logging.WARNING)

def process_icon_image(image_url):
    """
    Process and convert the given image URL to a base64 encoded data URI, with error handling.
    """
    try:
        image_data = download_image(image_url)

        if image_data:
            # Save the downloaded image to a temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file_path = temp_file.name
            with open(temp_file_path, 'wb') as file:
                file.write(image_data)

            icon = Image.open(temp_file_path)
            icon_format = icon.format

            if icon_format not in ["PNG", "GIF", "JPG", "JPEG", "WEBP"]:
                return JsonResponse({'error': f"The file format '{icon_format}' is not supported."}, status=200)

            if hasattr(icon, 'info') and 'transparency' in icon.info:
                base64_encoded_data = base64.b64encode(image_data)
            else:
                if not icon.mode == "RGBA":
                    icon = icon.convert('RGBA')

                pixels = icon.getpixel((1, 1))

                if pixels[0] >= 251 and pixels[1] >= 251 and pixels[2] >= 251:
                    processed_image = rembg(temp_file_path)
                    if processed_image:
                        base64_encoded_data = base64.b64encode(processed_image)
                    else:
                        base64_encoded_data = base64.b64encode(image_data)
                else:
                    base64_encoded_data = base64.b64encode(image_data)


            base64_string = base64_encoded_data.decode('utf-8')
            image_data_uri = f'data:image/{icon_format};base64,{base64_string}'
            icon.close()
            return JsonResponse({'image_data': image_data_uri}, status=status.HTTP_200_OK)
        else:
            return JsonResponse({'error': 'Failed to download image or no image data received.'}, status=status.HTTP_200_OK)

    except Exception as e:
        logging.exception(f"Error processing image from {image_url}: {e}")
        return JsonResponse({'error': 'An error occurred while processing the image.'}, status=status.HTTP_200_OK)

