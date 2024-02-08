from bs4 import BeautifulSoup
import requests
import time
import logging

logger = logging.getLogger(__name__)


def extract_html_element_attribute(url: str, search_criteria: dict, attribute: str) -> str or list or int:
    """
    Fetches the HTML content from a URL and extracts the value(s) of a specified attribute from elements matching
    given search criteria. This version includes a User-Agent header to make requests appear more human-like.

    Args:
        url (str): The URL of the webpage to fetch.
        search_criteria (dict): Criteria to find HTML elements, e.g., {"class_": "example"} for simple or
                                {"name": "meta", "attrs": {"property": "og:image"}} for complex search.
        attribute (str): The attribute from which to extract the value.

    Returns:
        str or list: The value of the specified attribute from the first matching element,
                     a list of values if multiple elements match, or an error code as an integer on failure.
                     Returns -1 if the URL is not accessible after retries, -2 if no matching elements are found.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    attempts = 0
    while attempts < 3:
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                if "name" in search_criteria and "attrs" in search_criteria:
                    elements = soup.find_all(search_criteria["name"], **search_criteria["attrs"])
                else:
                    elements = soup.find_all(**search_criteria)
                if not elements:
                    return -2
                values = []
                for element in elements:
                    if element.has_attr(attribute):
                        value = element[attribute]
                        values.append(value)
                if not values:
                    return -2
                return values[0] if len(values) == 1 else values
            else:
                attempts = 1
                time.sleep(1)
        except Exception as e:
            attempts = 1
            time.sleep(1)
    return -1
