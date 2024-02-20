from rembg import remove


def rembg(temp_file_path):
    try:
        with open(temp_file_path, 'rb') as i:
            output = remove(i.read())
            return output
    except Exception as e:
        print("Error:", str(e))
        return None
