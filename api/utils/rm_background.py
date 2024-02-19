import requests
from PIL import Image
from io import BytesIO


def has_transparent_background(icon):
    if icon.mode in ('RGBA', 'LA') or (icon.mode == 'P' and 'transparency' in icon.info):
        transparent = any(pixel[3] < 255 for row in icon.getdata() for pixel in row)
        return transparent
    return False


def remove_bg(temp_file_path, api_key="Ddr1NQFQbC2hRDazKQDsnT6e"):
    try:
        with open(temp_file_path, 'rb') as image_file:
            response = requests.post(
                'https://api.remove.bg/v1.0/removebg',
                files={'image_file': image_file},
                data={'size': 'auto'},
                headers={'X-Api-Key': api_key},
            )
        if response.status_code == requests.codes.ok:
            return Image.open(BytesIO(response.content))
        else:
            print("Error:", response.status_code, response.text)
            return None
    except Exception as e:
        print("Error:", str(e))
        return None
