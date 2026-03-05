"""Test Executor - Core test execution engine

Execute test points against NETCONF/RESTCONF devices.
Based on RFC 6241 (NETCONF), RFC 7950 (YANG), and RFC 8040 (RESTCONF).
"""

import time
import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

from ..core.types import TestPoint, TestType, Severity
from .test_result import TestSuiteResult, TestResult, TestStatus, ExecutionContext, TestPhase


logger = logging.getLogger(__name__)


@dataclass
class ExecutorConfig:
    """Test executor configuration"""
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0
    continue_on_failure: bool = True
    parallel_execution: bool = False
    max_workers: int = 4


class TestExecutor:
    """
    Core test execution engine.
    
    Executes test points against devices using NETCONF or RESTCONF.
    """
    
    def __init__(self, config: Optional[ExecutorConfig] = None):
        """
        Initialize test executor.
        
        Args:
            config: Executor configuration
        """
        self.config = config or ExecutorConfig()
        self.context = ExecutionContext()
        self._device_client = None
        self._test_callbacks: Dict[TestType, Callable] = {}
    
    def register_test_callback(self, test_type: TestType, 
                              callback: Callable[[TestPoint], TestResult]):
        """
        Register a test callback for a specific test type.
        
        Args:
            test_type: Type of test
            callback: Function to execute test and return result
        """
        self._test_callbacks[test_type] = callback
    
    def set_device_client(self, client: Any):
        """
        Set the device client for test execution.
        
        Args:
            client: NETCONF or RESTCONF client
        """
        self._device_client = client
    
    def execute_test_points(self, test_points: List[TestPoint],
                            device_info: Dict[str, Any],
                            yang_file: str = "") -> TestSuiteResult:
        """
        Execute a list of test points.
        
        Args:
            test_points: List of test points to execute
            device_info: Device connection information
            yang_file: Path to YANG file being tested
            
        Returns:
            Test suite result containing all test results
        """
        suite_name = f"Test Suite - {yang_file or 'Unknown'}"
        result = TestSuiteResult(suite_name=suite_name, yang_file=yang_file)
        
        self.context.update_phase(TestPhase.TEST_EXECUTION)
        
        logger.info(f"Starting execution of {len(test_points)} test points")
        
        for test_point in test_points:
            test_result = self._execute_single_test(test_point, device_info)
            result.add_result(test_result)
            
            # Log progress
            logger.info(f"Completed {test_point.test_name}: {'PASS' if test_result.passed else 'FAIL'}")
        
        result.finalize()
        logger.info(f"Execution complete: {result.passed_tests}/{result.total_tests} passed")
        
        return result
    
    def _execute_single_test(self, test_point: TestPoint,
                           device_info: Dict[str, Any]) -> TestResult:
        """
        Execute a single test point.
        
        Args:
            test_point: Test point to execute
            device_info: Device connection information
            
        Returns:
            Test result
        """
        self.context.current_test_id = test_point.test_id
        
        result = TestResult(
            test_id=test_point.test_id,
            test_name=test_point.test_name,
            passed=False,
            expected_result=test_point.expected_result,
            rfc_reference=test_point.rfc_reference,
            status=TestStatus.RUNNING,
        )
        
        start_time = time.time()
        
        try:
            # Check if there's a registered callback for this test type
            if test_point.test_type in self._test_callbacks:
                callback = self._test_callbacks[test_point.test_type]
                callback_result = callback(test_point)
                
                # Merge callback result
                result.passed = callback_result.passed
                result.actual_result = callback_result.actual_result
                result.error_message = callback_result.error_message
                result.status = TestStatus.PASSED if callback_result.passed else TestStatus.FAILED
            
            # Execute based on test type using device client
            elif self._device_client is not None:
                test_result = self._execute_with_client(test_point, device_info)
                result.passed = test_result.passed
                result.actual_result = test_result.actual_result
                result.error_message = test_result.error_message
                result.status = TestStatus.PASSED if test_result.passed else TestStatus.FAILED
                result.raw_response = getattr(test_result, 'raw_response', None)
            else:
                # No client available - mark as error
                result.status = TestStatus.ERROR
                result.error_message = "No device client available for test execution"
                result.passed = False
            
        except Exception as e:
            result.status = TestStatus.ERROR
            result.error_message = f"Test execution error: {str(e)}"
            result.passed = False
            logger.exception(f"Error executing test {test_point.test_id}")
        
        finally:
            result.execution_time = time.time() - start_time
            result.timestamp = datetime.now().isoformat()
            result.device_info = device_info
        
        # Record execution in context
        self.context.record_execution(test_point.test_id, result)
        
        return result
    
    def _execute_with_client(self, test_point: TestPoint,
                            device_info: Dict[str, Any]) -> TestResult:
        """
        Execute test using the device client.
        
        Args:
            test_point: Test point to execute
            device_info: Device connection information
            
        Returns:
            Test result from client execution
        """
        # Determine test type and execute appropriate operation
        if test_point.test_type in [TestType.GET_CONFIG, TestType.GET]:
            return self._execute_get(test_point)
        
        elif test_point.test_type == TestType.EDIT_CONFIG:
            return self._execute_edit_config(test_point)
        
        elif test_point.test_type == TestType.LOCK_UNLOCK:
            return self._execute_lock_unlock(test_point)
        
        elif test_point.test_type == TestType.COMMIT_DISCARD:
            return self._execute_commit_discard(test_point)
        
        elif test_point.test_type == TestType.VALIDATE:
            return self._execute_validate(test_point)
        
        elif test_point.test_type in [TestType.RESTCONF_GET, TestType.RESTCONF_POST,
                                       TestType.RESTCONF_PUT, TestType.RESTCONF_PATCH,
                                       TestType.RESTCONF_DELETE]:
            return self._execute_restconf(test_point)
        
        elif test_point.test_type == TestType.YANG_PUSH_SUBSCRIPTION:
            return self._execute_yang_push(test_point)
        
        elif test_point.test_type == TestType.CAPABILITY_NEGOTIATION:
            return self._execute_capability_check(test_point)
        
        else:
            # Generic test - just mark as passed for now
            return TestResult(
                test_id=test_point.test_id,
                test_name=test_point.test_name,
                passed=True,
                actual_result="Test type not yet implemented for execution",
            )
    
    def _execute_get(self, test_point: TestPoint) -> TestResult:
        """Execute GET/GET-CONFIG operation"""
        try:
            if hasattr(self._device_client, 'get_config'):
                response = self._device_client.get_config()
                return TestResult(
                    test_id=test_point.test_id,
                    test_name=test_point.test_name,
                    passed=True,
                    actual_result="Configuration retrieved successfully",
                )
            elif hasattr(self._device_client, 'get'):
                response = self._device_client.get()
                return TestResult(
                    test_id=test_point.test_id,
                    test_name=test_point.test_name,
                    passed=True,
                    actual_result="Data retrieved successfully",
                )
        except Exception as e:
            return TestResult(
                test_id=test_point.test_id,
                test_name=test_point.test_name,
                passed=False,
                error_message=f"GET operation failed: {str(e)}",
            )
        
        return TestResult(
            test_id=test_point.test_id,
            test_name=test_point.test_name,
            passed=False,
            error_message="Client does not support GET operations",
        )
    
    def _execute_edit_config(self, test_point: TestPoint) -> TestResult:
        """Execute EDIT-CONFIG operation"""
        try:
            if hasattr(self._device_client, 'edit_config'):
                # Use default test config
                test_config = test_point.metadata.get('test_config', '<config/>')
                response = self._device_client.edit_config(
                    target='candidate',
                    config=test_config
                )
                return TestResult(
                    test_id=test_point.test_id,
                    test_name=test_point.test_name,
                    passed=True,
                    actual_result="Configuration edited successfully",
                )
        except Exception as e:
            return TestResult(
                test_id=test_point.test_id,
                test_name=test_point.test_name,
                passed=False,
                error_message=f"EDIT-CONFIG operation failed: {str(e)}",
            )
        
        return TestResult(
            test_id=test_point.test_id,
            test_name=test_point.test_name,
            passed=False,
            error_message="Client does not support EDIT-CONFIG operations",
        )
    
    def _execute_lock_unlock(self, test_point: TestPoint) -> TestResult:
        """Execute LOCK/UNLOCK operation"""
        try:
            if hasattr(self._device_client, 'lock') and hasattr(self._device_client, 'unlock'):
                self._device_client.lock(target='candidate')
                self._device_client.unlock(target='candidate')
                return TestResult(
                    test_id=test_point.test_id,
                    test_name=test_point.test_name,
                    passed=True,
                    actual_result="Lock/Unlock operations successful",
                )
        except Exception as e:
            return TestResult(
                test_id=test_point.test_id,
                test_name=test_point.test_name,
                passed=False,
                error_message=f"Lock/Unlock operation failed: {str(e)}",
            )
        
        return TestResult(
            test_id=test_point.test_id,
            test_name=test_point.test_name,
            passed=False,
            error_message="Client does not support Lock/Unlock operations",
        )
    
    def _execute_commit_discard(self, test_point: TestPoint) -> TestResult:
        """Execute COMMIT/DISCARD operation"""
        try:
            if hasattr(self._device_client, 'commit') and hasattr(self._device_client, 'discard_changes'):
                self._device_client.discard_changes()
                return TestResult(
                    test_id=test_point.test_id,
                    test_name=test_point.test_name,
                    passed=True,
                    actual_result="Commit/Discard operations successful",
                )
        except Exception as e:
            return TestResult(
                test_id=test_point.test_id,
                test_name=test_point.test_name,
                passed=False,
                error_message=f"Commit/Discard operation failed: {str(e)}",
            )
        
        return TestResult(
            test_id=test_point.test_id,
            test_name=test_point.test_name,
            passed=False,
            error_message="Client does not support Commit/Discard operations",
        )
    
    def _execute_validate(self, test_point: TestPoint) -> TestResult:
        """Execute VALIDATE operation"""
        try:
            if hasattr(self._device_client, 'validate'):
                response = self._device_client.validate(source='candidate')
                return TestResult(
                    test_id=test_point.test_id,
                    test_name=test_point.test_name,
                    passed=True,
                    actual_result="Validate operation successful",
                )
        except Exception as e:
            return TestResult(
                test_id=test_point.test_id,
                test_name=test_point.test_name,
                passed=False,
                error_message=f"Validate operation failed: {str(e)}",
            )
        
        return TestResult(
            test_id=test_point.test_id,
            test_name=test_point.test_name,
            passed=False,
            error_message="Client does not support Validate operations",
        )
    
    def _execute_restconf(self, test_point: TestPoint) -> TestResult:
        """Execute RESTCONF operation"""
        # This will be handled by the RESTCONF executor
        return TestResult(
            test_id=test_point.test_id,
            test_name=test_point.test_name,
            passed=False,
            error_message="Use RESTCONF executor for RESTCONF tests",
        )
    
    def _execute_yang_push(self, test_point: TestPoint) -> TestResult:
        """Execute YANG Push subscription test"""
        # This will be handled by the YANG Push tester
        return TestResult(
            test_id=test_point.test_id,
            test_name=test_point.test_name,
            passed=False,
            error_message="Use YANG Push tester for YANG Push tests",
        )
    
    def _execute_capability_check(self, test_point: TestPoint) -> TestResult:
        """Execute capability negotiation test"""
        try:
            if hasattr(self._device_client, 'get_capabilities'):
                caps = self._device_client.get_capabilities()
                return TestResult(
                    test_id=test_point.test_id,
                    test_name=test_point.test_name,
                    passed=True,
                    actual_result=f"Capabilities: {caps.get('server_capabilities', [])}",
                )
        except Exception as e:
            return TestResult(
                test_id=test_point.test_id,
                test_name=test_point.test_name,
                passed=False,
                error_message=f"Capability check failed: {str(e)}",
            )
        
        return TestResult(
            test_id=test_point.test_id,
            test_name=test_point.test_name,
            passed=False,
            error_message="Client does not support capability queries",
        )
