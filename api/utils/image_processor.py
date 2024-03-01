import logging
import base64
import tempfile
from io import BytesIO

from rembg import remove
from rest_framework import status

from api.utils.html_content_parser import download_image
from PIL import Image
from decouple import config
from django.http import JsonResponse
from api.utils.rembg import rembg
import re

# Configure logging
logging.basicConfig(filename=config('log_path'), encoding='utf-8', level=logging.WARNING)


def process_icon_image(image_url, rm_bg=True):
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
                return JsonResponse({
                    'error': f"The file format '{icon_format}' is not supported for the url {image_url}."},
                    status=status.HTTP_200_OK)

            if hasattr(icon, 'info') and 'transparency' in icon.info:
                base64_encoded_data = base64.b64encode(image_data)
            else:
                if not icon.mode == "RGBA":
                    icon = icon.convert('RGBA')

                pixels = icon.getpixel((1, 1))
                print(pixels)

                if pixels[0] >= 237 and pixels[1] >= 237 and pixels[2] >= 237 and rm_bg:
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
            return JsonResponse({'error': f'Failed to download icon from {image_url}.'},
                                status=status.HTTP_200_OK)

    except Exception as e:
        logging.exception(f"Error processing image from {image_url}: {e}")
        return JsonResponse(
            {'error': f'An error occurred while processing the icon for {image_url}.'},
            status=status.HTTP_200_OK)


def process_icon_base64(base64_icon, program_name, rm_bg=True):
    try:
        base64_str = re.search(r'base64,(.*)', base64_icon).group(1)
        im = Image.open(BytesIO(base64.b64decode(base64_str)))
        img_format = im.format

        if img_format not in ["PNG", "GIF", "JPG", "JPEG", "WEBP"]:
            return {'error': f"The file format '{img_format}' is not supported for {program_name}."}

        if hasattr(im, 'info') and 'transparency' in im.info:
            image_data_uri = f'data:image/{img_format};base64,{base64_str}'
            return JsonResponse({'image_data': image_data_uri}, status=status.HTTP_200_OK)
        else:
            if not im.mode == "RGBA":
                im = im.convert('RGBA')

                pixels = im.getpixel((1, 1))
                print(pixels)

                if pixels[0] >= 237 and pixels[1] >= 237 and pixels[2] >= 237 and rm_bg:
                    rm_img = remove(base64.b64decode(base64_str))
                    base64_encoded_data = base64.b64encode(rm_img)
                    base64_string = base64_encoded_data.decode('utf-8')
                    image_data_uri = f'data:image/{img_format};base64,{base64_string}'
                    return JsonResponse({'image_data': image_data_uri}, status=status.HTTP_200_OK)
                else:
                    image_data_uri = f'data:image/{img_format};base64,{base64_str}'
                    return JsonResponse({'image_data': image_data_uri}, status=status.HTTP_200_OK)

    except Exception as e:
        JsonResponse(
            {'error': f'An error occurred while processing the icon for {program_name}.'},
            status=status.HTTP_200_OK)
