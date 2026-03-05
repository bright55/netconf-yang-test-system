"""YANG Data Types and Constants based on RFC 7950"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class TestType(Enum):
    """Test type enumeration"""
    # YANG Static Tests
    SYNTAX_VALIDATION = "syntax_validation"
    MODULE_IMPORT = "module_import"
    FEATURE_CONDITION = "feature_condition"
    VERSION_COMPATIBILITY = "version_compatibility"
    MANDATORY_FIELD = "mandatory_field"
    DEFAULT_VALUE = "default_value"
    TYPE_VALIDATION = "type_validation"
    RANGE_CONSTRAINT = "range_constraint"
    PATTERN_CONSTRAINT = "pattern_constraint"
    ENUM_VALIDATION = "enum_validation"
    MUST_EXPRESSION = "must_expression"
    WHEN_CONDITION = "when_condition"
    CHOICE_CASE = "choice_case"
    
    # NETCONF Operations Tests
    GET_CONFIG = "get_config"
    EDIT_CONFIG = "edit_config"
    COPY_CONFIG = "copy_config"
    DELETE_CONFIG = "delete_config"
    LOCK_UNLOCK = "lock_unlock"
    COMMIT_DISCARD = "commit_discard"
    VALIDATE = "validate"
    RPC_VALIDATION = "rpc_validation"
    NOTIFICATION_VALIDATION = "notification_validation"
    
    # RESTCONF Tests
    RESTCONF_GET = "restconf_get"
    RESTCONF_POST = "restconf_post"
    RESTCONF_PUT = "restconf_put"
    RESTCONF_PATCH = "restconf_patch"
    RESTCONF_DELETE = "restconf_delete"
    
    # YANG Push Tests
    YANG_PUSH_SUBSCRIPTION = "yang_push_subscription"
    
    # Capability Tests
    CAPABILITY_NEGOTIATION = "capability_negotiation"
    
    # NACM Tests
    NACM_AUTHORIZATION = "nacm_authorization"


class Severity(Enum):
    """Test severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TestPoint:
    """Test point data structure"""
    test_id: str
    test_name: str
    test_type: TestType
    yang_path: str
    test_description: str
    test_steps: List[str]
    expected_result: str
    severity: Severity = Severity.MEDIUM
    auto_executable: bool = True
    rfc_reference: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "test_type": self.test_type.value,
            "yang_path": self.yang_path,
            "test_description": self.test_description,
            "test_steps": self.test_steps,
            "expected_result": self.expected_result,
            "severity": self.severity.value,
            "auto_executable": self.auto_executable,
            "rfc_reference": self.rfc_reference,
            "metadata": self.metadata,
        }


@dataclass
class TestResult:
    """Test result data structure"""
    test_id: str
    test_name: str
    passed: bool
    actual_result: str = ""
    expected_result: str = ""
    error_message: str = ""
    execution_time: float = 0.0
    rfc_reference: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "passed": self.passed,
            "actual_result": self.actual_result,
            "expected_result": self.expected_result,
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "rfc_reference": self.rfc_reference,
        }


@dataclass
class YANGValidationResult:
    """YANG validation result"""
    is_valid: bool
    errors: List[Dict[str, str]] = field(default_factory=list)
    warnings: List[Dict[str, str]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
        }


# NETCONF Capability Constants (RFC 6241)
NETCONF_CAPABILITIES = {
    "urn:ietf:params:netconf:base:1.0": "Base NETCONF Capability",
    "urn:ietf:params:netconf:base:1.1": "Base NETCONF 1.1",
    "urn:ietf:params:netconf:capability:writable-running:1.0": "Writable Running",
    "urn:ietf:params:netconf:capability:candidate:1.0": "Candidate Configuration",
    "urn:ietf:params:netconf:capability:confirmed-commit:1.0": "Confirmed Commit",
    "urn:ietf:params:netconf:capability:validate:1.0": "Validate",
    "urn:ietf:params:netconf:capability:xpath:1.0": "XPath",
    "urn:ietf:params:netconf:capability:with-defaults:1.0": "With Defaults",
    "urn:ietf:params:netconf:capability:rollback-on-error:1.0": "Rollback On Error",
    "urn:ietf:params:netconf:capability:notification:1.0": "Notification",
    "urn:ietf:params:netconf:capability:interleave:1.0": "Interleave",
}

# RESTCONF Capability Constants (RFC 8040)
RESTCONF_CAPABILITIES = {
    "urn:ietf:params:restconf:capability:defaults:1.0": "Defaults",
    "urn:ietf:params:restconf:capability:yang-push:1.0": "YANG Push",
    "urn:ietf:params:restconf:capability:yang-push:1.1": "YANG Push 1.1",
}

# YANG Built-in Types (RFC 7950 Section 9.2)
YANG_BUILTIN_TYPES = [
    "int8", "int16", "int32", "int64",
    "uint8", "uint16", "uint32", "uint64",
    "decimal64", "float64", "float32",
    "string", "boolean", "enumeration",
    "bits", "binary", "leafref",
    "identityref", "instance-identifier",
    "union", "array",
]

# NETCONF Operations
NETCONF_OPERATIONS = [
    "get-config", "get", "edit-config", "copy-config",
    "delete-config", "lock", "unlock", "commit",
    "discard-changes", "validate", "close-session", "kill-session"
]

# RESTCONF HTTP Methods
RESTCONF_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]
