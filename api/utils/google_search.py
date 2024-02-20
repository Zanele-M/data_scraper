import json
from typing import Any
import logging
from decouple import config

from api.client.http_client import HTTPClient

logger = logging.getLogger(__name__)


def fetch_google_search(query: str, page_size: int = 3, output_file: str = None) -> list[dict[str, Any]]:
    """
    Fetches links from Google search results for a given query using the SpaceSERP API.

    This function sends a request to the SpaceSERP API with a specific query and optional page size,
    then processes the JSON response to extract the first search result link. If specified, the result
    is also saved to a JSON file for persistence.
    Args:
        query (str): The search query.
        page_size (int, optional): The number of search results to return. Defaults to 1.
        output_file (str, optional): Path to the file where the search result will be saved.
                                     If None, the result is not written to a file. Defaults to None.

    Returns:
        list[dict[str, Any]]: A list of dictionaries containing the links and their positions.
    """
    url = "https://api.spaceserp.com/google/search"
    api_key = config('SPACESERP_API_KEY')
    encoded_query = query
    params = {
        "apiKey": api_key,
        "q": encoded_query,
        "location": "Berlin,Berlin,Germany",
        "domain": "google.de",
        "gl": "de",
        "hl": "de",
        "pageSize": page_size
    }

    client = HTTPClient(url, retry_count=3, backoff_factor=1.0)

    response = client.request("GET", params=params)

    result = response.json()

    print('result', result)
    if 'organic_results' in result and result['organic_results']:
        links = []
        for item in result['organic_results']:
            link = item['link']
            position = item['position']
            links.append({'link': link, 'position': position})
        if output_file:
            try:
                with open(output_file, 'w') as file:
                    json.dump({'links': links}, file)
            except IOError as e:
                logger.error(f"Error writing to file: {e}")
                return [{"error": "Error writing to file"}]
        return links
    else:
        logger.error("No link found in the API response.")
        return [{"error": "No links found in the Google API response"}]
