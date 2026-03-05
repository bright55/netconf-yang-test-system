"""NETCONF Operations - Test NETCONF protocol operations

Based on RFC 6241 - Network Configuration Protocol
"""

import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from .client import NETCONFClient
from ..core.types import TestResult


@dataclass
class OperationResult:
    """NETCONF operation result"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    rpc_error: Optional[Dict] = None


class NETCONFOperations:
    """Test NETCONF protocol operations"""
    
    def __init__(self, client: NETCONFClient):
        """
        Initialize NETCONF operations tester
        
        Args:
            client: NETCONFClient instance
        """
        self.client = client
        
        if not self.client.is_connected():
            raise RuntimeError("Client is not connected")
    
    # ==================== Get Operations ====================
    
    def test_get_config_running(self) -> TestResult:
        """Test get-config from running datastore"""
        start_time = time.time()
        
        try:
            result = self.client.get_config(source='running')
            
            return TestResult(
                test_id="get_config_running",
                test_name="Get Config from Running",
                passed=result.ok,
                actual_result=str(result.data)[:500] if result.data else "No data",
                expected_result="Configuration data from running",
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 7.1"
            )
            
        except Exception as e:
            return TestResult(
                test_id="get_config_running",
                test_name="Get Config from Running",
                passed=False,
                error_message=str(e),
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 7.1"
            )
    
    def test_get_config_candidate(self) -> TestResult:
        """Test get-config from candidate datastore"""
        start_time = time.time()
        
        try:
            # Check if candidate is supported
            caps = self.client.get_capabilities()
            if not any('candidate' in c for c in caps.get('server_capabilities', [])):
                return TestResult(
                    test_id="get_config_candidate",
                    test_name="Get Config from Candidate",
                    passed=False,
                    error_message="Candidate datastore not supported",
                    rfc_reference="RFC 6241 Section 8.3"
                )
            
            result = self.client.get_config(source='candidate')
            
            return TestResult(
                test_id="get_config_candidate",
                test_name="Get Config from Candidate",
                passed=result.ok,
                actual_result="Candidate retrieved" if result.ok else "Failed",
                expected_result="Configuration data from candidate",
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 7.1"
            )
            
        except Exception as e:
            return TestResult(
                test_id="get_config_candidate",
                test_name="Get Config from Candidate",
                passed=False,
                error_message=str(e),
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 7.1"
            )
    
    def test_get_with_filter(self, filter_xml: str) -> TestResult:
        """Test get with XPath filter"""
        start_time = time.time()
        
        try:
            result = self.client.get(filter=filter_xml)
            
            return TestResult(
                test_id="get_with_filter",
                test_name="Get with XPath Filter",
                passed=result.ok,
                actual_result="Filtered data retrieved" if result.ok else "Failed",
                expected_result="Filtered configuration and state data",
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 7.7"
            )
            
        except Exception as e:
            return TestResult(
                test_id="get_with_filter",
                test_name="Get with XPath Filter",
                passed=False,
                error_message=str(e),
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 7.7"
            )
    
    # ==================== Edit Operations ====================
    
    def test_edit_config_merge(self, config_xml: str) -> TestResult:
        """Test edit-config with merge operation"""
        start_time = time.time()
        
        try:
            result = self.client.edit_config(
                target='candidate',
                config=config_xml,
                default_operation='merge'
            )
            
            # Try to commit if candidate supported
            if result.ok:
                try:
                    caps = self.client.get_capabilities()
                    if any('candidate' in c for c in caps.get('server_capabilities', [])):
                        self.client.commit()
                except Exception:
                    pass
            
            return TestResult(
                test_id="edit_config_merge",
                test_name="Edit Config (Merge)",
                passed=result.ok,
                actual_result="Config merged" if result.ok else "Failed to merge",
                expected_result="Configuration merged successfully",
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 7.2"
            )
            
        except Exception as e:
            return TestResult(
                test_id="edit_config_merge",
                test_name="Edit Config (Merge)",
                passed=False,
                error_message=str(e),
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 7.2"
            )
    
    def test_edit_config_replace(self, config_xml: str) -> TestResult:
        """Test edit-config with replace operation"""
        start_time = time.time()
        
        try:
            result = self.client.edit_config(
                target='candidate',
                config=config_xml,
                default_operation='replace'
            )
            
            return TestResult(
                test_id="edit_config_replace",
                test_name="Edit Config (Replace)",
                passed=result.ok,
                actual_result="Config replaced" if result.ok else "Failed to replace",
                expected_result="Configuration replaced successfully",
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 7.2"
            )
            
        except Exception as e:
            return TestResult(
                test_id="edit_config_replace",
                test_name="Edit Config (Replace)",
                passed=False,
                error_message=str(e),
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 7.2"
            )
    
    def test_edit_config_create(self, config_xml: str) -> TestResult:
        """Test edit-config with create operation"""
        start_time = time.time()
        
        try:
            result = self.client.edit_config(
                target='candidate',
                config=config_xml,
                default_operation='merge',
                operation='create'
            )
            
            return TestResult(
                test_id="edit_config_create",
                test_name="Edit Config (Create)",
                passed=result.ok,
                actual_result="Config created" if result.ok else "Failed to create",
                expected_result="Configuration created successfully",
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 7.2"
            )
            
        except Exception as e:
            return TestResult(
                test_id="edit_config_create",
                test_name="Edit Config (Create)",
                passed=False,
                error_message=str(e),
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 7.2"
            )
    
    def test_edit_config_delete(self, config_xml: str) -> TestResult:
        """Test edit-config with delete operation"""
        start_time = time.time()
        
        try:
            result = self.client.edit_config(
                target='candidate',
                config=config_xml,
                operation='delete'
            )
            
            return TestResult(
                test_id="edit_config_delete",
                test_name="Edit Config (Delete)",
                passed=result.ok,
                actual_result="Config deleted" if result.ok else "Failed to delete",
                expected_result="Configuration deleted successfully",
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 7.2"
            )
            
        except Exception as e:
            return TestResult(
                test_id="edit_config_delete",
                test_name="Edit Config (Delete)",
                passed=False,
                error_message=str(e),
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 7.2"
            )
    
    # ==================== Lock Operations ====================
    
    def test_lock_candidate(self) -> TestResult:
        """Test locking candidate datastore"""
        start_time = time.time()
        
        try:
            # Check if candidate is supported
            caps = self.client.get_capabilities()
            if not any('candidate' in c for c in caps.get('server_capabilities', [])):
                return TestResult(
                    test_id="lock_candidate",
                    test_name="Lock Candidate",
                    passed=False,
                    error_message="Candidate datastore not supported"
                )
            
            result = self.client.lock(target='candidate')
            
            # Unlock after test
            if result.ok:
                self.client.unlock(target='candidate')
            
            return TestResult(
                test_id="lock_candidate",
                test_name="Lock Candidate",
                passed=result.ok,
                actual_result="Candidate locked" if result.ok else "Failed to lock",
                expected_result="Lock acquired successfully",
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 7.5"
            )
            
        except Exception as e:
            return TestResult(
                test_id="lock_candidate",
                test_name="Lock Candidate",
                passed=False,
                error_message=str(e),
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 7.5"
            )
    
    def test_lock_running(self) -> TestResult:
        """Test locking running datastore"""
        start_time = time.time()
        
        try:
            result = self.client.lock(target='running')
            
            # Unlock after test
            if result.ok:
                self.client.unlock(target='running')
            
            return TestResult(
                test_id="lock_running",
                test_name="Lock Running",
                passed=result.ok,
                actual_result="Running locked" if result.ok else "Failed to lock",
                expected_result="Lock acquired successfully",
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 7.5"
            )
            
        except Exception as e:
            return TestResult(
                test_id="lock_running",
                test_name="Lock Running",
                passed=False,
                error_message=str(e),
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 7.5"
            )
    
    # ==================== Commit Operations ====================
    
    def test_commit(self) -> TestResult:
        """Test commit operation"""
        start_time = time.time()
        
        try:
            # Check if candidate is supported
            caps = self.client.get_capabilities()
            if not any('candidate' in c for c in caps.get('server_capabilities', [])):
                return TestResult(
                    test_id="commit",
                    test_name="Commit",
                    passed=False,
                    error_message="Candidate datastore not supported"
                )
            
            result = self.client.commit()
            
            return TestResult(
                test_id="commit",
                test_name="Commit",
                passed=result.ok,
                actual_result="Committed" if result.ok else "Failed to commit",
                expected_result="Configuration committed successfully",
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 7.4"
            )
            
        except Exception as e:
            return TestResult(
                test_id="commit",
                test_name="Commit",
                passed=False,
                error_message=str(e),
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 7.4"
            )
    
    def test_confirmed_commit(self, timeout: int = 60) -> TestResult:
        """Test confirmed commit operation"""
        start_time = time.time()
        
        try:
            # Check if confirmed-commit is supported
            caps = self.client.get_capabilities()
            if not any('confirmed-commit' in c for c in caps.get('server_capabilities', [])):
                return TestResult(
                    test_id="confirmed_commit",
                    test_name="Confirmed Commit",
                    passed=False,
                    error_message="Confirmed commit not supported"
                )
            
            result = self.client.commit(confirmed=True, timeout=timeout)
            
            return TestResult(
                test_id="confirmed_commit",
                test_name="Confirmed Commit",
                passed=result.ok,
                actual_result="Confirmed commit started" if result.ok else "Failed",
                expected_result="Confirmed commit started",
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 7.4"
            )
            
        except Exception as e:
            return TestResult(
                test_id="confirmed_commit",
                test_name="Confirmed Commit",
                passed=False,
                error_message=str(e),
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 7.4"
            )
    
    def test_discard_changes(self) -> TestResult:
        """Test discard-changes operation"""
        start_time = time.time()
        
        try:
            # Check if candidate is supported
            caps = self.client.get_capabilities()
            if not any('candidate' in c for c in caps.get('server_capabilities', [])):
                return TestResult(
                    test_id="discard_changes",
                    test_name="Discard Changes",
                    passed=False,
                    error_message="Candidate datastore not supported"
                )
            
            result = self.client.discard_changes()
            
            return TestResult(
                test_id="discard_changes",
                test_name="Discard Changes",
                passed=result.ok,
                actual_result="Changes discarded" if result.ok else "Failed",
                expected_result="Changes discarded successfully",
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 7.4"
            )
            
        except Exception as e:
            return TestResult(
                test_id="discard_changes",
                test_name="Discard Changes",
                passed=False,
                error_message=str(e),
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 7.4"
            )
    
    # ==================== Validate Operations ====================
    
    def test_validate_candidate(self) -> TestResult:
        """Test validate operation on candidate"""
        start_time = time.time()
        
        try:
            # Check if validate is supported
            caps = self.client.get_capabilities()
            if not any('validate' in c for c in caps.get('server_capabilities', [])):
                return TestResult(
                    test_id="validate",
                    test_name="Validate Configuration",
                    passed=False,
                    error_message="Validate not supported"
                )
            
            result = self.client.validate(source='candidate')
            
            return TestResult(
                test_id="validate",
                test_name="Validate Configuration",
                passed=result.ok,
                actual_result="Configuration valid" if result.ok else "Validation failed",
                expected_result="Configuration validated successfully",
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 8.6"
            )
            
        except Exception as e:
            return TestResult(
                test_id="validate",
                test_name="Validate Configuration",
                passed=False,
                error_message=str(e),
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 8.6"
            )
    
    # ==================== Session Operations ====================
    
    def test_close_session(self) -> TestResult:
        """Test close-session operation"""
        start_time = time.time()
        
        try:
            result = self.client.close_session()
            
            return TestResult(
                test_id="close_session",
                test_name="Close Session",
                passed=result.ok,
                actual_result="Session closed" if result.ok else "Failed to close",
                expected_result="Session closed successfully",
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 7.8"
            )
            
        except Exception as e:
            return TestResult(
                test_id="close_session",
                test_name="Close Session",
                passed=False,
                error_message=str(e),
                execution_time=time.time() - start_time,
                rfc_reference="RFC 6241 Section 7.8"
            )
    
    def run_all_tests(self) -> List[TestResult]:
        """Run all NETCONF operation tests"""
        results = []
        
        # Get tests
        results.append(self.test_get_config_running())
        
        # Lock tests
        results.append(self.test_lock_candidate())
        
        # Commit tests (only if candidate supported)
        caps = self.client.get_capabilities()
        if any('candidate' in c for c in caps.get('server_capabilities', [])):
            results.append(self.test_commit())
            results.append(self.test_discard_changes())
        
        # Validate test (only if supported)
        if any('validate' in c for c in caps.get('server_capabilities', [])):
            results.append(self.test_validate_candidate())
        
        return results
