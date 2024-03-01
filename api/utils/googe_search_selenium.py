import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import quote

IMG_XPATH = '/html/body/div[2]/c-wiz/div[3]/div[2]/div[3]/div[2]/div[2]/div[2]/div[2]/c-wiz/div/div/div/div/div[3]/div[1]/a/img[1]'
DIV_IMG_SPAN = "/html/body/div[2]/c-wiz/div[3]/div[1]/div/div/div/div/div[1]/div[1]/span/div[1]/div[1]/div[1]/a[1]/div[1]/img"


def fetch_icons(query: str):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    wd = webdriver.Chrome(options=options)

    encoded_query = quote(query)
    search_url = f"https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={encoded_query}&oq={encoded_query}&gs_l=img"
    thumbnail_results = []
    counter = 0

    while len(thumbnail_results) == 0 and counter < 10:
        wd.delete_all_cookies()  # magic
        wd.get(search_url)
        print(counter)

        if "Before you continue to Google" in wd.page_source:
            accept_cookies = wd.find_element(
                By.XPATH, "/html/body/c-wiz/div/div/div/div[2]/div[1]/div[3]/div[1]/div[1]/form[2]/div/div/button")
            if accept_cookies:
                accept_cookies.click()

        if "Make sure all words are spelled correctly" in wd.page_source:
            return f"No image found for {query}"

        try:
            thumbnail_results = wd.find_elements(By.XPATH, DIV_IMG_SPAN)
            counter = counter + 1
        except Exception as e:
            return f"Thumbnail results failed with error {e} for query: {query}"

    if len(thumbnail_results) > 0:
        try:
            thumbnail_results[0].click()
            time.sleep(3)
        except Exception as e:
            return f"Click failed for image {thumbnail_results[0]} with error {e}"

        # todo add try/catch
        try:
            actual_image = wd.find_element(By.XPATH, IMG_XPATH)
        except Exception as e:
            return f"Failed to find the image element for query: {query} and XPATH {IMG_XPATH} with error: {str(e)}"
        if actual_image.get_attribute('src') and (
                'http' in actual_image.get_attribute('src') or 'base64' in actual_image.get_attribute('src')):
            image_result = actual_image.get_attribute('src')
            return image_result
        else:
            return f"Image not found for {query}"
    else:
        return f"No images found for {query}"
