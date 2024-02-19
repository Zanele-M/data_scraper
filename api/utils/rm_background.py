import requests
from PIL import Image
from io import BytesIO


def has_transparent_background(icon):
    if icon.mode == 'RGBA' or icon.mode == 'LA':
        print("Checking transparency in RGBA or LA mode.")
        transparent = any(pixel[3] < 255 for pixel in icon.getdata())
        return transparent
    elif icon.mode == 'P' and 'transparency' in icon.info:
        print("Checking transparency in P mode with transparency info.")
        # In mode 'P', we have to look at the transparency info directly.
        # This is a simplified check; you might need to adjust based on how transparency is defined for your images.
        return True
    else:
        # For other modes, we assume no transparency.
        print(f"No transparency check implemented for mode {icon.mode}.")
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
