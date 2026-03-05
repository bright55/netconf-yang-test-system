"""Test Point Generator - Generate test points from YANG models

Generate test cases based on YANG data nodes, types, constraints, and operations.
"""

import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .types import TestType, Severity, TestPoint
from .yang_parser import YANGParser


class TestPointGenerator:
    """Generate test points from YANG models"""
    
    def __init__(self, yang_file: str):
        """
        Initialize test point generator
        
        Args:
            yang_file: Path to YANG file
        """
        self.yang_file = yang_file
        self.parser = YANGParser(yang_file)
        self.test_points: List[TestPoint] = []
    
    def generate_all_test_points(self) -> List[TestPoint]:
        """
        Generate all test points from YANG model
        
        Returns:
            List of TestPoint objects
        """
        # Parse YANG file
        parse_result = self.parser.parse()
        
        if "error" in parse_result:
            return []
        
        self.test_points = []
        
        # Generate syntax validation tests
        self._generate_syntax_tests()
        
        # Generate module import tests
        self._generate_import_tests()
        
        # Generate feature tests
        self._generate_feature_tests()
        
        # Generate data node tests
        self._generate_data_node_tests()
        
        # Generate RPC tests
        self._generate_rpc_tests()
        
        # Generate notification tests
        self._generate_notification_tests()
        
        # Generate NETCONF operation tests
        self._generate_netconf_operation_tests()
        
        # Generate RESTCONF operation tests
        self._generate_restconf_operation_tests()
        
        # Generate capability tests
        self._generate_capability_tests()
        
        return self.test_points
    
    def _generate_syntax_tests(self):
        """Generate YANG syntax validation tests"""
        self.test_points.append(TestPoint(
            test_id=self._generate_test_id("syntax_validation"),
            test_name="YANG 1.1 Syntax Validation",
            test_type=TestType.SYNTAX_VALIDATION,
            yang_path="/",
            test_description="Validate YANG file syntax according to RFC 7950",
            test_steps=[
                f"Parse YANG file: {self.yang_file}",
                "Check for syntax errors",
                "Verify YANG version"
            ],
            expected_result="YANG file should be syntactically valid",
            severity=Severity.CRITICAL,
            rfc_reference="RFC 7950"
        ))
    
    def _generate_import_tests(self):
        """Generate module import tests"""
        self.test_points.append(TestPoint(
            test_id=self._generate_test_id("module_import"),
            test_name="Module Import Validation",
            test_type=TestType.MODULE_IMPORT,
            yang_path="/",
            test_description="Validate all imported modules are available",
            test_steps=[
                f"Parse YANG file: {self.yang_file}",
                "Extract imported modules",
                "Verify all imports can be resolved"
            ],
            expected_result="All imported modules should be available",
            severity=Severity.HIGH,
            rfc_reference="RFC 7950 Section 7"
        ))
    
    def _generate_feature_tests(self):
        """Generate feature condition tests"""
        features = self.parser.extract_features()
        
        for feature in features:
            self.test_points.append(TestPoint(
                test_id=self._generate_test_id(f"feature_{feature['name']}"),
                test_name=f"Feature Support: {feature['name']}",
                test_type=TestType.FEATURE_CONDITION,
                yang_path=f"/feature:{feature['name']}",
                test_description=f"Test if device supports feature: {feature['name']}",
                test_steps=[
                    f"Query device for feature: {feature['name']}",
                    "Check if feature is supported",
                    "Verify feature behavior if supported"
                ],
                expected_result="Feature should be supported or gracefully reported as unsupported",
                severity=Severity.MEDIUM,
                rfc_reference="RFC 7950 Section 7.20.1"
            ))
    
    def _generate_data_node_tests(self):
        """Generate tests for data nodes"""
        testable_nodes = self.parser.extract_testable_nodes()
        
        for node in testable_nodes:
            # Mandatory field tests
            if node.get('is_mandatory'):
                self.test_points.append(TestPoint(
                    test_id=self._generate_test_id(f"mandatory_{node['name']}"),
                    test_name=f"Mandatory Field: {node['name']}",
                    test_type=TestType.MANDATORY_FIELD,
                    yang_path=node['path'],
                    test_description=f"Test mandatory field: {node['path']}",
                    test_steps=[
                        f"Attempt to create config without {node['name']}",
                        "Verify operation fails",
                        "Verify error message is appropriate"
                    ],
                    expected_result="Operation should fail with appropriate error",
                    severity=Severity.HIGH,
                    rfc_reference="RFC 7950 Section 3"
                ))
            
            # Default value tests
            if node.get('default_value'):
                self.test_points.append(TestPoint(
                    test_id=self._generate_test_id(f"default_{node['name']}"),
                    test_name=f"Default Value: {node['name']}",
                    test_type=TestType.DEFAULT_VALUE,
                    yang_path=node['path'],
                    test_description=f"Test default value for: {node['path']}",
                    test_steps=[
                        f"Create config without specifying {node['name']}",
                        "Read back the configuration",
                        f"Verify default value '{node['default_value']}' is used"
                    ],
                    expected_result="Default value should be applied when not specified",
                    severity=Severity.MEDIUM,
                    rfc_reference="RFC 7950 Section 7.6.1"
                ))
            
            # Type validation tests
            if node.get('yang_type'):
                self.test_points.append(TestPoint(
                    test_id=self._generate_test_id(f"type_{node['name']}"),
                    test_name=f"Type Validation: {node['name']}",
                    test_type=TestType.TYPE_VALIDATION,
                    yang_path=node['path'],
                    test_description=f"Test type validation for: {node['path']}",
                    test_steps=[
                        f"Try to set {node['name']} with invalid type",
                        "Verify operation fails",
                        "Try to set with valid type",
                        "Verify operation succeeds"
                    ],
                    expected_result="Invalid types should be rejected, valid types accepted",
                    severity=Severity.HIGH,
                    rfc_reference="RFC 7950 Section 9"
                ))
            
            # Range constraint tests
            constraints = node.get('constraints', {})
            if 'range' in constraints or 'length' in constraints:
                self.test_points.append(TestPoint(
                    test_id=self._generate_test_id(f"range_{node['name']}"),
                    test_name=f"Range Constraint: {node['name']}",
                    test_type=TestType.RANGE_CONSTRAINT,
                    yang_path=node['path'],
                    test_description=f"Test range constraint for: {node['path']}",
                    test_steps=[
                        f"Try to set {node['name']} outside valid range",
                        "Verify operation fails",
                        "Try to set within range",
                        "Verify operation succeeds"
                    ],
                    expected_result="Values outside range should be rejected",
                    severity=Severity.HIGH,
                    rfc_reference="RFC 7950 Section 9.2.4"
                ))
            
            # Pattern constraint tests
            if 'pattern' in constraints:
                self.test_points.append(TestPoint(
                    test_id=self._generate_test_id(f"pattern_{node['name']}"),
                    test_name=f"Pattern Constraint: {node['name']}",
                    test_type=TestType.PATTERN_CONSTRAINT,
                    yang_path=node['path'],
                    test_description=f"Test pattern constraint for: {node['path']}",
                    test_steps=[
                        f"Try to set {node['name']} not matching pattern",
                        "Verify operation fails",
                        "Try to set with matching pattern",
                        "Verify operation succeeds"
                    ],
                    expected_result="Non-matching patterns should be rejected",
                    severity=Severity.HIGH,
                    rfc_reference="RFC 7950 Section 9.4.6"
                ))
            
            # Enum validation tests
            if 'enum' in constraints:
                self.test_points.append(TestPoint(
                    test_id=self._generate_test_id(f"enum_{node['name']}"),
                    test_name=f"Enum Validation: {node['name']}",
                    test_type=TestType.ENUM_VALIDATION,
                    yang_path=node['path'],
                    test_description=f"Test enum validation for: {node['path']}",
                    test_steps=[
                        f"Try to set {node['name']} with invalid enum value",
                        "Verify operation fails",
                        f"Try to set with valid enum: {constraints['enum']}",
                        "Verify operation succeeds"
                    ],
                    expected_result="Invalid enum values should be rejected",
                    severity=Severity.HIGH,
                    rfc_reference="RFC 7950 Section 9.6"
                ))
    
    def _generate_rpc_tests(self):
        """Generate RPC validation tests"""
        rpcs = self.parser.extract_rpcs()
        
        for rpc in rpcs:
            self.test_points.append(TestPoint(
                test_id=self._generate_test_id(f"rpc_{rpc['name']}"),
                test_name=f"RPC Execution: {rpc['name']}",
                test_type=TestType.RPC_VALIDATION,
                yang_path=f"/rpc/{rpc['name']}",
                test_description=f"Test RPC: {rpc['name']}",
                test_steps=[
                    f"Invoke RPC: {rpc['name']}",
                    "Verify RPC executes successfully",
                    "Verify output parameters if any"
                ],
                expected_result="RPC should execute and return expected output",
                severity=Severity.HIGH,
                rfc_reference="RFC 7950 Section 7.14"
            ))
            
            # Test RPC input validation
            if rpc.get('input'):
                self.test_points.append(TestPoint(
                    test_id=self._generate_test_id(f"rpc_input_{rpc['name']}"),
                    test_name=f"RPC Input Validation: {rpc['name']}",
                    test_type=TestType.RPC_VALIDATION,
                    yang_path=f"/rpc/{rpc['name']}/input",
                    test_description=f"Test RPC input validation: {rpc['name']}",
                    test_steps=[
                        f"Invoke RPC {rpc['name']} with invalid input",
                        "Verify error is returned",
                        "Invoke with valid input",
                        "Verify success"
                    ],
                    expected_result="Invalid input should be rejected",
                    severity=Severity.HIGH,
                    rfc_reference="RFC 7950 Section 7.14"
                ))
    
    def _generate_notification_tests(self):
        """Generate notification validation tests"""
        notifications = self.parser.extract_notifications()
        
        for notif in notifications:
            self.test_points.append(TestPoint(
                test_id=self._generate_test_id(f"notification_{notif['name']}"),
                test_name=f"Notification: {notif['name']}",
                test_type=TestType.NOTIFICATION_VALIDATION,
                yang_path=f"/notification/{notif['name']}",
                test_description=f"Test notification: {notif['name']}",
                test_steps=[
                    f"Subscribe to notification: {notif['name']}",
                    "Trigger notification event",
                    "Verify notification is received"
                ],
                expected_result="Notification should be received when event occurs",
                severity=Severity.MEDIUM,
                rfc_reference="RFC 7950 Section 7.16"
            ))
    
    def _generate_netconf_operation_tests(self):
        """Generate NETCONF operation tests"""
        # Get-config test
        self.test_points.append(TestPoint(
            test_id=self._generate_test_id("get_config"),
            test_name="NETCONF get-config Operation",
            test_type=TestType.GET_CONFIG,
            yang_path="/",
            test_description="Test NETCONF get-config operation",
            test_steps=[
                "Connect to device via NETCONF",
                "Send get-config request",
                "Verify configuration is returned"
            ],
            expected_result="Configuration should be returned successfully",
            severity=Severity.CRITICAL,
            rfc_reference="RFC 6241 Section 7.1"
        ))
        
        # Get test
        self.test_points.append(TestPoint(
            test_id=self._generate_test_id("get"),
            test_name="NETCONF get Operation",
            test_type=TestType.GET_CONFIG,
            yang_path="/",
            test_description="Test NETCONF get operation (including state data)",
            test_steps=[
                "Connect to device via NETCONF",
                "Send get request",
                "Verify configuration and state data are returned"
            ],
            expected_result="Configuration and state data should be returned",
            severity=Severity.CRITICAL,
            rfc_reference="RFC 6241 Section 7.7"
        ))
        
        # Edit-config tests
        for operation in ['merge', 'replace', 'create', 'delete']:
            self.test_points.append(TestPoint(
                test_id=self._generate_test_id(f"edit_config_{operation}"),
                test_name=f"NETCONF edit-config ({operation})",
                test_type=TestType.EDIT_CONFIG,
                yang_path="/",
                test_description=f"Test NETCONF edit-config with {operation} operation",
                test_steps=[
                    "Connect to device via NETCONF",
                    f"Edit config using {operation} operation",
                    "Commit changes",
                    "Verify changes were applied"
                ],
                expected_result=f"Edit-config with {operation} should work correctly",
                severity=Severity.CRITICAL,
                rfc_reference="RFC 6241 Section 7.2"
            ))
        
        # Lock/Unlock test
        self.test_points.append(TestPoint(
            test_id=self._generate_test_id("lock_unlock"),
            test_name="NETCONF lock/unlock Operation",
            test_type=TestType.LOCK_UNLOCK,
            yang_path="/",
            test_description="Test NETCONF lock and unlock operations",
            test_steps=[
                "Connect to device via NETCONF",
                "Lock candidate datastore",
                "Verify lock is acquired",
                "Unlock candidate datastore",
                "Verify lock is released"
            ],
            expected_result="Lock/unlock should work correctly",
            severity=Severity.HIGH,
            rfc_reference="RFC 6241 Section 7.5"
        ))
        
        # Commit test
        self.test_points.append(TestPoint(
            test_id=self._generate_test_id("commit"),
            test_name="NETCONF commit Operation",
            test_type=TestType.COMMIT_DISCARD,
            yang_path="/",
            test_description="Test NETCONF commit operation",
            test_steps=[
                "Connect to device via NETCONF",
                "Edit candidate configuration",
                "Commit changes",
                "Verify changes are in running config"
            ],
            expected_result="Commit should successfully apply changes",
            severity=Severity.CRITICAL,
            rfc_reference="RFC 6241 Section 7.4"
        ))
        
        # Validate test
        self.test_points.append(TestPoint(
            test_id=self._generate_test_id("validate"),
            test_name="NETCONF validate Operation",
            test_type=TestType.VALIDATE,
            yang_path="/",
            test_description="Test NETCONF validate operation",
            test_steps=[
                "Connect to device via NETCONF",
                "Edit candidate with invalid config",
                "Try to validate",
                "Verify validation fails appropriately"
            ],
            expected_result="Invalid configuration should be rejected",
            severity=Severity.HIGH,
            rfc_reference="RFC 6241 Section 8.6"
        ))
    
    def _generate_restconf_operation_tests(self):
        """Generate RESTCONF operation tests"""
        # RESTCONF GET
        self.test_points.append(TestPoint(
            test_id=self._generate_test_id("restconf_get"),
            test_name="RESTCONF GET Operation",
            test_type=TestType.RESTCONF_GET,
            yang_path="/",
            test_description="Test RESTCONF GET operation",
            test_steps=[
                "Connect to device via RESTCONF",
                "Send GET request",
                "Verify data is returned"
            ],
            expected_result="Data should be returned successfully",
            severity=Severity.CRITICAL,
            rfc_reference="RFC 8040 Section 3.3"
        ))
        
        # RESTCONF POST
        self.test_points.append(TestPoint(
            test_id=self._generate_test_id("restconf_post"),
            test_name="RESTCONF POST Operation",
            test_type=TestType.RESTCONF_POST,
            yang_path="/",
            test_description="Test RESTCONF POST to create data",
            test_steps=[
                "Connect to device via RESTCONF",
                "Send POST request with new data",
                "Verify resource is created"
            ],
            expected_result="Resource should be created successfully",
            severity=Severity.CRITICAL,
            rfc_reference="RFC 8040 Section 3.4"
        ))
        
        # RESTCONF PUT
        self.test_points.append(TestPoint(
            test_id=self._generate_test_id("restconf_put"),
            test_name="RESTCONF PUT Operation",
            test_type=TestType.RESTCONF_PUT,
            yang_path="/",
            test_description="Test RESTCONF PUT to replace data",
            test_steps=[
                "Connect to device via RESTCONF",
                "Send PUT request with replacement data",
                "Verify resource is replaced"
            ],
            expected_result="Resource should be replaced successfully",
            severity=Severity.CRITICAL,
            rfc_reference="RFC 8040 Section 3.5"
        ))
        
        # RESTCONF PATCH
        self.test_points.append(TestPoint(
            test_id=self._generate_test_id("restconf_patch"),
            test_name="RESTCONF PATCH Operation",
            test_type=TestType.RESTCONF_PATCH,
            yang_path="/",
            test_description="Test RESTCONF PATCH to modify data",
            test_steps=[
                "Connect to device via RESTCONF",
                "Send PATCH request with modifications",
                "Verify resource is modified"
            ],
            expected_result="Resource should be modified successfully",
            severity=Severity.CRITICAL,
            rfc_reference="RFC 8040 Section 4.5"
        ))
        
        # RESTCONF DELETE
        self.test_points.append(TestPoint(
            test_id=self._generate_test_id("restconf_delete"),
            test_name="RESTCONF DELETE Operation",
            test_type=TestType.RESTCONF_DELETE,
            yang_path="/",
            test_description="Test RESTCONF DELETE operation",
            test_steps=[
                "Connect to device via RESTCONF",
                "Send DELETE request",
                "Verify resource is deleted"
            ],
            expected_result="Resource should be deleted successfully",
            severity=Severity.CRITICAL,
            rfc_reference="RFC 8040 Section 3.6"
        ))
    
    def _generate_capability_tests(self):
        """Generate capability negotiation tests"""
        # Base capability test
        self.test_points.append(TestPoint(
            test_id=self._generate_test_id("capability_base"),
            test_name="NETCONF Base Capability",
            test_type=TestType.CAPABILITY_NEGOTIATION,
            yang_path="/",
            test_description="Test NETCONF base:1 capability",
            test_steps=[
                "Connect to device via NETCONF",
                "Query server capabilities",
                "Verify :base:1.0 or :base:1.1 is advertised"
            ],
            expected_result="Base capability should be advertised",
            severity=Severity.CRITICAL,
            rfc_reference="RFC 6241 Section 8.1"
        ))
        
        # Candidate capability test
        self.test_points.append(TestPoint(
            test_id=self._generate_test_id("capability_candidate"),
            test_name="NETCONF Candidate Capability",
            test_type=TestType.CAPABILITY_NEGOTIATION,
            yang_path="/",
            test_description="Test NETCONF candidate capability",
            test_steps=[
                "Connect to device via NETCONF",
                "Query server capabilities",
                "Check if :candidate is advertised"
            ],
            expected_result="Candidate capability should be advertised if supported",
            severity=Severity.HIGH,
            rfc_reference="RFC 6241 Section 8.3"
        ))
        
        # Writable-running capability test
        self.test_points.append(TestPoint(
            test_id=self._generate_test_id("capability_writable_running"),
            test_name="NETCONF Writable-Running Capability",
            test_type=TestType.CAPABILITY_NEGOTIATION,
            yang_path="/",
            test_description="Test NETCONF writable-running capability",
            test_steps=[
                "Connect to device via NETCONF",
                "Query server capabilities",
                "Check if :writable-running is advertised"
            ],
            expected_result="Writable-running capability should be advertised if supported",
            severity=Severity.HIGH,
            rfc_reference="RFC 6241 Section 8.2"
        ))
        
        # Validate capability test
        self.test_points.append(TestPoint(
            test_id=self._generate_test_id("capability_validate"),
            test_name="NETCONF Validate Capability",
            test_type=TestType.CAPABILITY_NEGOTIATION,
            yang_path="/",
            test_description="Test NETCONF validate capability",
            test_steps=[
                "Connect to device via NETCONF",
                "Query server capabilities",
                "Check if :validate is advertised"
            ],
            expected_result="Validate capability should be advertised if supported",
            severity=Severity.MEDIUM,
            rfc_reference="RFC 6241 Section 8.6"
        ))
    
    def _generate_test_id(self, base: str) -> str:
        """Generate unique test ID"""
        # Create a hash from yang_file and base
        hash_input = f"{self.yang_file}:{base}".encode()
        hash_value = hashlib.md5(hash_input).hexdigest()[:8]
        return f"test_{hash_value}"
    
    def get_test_points_by_type(self, test_type: TestType) -> List[TestPoint]:
        """Get test points filtered by type"""
        return [tp for tp in self.test_points if tp.test_type == test_type]
    
    def get_test_points_by_severity(self, severity: Severity) -> List[TestPoint]:
        """Get test points filtered by severity"""
        return [tp for tp in self.test_points if tp.severity == severity]
    
    def get_executable_test_points(self) -> List[TestPoint]:
        """Get only auto-executable test points"""
        return [tp for tp in self.test_points if tp.auto_executable]
