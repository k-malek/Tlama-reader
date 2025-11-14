"""
Website Caller Utility

A simple utility class for making HTTP requests to websites.
"""

import requests
from typing import Optional, Dict, Any
from urllib.parse import urlparse

try:
    from playwright.sync_api import sync_playwright, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class WebsiteCaller:
    """Utility class for calling websites by URL."""

    def __init__(self, timeout: int = 10, headers: Optional[Dict[str, str]] = None,
                 use_browser: bool = False):
        """
        Initialize the WebsiteCaller.

        Args:
            timeout: Request timeout in seconds (default: 10)
            headers: Optional default headers to include in all requests
            use_browser: If True, use browser automation for JavaScript execution (default: False)
        """
        self.timeout = timeout
        self.default_headers = headers or {}
        self.use_browser = use_browser
        self.session = requests.Session()
        if self.default_headers:
            self.session.headers.update(self.default_headers)

        # Browser automation setup
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        if self.use_browser:
            if not PLAYWRIGHT_AVAILABLE:
                raise ImportError(
                    "Playwright is required for browser automation. "
                    "Install it with: pip install playwright && playwright install"
                )
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=True)
            self._context = self._browser.new_context()

    def _validate_url(self, url: str) -> bool:
        """Validate that the URL is properly formatted."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def call(self, url: str, method: str = "GET", **kwargs) -> requests.Response:
        """
        Call a website by URL.

        Args:
            url: The URL to call
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            **kwargs: Additional arguments to pass to requests (headers, data, json, params, etc.)

        Returns:
            requests.Response object

        Raises:
            ValueError: If URL is invalid
            requests.RequestException: If request fails
        """
        if not self._validate_url(url):
            raise ValueError(f"Invalid URL: {url}")

        method = method.upper()
        if method not in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]:
            raise ValueError(f"Unsupported HTTP method: {method}")

        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            return response
        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to call {url}: {str(e)}") from e

    def get(self, url: str, params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None) -> requests.Response:
        """
        Make a GET request to a URL.

        Args:
            url: The URL to call
            params: Optional query parameters
            headers: Optional headers to include

        Returns:
            requests.Response object
        """
        kwargs = {}
        if params:
            kwargs["params"] = params
        if headers:
            kwargs["headers"] = headers
        return self.call(url, method="GET", **kwargs)

    def get_text(self, url: str, params: Optional[Dict[str, Any]] = None,
                 headers: Optional[Dict[str, str]] = None) -> str:
        """
        Make a GET request and return text response.

        Args:
            url: The URL to call
            params: Optional query parameters
            headers: Optional headers to include

        Returns:
            Response text
        """
        response = self.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.text

    def get_html_with_browser(self, url: str, wait_for_selector: Optional[str] = None,
                             wait_timeout: Optional[int] = None,
                             wait_until: str = "networkidle") -> str:
        """
        Get HTML content after JavaScript execution using browser automation.

        Args:
            url: The URL to load
            wait_for_selector: Optional CSS selector to wait for before getting HTML
            wait_timeout: Optional timeout in milliseconds for waiting (default: uses self.timeout * 1000)
            wait_until: When to consider navigation succeeded: "load", "domcontentloaded", "networkidle" (default: "networkidle")

        Returns:
            HTML content as string

        Raises:
            ValueError: If URL is invalid or browser automation is not enabled
            RuntimeError: If browser automation fails
        """
        if not self.use_browser:
            raise ValueError("Browser automation is not enabled. Set use_browser=True in __init__")

        if not self._context:
            raise RuntimeError("Browser context is not initialized")

        if wait_timeout is None:
            wait_timeout = self.timeout * 1000

        page = self._context.new_page()
        try:
            # Navigate to URL
            page.goto(url, wait_until=wait_until, timeout=wait_timeout)

            # Wait for specific selector if provided
            if wait_for_selector:
                page.wait_for_selector(wait_for_selector, timeout=wait_timeout)

            # Get HTML content
            html = page.content()
            return html
        finally:
            page.close()

    def close(self):
        """Close the session and browser if opened."""
        self.session.close()
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
