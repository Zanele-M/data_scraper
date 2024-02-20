from rembg import remove


def rembg(temp_file_path):
    try:
        with open(temp_file_path, 'rb') as i:
            output = remove(i.read())
            return output
    except Exception as e:
        print("Error:", str(e))
        return None


def has_transparent_background(icon, program_name):
    if icon.mode == 'RGBA' or icon.mode == 'LA':
        print(f"Checking transparency in RGBA or LA mode for {program_name}.")
        transparent = any(pixel[3] < 255 for pixel in icon.getdata())
        return transparent
    elif icon.mode == 'P' and 'transparency' in icon.info:
        print(f"Checking transparency in P mode with transparency info for {program_name}.")
        # In mode 'P', we have to look at the transparency info directly.
        # This is a simplified check; you might need to adjust based on how transparency is defined for your images.
        return True
    else:
        # For other modes, we assume no transparency.
        print(f"No transparency check implemented for mode {icon.mode} for {program_name}.")
        return False
