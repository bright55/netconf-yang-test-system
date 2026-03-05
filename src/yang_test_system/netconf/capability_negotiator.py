"""Capability Negotiator - NETCONF/RESTCONF capability verification

Based on RFC 6241 - Network Configuration Protocol
RFC 8040 - RESTCONF Protocol
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .client import NETCONFClient
from ..core.types import TestResult


class CapabilityType(Enum):
    """Capability type enumeration"""
    NETCONF_BASE = "netconf_base"
    NETCONF_CANDIDATE = "netconf_candidate"
    NETCONF_WRITABLE_RUNNING = "netconf_writable_running"
    NETCONF_CONFIRMED_COMMIT = "netconf_confirmed_commit"
    NETCONF_VALIDATE = "netconf_validate"
    NETCONF_XPATH = "netconf_xpath"
    NETCONF_WITH_DEFAULTS = "netconf_with_defaults"
    NETCONF_ROLLBACK_ERROR = "netconf_rollback_error"
    NETCONF_NOTIFICATION = "netconf_notification"
    NETCONF_INTERLEAVE = "netconf_interleave"
    RESTCONF = "restconf"
    YANG_PUSH = "yang_push"


# NETCONF capability URIs (RFC 6241)
NETCONF_CAPABILITY_URIS = {
    "base:1.0": "urn:ietf:params:netconf:base:1.0",
    "base:1.1": "urn:ietf:params:netconf:base:1.1",
    "writable-running": "urn:ietf:params:netconf:capability:writable-running:1.0",
    "candidate": "urn:ietf:params:netconf:capability:candidate:1.0",
    "confirmed-commit": "urn:ietf:params:netconf:capability:confirmed-commit:1.0",
    "validate": "urn:ietf:params:netconf:capability:validate:1.0",
    "xpath": "urn:ietf:params:netconf:capability:xpath:1.0",
    "with-defaults": "urn:ietf:params:netconf:capability:with-defaults:1.0",
    "rollback-on-error": "urn:ietf:params:netconf:capability:rollback-on-error:1.0",
    "notification": "urn:ietf:params:netconf:capability:notification:1.0",
    "interleave": "urn:ietf:params:netconf:capability:interleave:1.0",
}

# RESTCONF capability URIs (RFC 8040)
RESTCONF_CAPABILITY_URIS = {
    "resource": "urn:ietf:params:restconf:capability:operations:1.0",
    "datastore": "urn:ietf:params:restconf:capability:yang-library:1.0",
    "yang-push": "urn:ietf:params:restconf:capability:yang-push:1.0",
    "yang-push:1.1": "urn:ietf:params:restconf:capability:yang-push:1.1",
}


@dataclass
class CapabilityInfo:
    """Capability information"""
    uri: str
    name: str
    description: str
    supported: bool
    version: str = ""


class CapabilityNegotiator:
    """NETCONF/RESTCONF capability negotiation and verification"""
    
    def __init__(self, client: Optional[NETCONFClient] = None):
        """
        Initialize capability negotiator
        
        Args:
            client: NETCONF client instance
        """
        self.client = client
        self.device_capabilities: Dict[str, Any] = {}
    
    def get_device_capabilities(self, host: str, port: int = 830,
                                username: Optional[str] = None,
                                password: Optional[str] = None) -> Dict[str, Any]:
        """
        Get device capabilities
        
        Args:
            host: Device hostname or IP
            port: NETCONF port
            username: SSH username
            password: SSH password
            
        Returns:
            Dictionary containing device capabilities
        """
        # Create client if not provided
        if not self.client:
            self.client = NETCONFClient(
                host=host,
                port=port,
                username=username,
                password=password
            )
            self.client.connect()
        
        # Get capabilities
        capabilities = self.client.get_capabilities()
        
        self.device_capabilities = {
            'netconf': capabilities.get('server_capabilities', []),
            'restconf': [],
            'session_id': capabilities.get('session_id'),
            'parsed': capabilities.get('parsed', {}),
        }
        
        return self.device_capabilities
    
    def parse_capabilities(self, capabilities: List[str]) -> Dict[str, CapabilityInfo]:
        """
        Parse capability list into structured information
        
        Args:
            capabilities: List of capability URIs
            
        Returns:
            Dictionary of parsed capabilities
        """
        parsed = {}
        
        for cap in capabilities:
            # Try to match known capabilities
            cap_info = self._parse_capability(cap)
            if cap_info:
                parsed[cap_info.name] = cap_info
        
        return parsed
    
    def _parse_capability(self, capability: str) -> Optional[CapabilityInfo]:
        """Parse a single capability"""
        # Check NETCONF capabilities
        for name, uri in NETCONF_CAPABILITY_URIS.items():
            if uri in capability:
                description = self._get_capability_description(name)
                return CapabilityInfo(
                    uri=capability,
                    name=name,
                    description=description,
                    supported=True,
                    version=name.split(':')[-1] if ':' in name else "1.0"
                )
        
        # Check RESTCONF capabilities
        for name, uri in RESTCONF_CAPABILITY_URIS.items():
            if uri in capability:
                description = self._get_restconf_capability_description(name)
                return CapabilityInfo(
                    uri=capability,
                    name=name,
                    description=description,
                    supported=True,
                )
        
        # Unknown capability
        return CapabilityInfo(
            uri=capability,
            name=capability.split(':')[-1] if ':' in capability else capability,
            description="Unknown capability",
            supported=True,
        )
    
    def _get_capability_description(self, name: str) -> str:
        """Get capability description"""
        descriptions = {
            "base:1.0": "Base NETCONF Capability (RFC 6241)",
            "base:1.1": "Base NETCONF 1.1 Capability",
            "writable-running": "Writable Running Configuration",
            "candidate": "Candidate Configuration Capability",
            "confirmed-commit": "Confirmed Commit Capability",
            "validate": "Configuration Validation Capability",
            "xpath": "XPath Filter Capability",
            "with-defaults": "With-Defaults Capability (RFC 6243)",
            "rollback-on-error": "Rollback On Error Capability",
            "notification": "Notification Capability (RFC 5277)",
            "interleave": "Notification Interleave Capability",
        }
        return descriptions.get(name, name)
    
    def _get_restconf_capability_description(self, name: str) -> str:
        """Get RESTCONF capability description"""
        descriptions = {
            "resource": "RESTCONF Resource (RFC 8040)",
            "datastore": "RESTCONF Datastore Access",
            "yang-push": "YANG Push Subscription (RFC 8641)",
            "yang-push:1.1": "YANG Push Subscription 1.1",
        }
        return descriptions.get(name, name)
    
    def verify_capability_consistency(self, expected: List[str],
                                       actual: List[str]) -> TestResult:
        """
        Verify capability consistency
        
        Args:
            expected: Expected capability list
            actual: Actual capability list
            
        Returns:
            TestResult with verification status
        """
        expected_set = set(expected)
        actual_set = set(actual)
        
        missing = expected_set - actual_set
        extra = actual_set - expected_set
        
        return TestResult(
            test_id="capability_consistency",
            test_name="Capability Consistency Check",
            passed=len(missing) == 0,
            actual_result=f"Missing: {list(missing)}, Extra: {list(extra)}",
            expected_result=f"Expected: {expected}",
            error_message=f"Missing capabilities: {list(missing)}" if missing else "",
            rfc_reference="RFC 6241 Section 8.1"
        )
    
    def verify_base_capability(self) -> TestResult:
        """Verify base NETCONF capability"""
        if not self.device_capabilities:
            return TestResult(
                test_id="base_capability",
                test_name="Base NETCONF Capability",
                passed=False,
                error_message="No capabilities retrieved"
            )
        
        netconf_caps = self.device_capabilities.get('netconf', [])
        has_base = any('base:1.' in cap for cap in netconf_caps)
        
        return TestResult(
            test_id="base_capability",
            test_name="Base NETCONF Capability",
            passed=has_base,
            actual_result="Base capability present" if has_base else "Base capability missing",
            expected_result=":base:1.0 or :base:1.1",
            rfc_reference="RFC 6241 Section 8.1"
        )
    
    def verify_candidate_capability(self) -> TestResult:
        """Verify candidate configuration capability"""
        if not self.device_capabilities:
            return TestResult(
                test_id="candidate_capability",
                test_name="Candidate Configuration Capability",
                passed=False,
                error_message="No capabilities retrieved"
            )
        
        netconf_caps = self.device_capabilities.get('netconf', [])
        has_candidate = any('candidate' in cap for cap in netconf_caps)
        
        return TestResult(
            test_id="candidate_capability",
            test_name="Candidate Configuration Capability",
            passed=has_candidate,
            actual_result="Candidate capability present" if has_candidate else "Candidate capability missing",
            expected_result=":candidate capability",
            rfc_reference="RFC 6241 Section 8.3"
        )
    
    def verify_writable_running_capability(self) -> TestResult:
        """Verify writable-running capability"""
        if not self.device_capabilities:
            return TestResult(
                test_id="writable_running_capability",
                test_name="Writable Running Capability",
                passed=False,
                error_message="No capabilities retrieved"
            )
        
        netconf_caps = self.device_capabilities.get('netconf', [])
        has_writable = any('writable-running' in cap for cap in netconf_caps)
        
        return TestResult(
            test_id="writable_running_capability",
            test_name="Writable Running Capability",
            passed=has_writable,
            actual_result="Writable-running present" if has_writable else "Writable-running missing",
            expected_result=":writable-running capability",
            rfc_reference="RFC 6241 Section 8.2"
        )
    
    def verify_validate_capability(self) -> TestResult:
        """Verify configuration validation capability"""
        if not self.device_capabilities:
            return TestResult(
                test_id="validate_capability",
                test_name="Configuration Validation Capability",
                passed=False,
                error_message="No capabilities retrieved"
            )
        
        netconf_caps = self.device_capabilities.get('netconf', [])
        has_validate = any('validate' in cap for cap in netconf_caps)
        
        return TestResult(
            test_id="validate_capability",
            test_name="Configuration Validation Capability",
            passed=has_validate,
            actual_result="Validate capability present" if has_validate else "Validate capability missing",
            expected_result=":validate capability",
            rfc_reference="RFC 6241 Section 8.6"
        )
    
    def verify_xpath_capability(self) -> TestResult:
        """Verify XPath filtering capability"""
        if not self.device_capabilities:
            return TestResult(
                test_id="xpath_capability",
                test_name="XPath Filtering Capability",
                passed=False,
                error_message="No capabilities retrieved"
            )
        
        netconf_caps = self.device_capabilities.get('netconf', [])
        has_xpath = any('xpath' in cap for cap in netconf_caps)
        
        return TestResult(
            test_id="xpath_capability",
            test_name="XPath Filtering Capability",
            passed=has_xpath,
            actual_result="XPath capability present" if has_xpath else "XPath capability missing",
            expected_result=":xpath capability",
            rfc_reference="RFC 6241 Section 8.9"
        )
    
    def verify_notification_capability(self) -> TestResult:
        """Verify notification capability"""
        if not self.device_capabilities:
            return TestResult(
                test_id="notification_capability",
                test_name="Notification Capability",
                passed=False,
                error_message="No capabilities retrieved"
            )
        
        netconf_caps = self.device_capabilities.get('netconf', [])
        has_notification = any('notification' in cap for cap in netconf_caps)
        
        return TestResult(
            test_id="notification_capability",
            test_name="Notification Capability",
            passed=has_notification,
            actual_result="Notification capability present" if has_notification else "Notification capability missing",
            expected_result=":notification capability",
            rfc_reference="RFC 5277"
        )
    
    def get_capability_summary(self) -> Dict[str, Any]:
        """Get capability summary"""
        if not self.device_capabilities:
            return {"error": "No capabilities retrieved"}
        
        netconf_caps = self.device_capabilities.get('netconf', [])
        parsed = self.parse_capabilities(netconf_caps)
        
        return {
            "total_capabilities": len(netconf_caps),
            "capabilities": list(parsed.keys()),
            "netconf_version": "1.1" if any('base:1.1' in c for c in netconf_caps) else "1.0",
            "has_candidate": any('candidate' in c for c in netconf_caps),
            "has_writable_running": any('writable-running' in c for c in netconf_caps),
            "has_validate": any('validate' in c for c in netconf_caps),
            "has_notification": any('notification' in c for c in netconf_caps),
            "session_id": self.device_capabilities.get('session_id'),
        }
