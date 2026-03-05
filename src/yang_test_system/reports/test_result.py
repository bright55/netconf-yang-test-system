"""Test Result Data Structures

Data classes for storing and representing test execution results.
Based on RFC 6241 (NETCONF), RFC 7950 (YANG), and RFC 8040 (RESTCONF).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestPhase(Enum):
    """Test execution phase"""
    STATIC_ANALYSIS = "static_analysis"
    CAPABILITY_NEGOTIATION = "capability_negotiation"
    TEST_EXECUTION = "test_execution"
    REPORT_GENERATION = "report_generation"


@dataclass
class TestResult:
    """
    Individual test result data structure.
    
    Represents the result of executing a single test point.
    Corresponds to test execution defined in RFC 6241 Section 8.
    """
    test_id: str
    test_name: str
    passed: bool
    status: TestStatus = TestStatus.PENDING
    actual_result: str = ""
    expected_result: str = ""
    error_message: str = ""
    execution_time: float = 0.0
    rfc_reference: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    device_info: Dict[str, Any] = field(default_factory=dict)
    raw_response: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "passed": self.passed,
            "status": self.status.value,
            "actual_result": self.actual_result,
            "expected_result": self.expected_result,
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "rfc_reference": self.rfc_reference,
            "timestamp": self.timestamp,
            "device_info": self.device_info,
            "raw_response": self.raw_response,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestResult':
        """Create from dictionary"""
        status = data.get('status', 'pending')
        if isinstance(status, str):
            status = TestStatus(status)
        return cls(
            test_id=data['test_id'],
            test_name=data['test_name'],
            passed=data['passed'],
            status=status,
            actual_result=data.get('actual_result', ''),
            expected_result=data.get('expected_result', ''),
            error_message=data.get('error_message', ''),
            execution_time=data.get('execution_time', 0.0),
            rfc_reference=data.get('rfc_reference', ''),
            timestamp=data.get('timestamp', datetime.now().isoformat()),
            device_info=data.get('device_info', {}),
            raw_response=data.get('raw_response'),
        )


@dataclass
class TestSuiteResult:
    """
    Test suite result containing multiple test results.
    
    Represents a collection of test results for a complete test run.
    """
    suite_name: str
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    error_tests: int = 0
    results: List[TestResult] = field(default_factory=list)
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: str = ""
    execution_duration: float = 0.0
    yang_file: str = ""
    device_info: Dict[str, Any] = field(default_factory=dict)
    
    def add_result(self, result: TestResult):
        """Add a test result to the suite"""
        self.results.append(result)
        self.total_tests += 1
        if result.passed:
            self.passed_tests += 1
        elif result.status == TestStatus.SKIPPED:
            self.skipped_tests += 1
        elif result.status == TestStatus.ERROR:
            self.error_tests += 1
        else:
            self.failed_tests += 1
    
    def finalize(self):
        """Finalize the test suite results"""
        self.end_time = datetime.now().isoformat()
        if self.start_time:
            try:
                start = datetime.fromisoformat(self.start_time)
                end = datetime.fromisoformat(self.end_time)
                self.execution_duration = (end - start).total_seconds()
            except ValueError:
                self.execution_duration = 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "suite_name": self.suite_name,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "skipped_tests": self.skipped_tests,
            "error_tests": self.error_tests,
            "success_rate": self.success_rate,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "execution_duration": self.execution_duration,
            "yang_file": self.yang_file,
            "device_info": self.device_info,
            "results": [r.to_dict() for r in self.results],
        }


@dataclass
class CapabilityResult:
    """
    Capability negotiation result.
    
    Represents the result of capability negotiation as defined in RFC 6241 Section 8.1.
    """
    capability_uri: str
    capability_name: str
    is_supported: bool
    version: str = ""
    additional_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "capability_uri": self.capability_uri,
            "capability_name": self.capability_name,
            "is_supported": self.is_supported,
            "version": self.version,
            "additional_info": self.additional_info,
        }


@dataclass
class ValidationResult:
    """
    YANG static validation result.
    
    Represents the result of YANG model validation as defined in RFC 7950.
    """
    is_valid: bool
    yang_file: str
    errors: List[Dict[str, str]] = field(default_factory=list)
    warnings: List[Dict[str, str]] = field(default_factory=list)
    info: List[Dict[str, str]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "is_valid": self.is_valid,
            "yang_file": self.yang_file,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
        }


@dataclass
class ExecutionContext:
    """
    Test execution context containing configuration and state information.
    
    Holds the current execution state during test runs.
    """
    test_phase: TestPhase = TestPhase.STATIC_ANALYSIS
    current_test_id: Optional[str] = None
    device_connection: Any = None
    execution_history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_phase(self, phase: TestPhase):
        """Update the current test phase"""
        self.test_phase = phase
    
    def record_execution(self, test_id: str, result: TestResult):
        """Record test execution in history"""
        self.execution_history.append({
            "test_id": test_id,
            "result": result.to_dict(),
            "timestamp": datetime.now().isoformat(),
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "test_phase": self.test_phase.value,
            "current_test_id": self.current_test_id,
            "execution_history": self.execution_history,
            "metadata": self.metadata,
        }
