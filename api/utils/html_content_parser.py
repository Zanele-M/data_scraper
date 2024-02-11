import logging
from bs4 import BeautifulSoup
from typing import Union, List

from api.client.http_client import HTTPClient

logger = logging.getLogger(__name__)


def extract_html_element_attribute(url: str, search_criteria: dict, attribute: str) -> Union[
    str, List[str], str]:
    """
    Fetches the HTML content from a URL using the HTTPClient and extracts the value(s) of a specified attribute
    from elements matching given search criteria. Returns human-readable error messages upon failure.

    Args:
        url (str): The URL of the webpage to fetch.
        search_criteria (dict): Criteria to find HTML elements.
        attribute (str): The attribute from which to extract the value.

    Returns:
        Union[str, List[str], str]: The value(s) of the specified attribute on success, or a descriptive error message.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    # Create an instance of HTTPClient internally
    client = HTTPClient(url, retry_count=3, backoff_factor=1.0)

    response = client.request("GET", headers=headers)
    # Check if the response is an error message
    if isinstance(response, dict) and "error" in response:
        return "Failed to fetch the site: " + response["error"]

    if response.status_code != 200:
        return f"Failed to access the URL. Status code: {response.status_code}"

    soup = BeautifulSoup(response.content, 'html.parser')
    elements = soup.find_all(**search_criteria) if search_criteria else []

    if not elements:
        return "No matching elements found for the provided search criteria."

    values = [element.get(attribute) for element in elements if element.has_attr(attribute)]

    if not values:
        return f"No elements found with the specified attribute '{attribute}'."

    return values[0] if len(values) == 1 else values


def download_image(url: str):
    """
    Download an image from the URL using the HTTPClient with up to 3 retries and exponential backoff.

    Args:
        url (str): The URL of the image to download.

    Returns:
        A tuple of (content_type, image_data) if successful, or (None, None) on failure.
    """
    # Create an instance of HTTPClient specifically for this download task
    # Adjust the instantiation as needed, especially if your HTTPClient class requires specific arguments
    client = HTTPClient(url, retry_count=3, backoff_factor=1.0)

    # Use the client to make a GET request and specify that we want the raw response
    response = client.request("GET")

    if response and response.status_code == 200:
        content_type = response.headers.get('Content-Type')
        return content_type, response.content
    else:
        logger.error(f"Failed to download image from {url}.")
        return None, None