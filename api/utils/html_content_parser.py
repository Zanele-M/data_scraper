import logging
from bs4 import BeautifulSoup
from typing import Union, List
from decouple import config

from api.client.http_client import HTTPClient

logger = logging.getLogger(__name__)
logging.basicConfig(filename=config('log_path'), encoding='utf-8', level=logging.WARNING)


def extract_html_element_attribute(url: str, search_criteria: dict, attribute: str) -> Union[
    str, List[str], List[dict]]:
    """
    Fetches the HTML content from a URL using the HTTPClient and extracts the value(s) of a specified attribute
    from elements matching given search criteria. Returns human-readable error messages upon failure.

    Args:
        url (str): The URL of the webpage to fetch.
        search_criteria (dict): Criteria to find HTML elements.
        attribute (str): The attribute from which to extract the value.

    Returns:
        Union[str, List[str], List[dict]]: The value(s) of the specified attribute on success,
        or a list of descriptive error messages.
    """

    # Create an instance of HTTPClient internally
    client = HTTPClient(url, retry_count=3, backoff_factor=1.5)

    response = client.request("GET")
    if isinstance(response, dict) and "error" in response:
        return [{"error": "Error fetching the page"}]  # Adjusted error message for clarity

    soup = BeautifulSoup(response.content, 'html.parser')
    elements = soup.find_all(**search_criteria) if search_criteria else []

    if not elements:
        return [{"error": "No matching elements found for the provided search criteria."}]

    values = [element.get(attribute) for element in elements if element.has_attr(attribute)]

    if not values:
        return [{"error": f"No elements found with the specified attribute '{attribute}'."}]

    # Adjusted to ensure the return type is consistent
    return values if len(values) > 1 else values[0]


def download_image(url: str):
    """
    Download an image from the URL using the HTTPClient with up to 3 retries and exponential backoff.

    Args:
        url (str): The URL of the image to download.

    Returns:
        A tuple of (content_type, image_data) if successful, or (None, None) on failure.
    """

    client = HTTPClient(url, retry_count=3, backoff_factor=0.5)

    try:
        response = client.request("GET")
        if response.status_code == 200:
            return response.content
        else:
            logger.error(f"Failed to download image from {url}.")
            return None
    except AttributeError:
        logger.error(f"Response object does not have the expected attributes.")
        return None
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return None
