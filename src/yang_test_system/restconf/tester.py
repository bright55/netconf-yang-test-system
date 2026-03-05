"""RESTCONF Tester - RESTCONF protocol testing (RFC 8040)

Based on RFC 8040 - RESTCONF Protocol
"""

import requests
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import json

from ..core.types import TestType


RESTCONF_CAPABILITIES = {
    "urn:ietf:params:restconf:capability:defaults": "Defaults",
    "urn:ietf:params:restconf:capability:yang-push": "YANG Push",
    "urn:ietf:params:restconf:capability:yang-push:1.0": "YANG Push 1.0",
    "urn:ietf:params:restconf:capability:yang-push:1.1": "YANG Push 1.1",
}


@dataclass
class RESTCONFResponse:
    """RESTCONF response wrapper"""
    status_code: int
    data: Any
    headers: Dict[str, str]
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300


class RESTCONFTester:
    """RESTCONF protocol tester (RFC 8040)"""

    def __init__(self, base_url: str, username: str, password: str,
                 timeout: int = 30):
        """
        Initialize RESTCONF tester

        Args:
            base_url: RESTCONF base URL (e.g., https://device:443)
            username: Authentication username
            password: Authentication password
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.auth = (username, password)
        self.timeout = timeout
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({
            'Accept': 'application/yang-data+json',
            'Content-Type': 'application/yang-data+json',
        })

        # Disable SSL warnings for testing
        requests.packages.urllib3.disable_warnings()

    def _build_url(self, path: str) -> str:
        """Build RESTCONF URL from path"""
        path = path.lstrip('/')
        return f"{self.base_url}/restconf/data/{path}"

    def _build_url_operations(self, path: str) -> str:
        """Build RESTCONF operations URL"""
        path = path.lstrip('/')
        return f"{self.base_url}/restconf/operations/{path}"

    def _request(self, method: str, url: str, **kwargs) -> RESTCONFResponse:
        """Execute RESTCONF request"""
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                verify=False,  # Skip SSL verification for testing
                **kwargs
            )

            # Parse response data
            try:
                data = response.json() if response.content else None
            except json.JSONDecodeError:
                data = response.text

            return RESTCONFResponse(
                status_code=response.status_code,
                data=data,
                headers=dict(response.headers),
            )

        except requests.exceptions.RequestException as e:
            return RESTCONFResponse(
                status_code=0,
                data=None,
                headers={},
                error=str(e)
            )

    # Data Resource Operations (RFC 8040 Section 3)

    def get(self, path: str, headers: Optional[Dict[str, str]] = None) -> RESTCONFResponse:
        """
        GET data resource (RFC 8040 Section 3.3)

        Args:
            path: Resource path
            headers: Additional headers

        Returns:
            RESTCONFResponse
        """
        url = self._build_url(path)
        return self._request('GET', url, headers=headers)

    def create(self, path: str, data: Dict[str, Any],
               headers: Optional[Dict[str, str]] = None) -> RESTCONFResponse:
        """
        POST to create data resource (RFC 8040 Section 3.4)

        Args:
            path: Resource path
            data: Data to create
            headers: Additional headers

        Returns:
            RESTCONFResponse
        """
        url = self._build_url(path)
        return self._request('POST', url, json=data, headers=headers)

    def replace(self, path: str, data: Dict[str, Any],
                headers: Optional[Dict[str, str]] = None) -> RESTCONFResponse:
        """
        PUT to replace data resource (RFC 8040 Section 3.5)

        Args:
            path: Resource path
            data: Replacement data
            headers: Additional headers

        Returns:
            RESTCONFResponse
        """
        url = self._build_url(path)
        return self._request('PUT', url, json=data, headers=headers)

    def patch(self, path: str, data: Dict[str, Any],
              headers: Optional[Dict[str, str]] = None) -> RESTCONFResponse:
        """
        PATCH to modify data resource (RFC 8040 Section 4.5)

        Args:
            path: Resource path
            data: Patch data
            headers: Additional headers

        Returns:
            RESTCONFResponse
        """
        url = self._build_url(path)
        return self._request('PATCH', url, json=data, headers=headers)

    def delete(self, path: str,
               headers: Optional[Dict[str, str]] = None) -> RESTCONFResponse:
        """
        DELETE data resource (RFC 8040 Section 3.6)

        Args:
            path: Resource path
            headers: Additional headers

        Returns:
            RESTCONFResponse
        """
        url = self._build_url(path)
        return self._request('DELETE', url, headers=headers)

    # Operations (RFC 8040 Section 4)

    def rpc(self, operation: str, input_data: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None) -> RESTCONFResponse:
        """
        Invoke RPC operation (RFC 8040 Section 4.1)

        Args:
            operation: Operation name
            input_data: Input parameters
            headers: Additional headers

        Returns:
            RESTCONFResponse
        """
        url = self._build_url_operations(operation)

        if input_data:
            return self._request('POST', url, json=input_data, headers=headers)
        else:
            return self._request('POST', url, headers=headers)

    # Capability Discovery (RFC 8040 Section 5)

    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get RESTCONF capabilities (RFC 8040 Section 5.3)

        Returns:
            Dictionary of capabilities
        """
        # Try to get capabilities from /restconf
        response = self._request('GET', f"{self.base_url}/restconf")

        capabilities = {
            "restconf_version": None,
            "operations": [],
            "datastores": [],
            "capabilities": [],
        }

        if response.ok and response.data:
            if isinstance(response.data, dict):
                # Extract capabilities info
                restconf = response.data.get('ietf-restconf:restconf', {})
                capabilities['restconf_version'] = restconf.get('restconf-version')
                capabilities['operations'] = restconf.get('operations', {})
                capabilities['datastores'] = restconf.get('datastores', {})

        return capabilities

    def get_api_info(self) -> Dict[str, Any]:
        """
        Get RESTCONF API information (RFC 8040 Section 5.3.2)

        Returns:
            API info dictionary
        """
        response = self._request('GET', f"{self.base_url}/restconf")

        if response.ok and response.data:
            return response.data

        return {"error": response.error or "Failed to get API info"}

    def get_datastores(self) -> RESTCONFResponse:
        """
        Get list of datastores (RFC 8040 Section 5.3.3)

        Returns:
            RESTCONFResponse
        """
        url = f"{self.base_url}/restconf/data/ietf-datastores:datastores"
        return self._request('GET', url)

    def get_modules(self) -> RESTCONFResponse:
        """
        Get YANG library information (RFC 8040 Section 5.3.4)

        Returns:
            RESTCONFResponse
        """
        url = f"{self.base_url}/restconf/data/ietf-yang-library:modules-state"
        return self._request('GET', url)

    # Schema Retrieval (RFC 8040 Section 5.3.5)

    def get_schema(self, module: str, revision: Optional[str] = None,
                   format: str = "yang") -> RESTCONFResponse:
        """
        Get YANG schema (RFC 8040 Section 5.3.5)

        Args:
            module: Module name
            revision: Module revision (optional)
            format: Schema format (yang, yin, xsd)

        Returns:
            RESTCONFResponse
        """
        url = f"{self.base_url}/restconf/yang-library-version"
        version_response = self._request('GET', url)

        yang_library_version = "2019-01-04"  # Default
        if version_response.ok and version_response.data:
            yang_library_version = version_response.data.get(
                'ietf-yang-library:yang-library-version',
                yang_library_version
            )

        path = f"ietf-yang-library:{module}"
        if revision:
            path += f"?revision={revision}"

        url = self._build_url(path)
        headers = {'Accept': f'application/yang.{format}'}
        return self._request('GET', url, headers=headers)

    # Error handling

    def parse_error(self, response: RESTCONFResponse) -> Dict[str, Any]:
        """
        Parse RESTCONF error response

        Args:
            response: RESTCONFResponse

        Returns:
            Parsed error information
        """
        if response.ok:
            return {}

        error_info = {
            "status": response.status_code,
            "message": response.error or "Unknown error",
        }

        if response.data and isinstance(response.data, dict):
            # Look for RESTCONF error
            errors = response.data.get('errors', {})
            error_list = errors.get('error', [])

            if error_list:
                error = error_list[0]
                error_info.update({
                    "error_type": error.get('error-type'),
                    "error_tag": error.get('error-tag'),
                    "error_app_tag": error.get('error-app-tag'),
                    "error_path": error.get('error-path'),
                    "error_message": error.get('error-message'),
                })

        return error_info

    def close(self):
        """Close session"""
        self.session.close()


def create_tester(base_url: str, username: str, password: str,
                  timeout: int = 30) -> RESTCONFTester:
    """Factory function to create RESTCONF tester"""
    return RESTCONFTester(
        base_url=base_url,
        username=username,
        password=password,
        timeout=timeout
    )
