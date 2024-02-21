import requests
import time
import logging
from typing import Any, Optional, Dict, Union

logger = logging.getLogger(__name__)


class HTTPClient:
    def __init__(self, url: str, api_key: Optional[str] = None, retry_count: int = 2, backoff_factor: float = 1.0):
        """
        Initializes the HTTP client with a base URL, optional API key for authentication, retry count, and backoff factor for retries.

        Args:
            url (str): The base URL for the API.
            api_key (Optional[str]): The API key for authentication.
            retry_count (int): The number of times to retry the request upon failure.
            backoff_factor (float): The factor by which to increase the delay between retries.
        """
        self.url = url
        self.api_key = api_key
        self.retry_count = retry_count
        self.backoff_factor = backoff_factor

    def request(self, method: str, params: Optional[Dict[str, Any]] = None,
                data: Optional[Union[Dict[str, Any], str]] = None, headers: Optional[Dict[str, Any]] = None) -> Any:
        """
        Makes an HTTP request and optionally returns the raw response object.

        Args:
            method (str): The HTTP method to use.
            params (Optional[Dict[str, Any]]): Query parameters for the request.
            data (Optional[Union[Dict[str, Any], str]]): Data to send in the request body.
            headers (Optional[Dict[str, Any]]): HTTP headers to send with the request.

        Returns:
            Any: The response data or the raw Response object if return_raw is True.
        """
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }

        # If headers were provided, merge them with the defaults
        if headers:
            headers = {**default_headers, **headers}
        else:  # Otherwise use the default headers
            headers = default_headers

        attempts = 0
        while attempts < self.retry_count:
            try:
                response = requests.request(method, self.url, params=params, data=data, headers=headers)
                if response.status_code == 200:
                    return response
                else:
                    logger.error(f"Expected status code 200 but got {response.status_code} for {self.url}")
            except Exception as e:
                logger.error(f"Error occurred while fetching or processing {self.url}", exc_info=e)
            time.sleep(self.backoff_factor * 60)
            attempts += 1

        return {"error": "Failed to fetch the response after retries"}
