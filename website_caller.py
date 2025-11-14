"""
Website Caller Utility

A simple utility class for making HTTP requests to websites.
"""

import requests
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
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
            raise requests.RequestException(f"Failed to call {url}: {str(e)}")
    
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
    
    def post(self, url: str, data: Optional[Any] = None, json: Optional[Dict[str, Any]] = None,
             headers: Optional[Dict[str, str]] = None) -> requests.Response:
        """
        Make a POST request to a URL.
        
        Args:
            url: The URL to call
            data: Optional form data to send
            json: Optional JSON data to send
            headers: Optional headers to include
        
        Returns:
            requests.Response object
        """
        kwargs = {}
        if data:
            kwargs["data"] = data
        if json:
            kwargs["json"] = json
        if headers:
            kwargs["headers"] = headers
        return self.call(url, method="POST", **kwargs)
    
    def put(self, url: str, data: Optional[Any] = None, json: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None) -> requests.Response:
        """
        Make a PUT request to a URL.
        
        Args:
            url: The URL to call
            data: Optional form data to send
            json: Optional JSON data to send
            headers: Optional headers to include
        
        Returns:
            requests.Response object
        """
        kwargs = {}
        if data:
            kwargs["data"] = data
        if json:
            kwargs["json"] = json
        if headers:
            kwargs["headers"] = headers
        return self.call(url, method="PUT", **kwargs)
    
    def delete(self, url: str, headers: Optional[Dict[str, str]] = None) -> requests.Response:
        """
        Make a DELETE request to a URL.
        
        Args:
            url: The URL to call
            headers: Optional headers to include
        
        Returns:
            requests.Response object
        """
        kwargs = {}
        if headers:
            kwargs["headers"] = headers
        return self.call(url, method="DELETE", **kwargs)
    
    def get_json(self, url: str, params: Optional[Dict[str, Any]] = None,
                 headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Make a GET request and return JSON response.
        
        Args:
            url: The URL to call
            params: Optional query parameters
            headers: Optional headers to include
        
        Returns:
            Parsed JSON response as dictionary
        """
        response = self.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    
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
    
    def _generate_filename(self, url: str, filename: Optional[str] = None, 
                          output_dir: Optional[str] = None) -> str:
        """
        Generate a filename from URL if not provided.
        
        Args:
            url: The URL to generate filename from
            filename: Optional custom filename
            output_dir: Optional output directory
        
        Returns:
            Full path to the output file
        """
        if filename:
            filepath = Path(filename)
        else:
            # Generate filename from URL
            parsed = urlparse(url)
            # Use domain name and path to create filename
            domain = parsed.netloc.replace("www.", "").replace(".", "_")
            path = parsed.path.strip("/").replace("/", "_") or "index"
            # Remove query string and fragment for filename
            filename = f"{domain}_{path}.html"
            filepath = Path(filename)
        
        # Add output directory if specified
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            filepath = output_path / filepath.name
        
        return str(filepath)
    
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
    
    def save_html(self, url: str, filename: Optional[str] = None,
                  output_dir: Optional[str] = None, params: Optional[Dict[str, Any]] = None,
                  headers: Optional[Dict[str, str]] = None, encoding: Optional[str] = None,
                  wait_for_selector: Optional[str] = None) -> str:
        """
        Call a URL, get HTML response, and save it to a file.
        
        Args:
            url: The URL to call
            filename: Optional custom filename (default: generated from URL)
            output_dir: Optional directory to save file in
            params: Optional query parameters
            headers: Optional headers to include
            encoding: Optional encoding for file (default: uses response encoding or utf-8)
            wait_for_selector: Optional CSS selector to wait for (only used with browser automation)
        
        Returns:
            Path to the saved file
        
        Raises:
            ValueError: If URL is invalid
            requests.RequestException: If request fails
            IOError: If file cannot be written
        """
        # Use browser automation if enabled
        response = None
        if self.use_browser:
            html_content = self.get_html_with_browser(url, wait_for_selector=wait_for_selector)
        else:
            # Get the HTML response using requests
            response = self.get(url, params=params, headers=headers)
            response.raise_for_status()
            html_content = response.text
        
        # Generate filename
        filepath = self._generate_filename(url, filename, output_dir)
        
        # Determine encoding
        if encoding is None:
            if self.use_browser:
                encoding = 'utf-8'
            else:
                encoding = response.encoding or 'utf-8' if response else 'utf-8'
        
        # Ensure directory exists
        file_path_obj = Path(filepath)
        file_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Save HTML content to file
        try:
            with open(filepath, 'w', encoding=encoding) as f:
                f.write(html_content)
            return filepath
        except IOError as e:
            raise IOError(f"Failed to save HTML to {filepath}: {str(e)}")
    
    def call_and_save(self, url: str, filename: Optional[str] = None,
                     output_dir: Optional[str] = None, method: str = "GET",
                     **kwargs) -> tuple[requests.Response, str]:
        """
        Call a URL and save the response to an HTML file.
        
        Args:
            url: The URL to call
            filename: Optional custom filename (default: generated from URL)
            output_dir: Optional directory to save file in
            method: HTTP method (default: GET)
            **kwargs: Additional arguments (params, headers, data, json, etc.)
        
        Returns:
            Tuple of (Response object, path to saved file)
        
        Raises:
            ValueError: If URL is invalid or method is not GET/HEAD
            requests.RequestException: If request fails
            IOError: If file cannot be written
        """
        if method.upper() not in ["GET", "HEAD"]:
            raise ValueError("call_and_save only supports GET and HEAD methods")
        
        # Make the request
        response = self.call(url, method=method, **kwargs)
        response.raise_for_status()
        
        # Generate filename
        filepath = self._generate_filename(url, filename, output_dir)
        
        # Determine encoding
        encoding = response.encoding or 'utf-8'
        
        # Ensure directory exists
        file_path_obj = Path(filepath)
        file_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Save HTML content to file
        try:
            with open(filepath, 'w', encoding=encoding) as f:
                f.write(response.text)
            return response, filepath
        except IOError as e:
            raise IOError(f"Failed to save HTML to {filepath}: {str(e)}")
    
    def close(self):
        """Close the session and browser if opened."""
        self.session.close()
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

