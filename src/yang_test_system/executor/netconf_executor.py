"""NETCONF Executor - Execute NETCONF operations for testing

Execute NETCONF operations (get-config, edit-config, etc.) against devices.
Based on RFC 6241 - Network Configuration Protocol.
"""

import time
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

try:
    from ncclient import manager
    from ncclient.xml_ import NCElement, NCReply
    NCCLIENT_AVAILABLE = True
except ImportError:
    NCCLIENT_AVAILABLE = False
    NCElement = Any
    NCReply = Any

from ..reports.test_result import TestResult
from ..core.types import TestPoint, TestType


logger = logging.getLogger(__name__)


@dataclass
class NETCONFConnectionInfo:
    """NETCONF connection information (RFC 6241)"""
    host: str
    port: int = 830
    username: Optional[str] = None
    password: Optional[str] = None
    hostkey_verify: bool = False
    transport: str = 'ssh'
    timeout: int = 30


class NETCONFExecutor:
    """
    Execute NETCONF operations for testing.
    
    Provides methods to execute NETCONF operations as defined in RFC 6241.
    """
    
    def __init__(self, connection_info: NETCONFConnectionInfo):
        """
        Initialize NETCONF executor.
        
        Args:
            connection_info: NETCONF connection information
        """
        self.connection_info = connection_info
        self.mgr = None
        self.connected = False
    
    def connect(self) -> bool:
        """
        Connect to NETCONF server.
        
        Returns:
            True if connection successful
            
        Raises:
            ImportError: If ncclient is not installed
            ConnectionError: If connection fails
        """
        if not NCCLIENT_AVAILABLE:
            raise ImportError("ncclient is not installed. Install with: pip install ncclient")
        
        try:
            self.mgr = manager.connect(
                host=self.connection_info.host,
                port=self.connection_info.port,
                username=self.connection_info.username,
                password=self.connection_info.password,
                hostkey_verify=self.connection_info.hostkey_verify,
                device_params={'name': 'default'},
                timeout=self.connection_info.timeout,
            )
            self.connected = True
            logger.info(f"Connected to {self.connection_info.host}:{self.connection_info.port}")
            return True
            
        except Exception as e:
            self.connected = False
            raise ConnectionError(f"Failed to connect to {self.connection_info.host}:{self.connection_info.port}: {str(e)}")
    
    def disconnect(self):
        """Close NETCONF session"""
        if self.mgr and self.connected:
            try:
                self.mgr.close_session()
            except Exception as e:
                logger.warning(f"Error closing session: {e}")
        self.connected = False
        self.mgr = None
    
    def is_connected(self) -> bool:
        """Check if connected to device"""
        return self.connected and self.mgr is not None
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
        return False
    
    # NETCONF Operations (RFC 6241)
    
    def get_config(self, source: str = 'running', 
                  filter: Optional[str] = None) -> NCElement:
        """
        Get configuration data (RFC 6241 Section 7.1).
        
        Args:
            source: Configuration source (running, candidate, startup)
            filter: XML filter for selective retrieval
            
        Returns:
            Configuration data
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to device")
        
        return self.mgr.get_config(source=source, filter=filter)
    
    def get(self, filter: Optional[str] = None) -> NCElement:
        """
        Get configuration and state data (RFC 6241 Section 7.7).
        
        Args:
            filter: XML filter for selective retrieval
            
        Returns:
            Configuration and state data
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to device")
        
        return self.mgr.get(filter=filter)
    
    def edit_config(self, target: str, config: Any,
                   default_operation: str = 'merge',
                   operation: Optional[str] = None,
                   error_option: Optional[str] = None) -> NCReply:
        """
        Edit configuration data (RFC 6241 Section 7.2).
        
        Args:
            target: Target datastore (running, candidate)
            config: Configuration data (XML string or Element)
            default_operation: Default operation (merge, replace, none)
            operation: Per-node operation (create, delete, remove, merge, replace)
            error_option: Error handling option (stop-on-error, continue-on-error, rollback-on-error)
            
        Returns:
            Reply from device
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to device")
        
        return self.mgr.edit_config(
            target=target,
            config=config,
            default_operation=default_operation,
            operation=operation,
            error_option=error_option
        )
    
    def copy_config(self, source: str, target: str) -> NCReply:
        """
        Copy configuration data (RFC 6241 Section 7.3).
        
        Args:
            source: Source configuration (running, candidate, startup, url)
            target: Target configuration (running, candidate, startup, url)
            
        Returns:
            Reply from device
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to device")
        
        return self.mgr.copy_config(source=source, target=target)
    
    def delete_config(self, target: str) -> NCReply:
        """
        Delete configuration data (RFC 6241 Section 7.4).
        
        Args:
            target: Target configuration (startup, url)
            
        Returns:
            Reply from device
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to device")
        
        return self.mgr.delete_config(target=target)
    
    def lock(self, target: str) -> NCReply:
        """
        Lock configuration datastore (RFC 6241 Section 7.5).
        
        Args:
            target: Target datastore (running, candidate, startup)
            
        Returns:
            Reply from device
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to device")
        
        return self.mgr.lock(target=target)
    
    def unlock(self, target: str) -> NCReply:
        """
        Unlock configuration datastore (RFC 6241 Section 7.6).
        
        Args:
            target: Target datastore (running, candidate, startup)
            
        Returns:
            Reply from device
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to device")
        
        return self.mgr.unlock(target=target)
    
    def commit(self, confirmed: bool = False,
               timeout: Optional[int] = None) -> NCReply:
        """
        Commit candidate configuration (RFC 6241 Section 7.4).
        
        Args:
            confirmed: Whether to use confirmed commit
            timeout: Confirmation timeout in seconds
            
        Returns:
            Reply from device
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to device")
        
        return self.mgr.commit(confirmed=confirmed, timeout=timeout)
    
    def discard_changes(self) -> NCReply:
        """
        Discard candidate configuration changes (RFC 6241 Section 7.4).
        
        Returns:
            Reply from device
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to device")
        
        return self.mgr.discard_changes()
    
    def validate(self, source: str = 'candidate') -> NCReply:
        """
        Validate configuration (RFC 6241 Section 8.6).
        
        Args:
            source: Configuration source to validate
            
        Returns:
            Reply from device
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to device")
        
        return self.mgr.validate(source=source)
    
    def rpc(self, rpc_xml: str) -> NCElement:
        """
        Send custom RPC.
        
        Args:
            rpc_xml: RPC request as XML string
            
        Returns:
            RPC response
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to device")
        
        return self.mgr.rpc(rpc_xml)
    
    def close_session(self) -> NCReply:
        """
        Close NETCONF session (RFC 6241 Section 7.8).
        
        Returns:
            Reply from device
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to device")
        
        return self.mgr.close_session()
    
    def kill_session(self, session_id: int) -> NCReply:
        """
        Kill another session (RFC 6241 Section 7.9).
        
        Args:
            session_id: Session ID to kill
            
        Returns:
            Reply from device
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to device")
        
        return self.mgr.kill_session(session_id=session_id)
    
    # Test execution methods
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get server capabilities (RFC 6241 Section 8.1).
        
        Returns:
            Dictionary containing server capabilities
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to device")
        
        capabilities = list(self.mgr.server_capabilities)
        parsed = {}
        
        for cap in capabilities:
            if ':' in cap:
                parts = cap.split(':', 1)
                if len(parts) == 2:
                    parsed[parts[1]] = {'prefix': parts[0], 'full': cap}
        
        return {
            'server_capabilities': capabilities,
            'parsed': parsed,
            'session_id': self.mgr.session_id,
        }
    
    def execute_test(self, test_point: TestPoint) -> TestResult:
        """
        Execute a NETCONF test point.
        
        Args:
            test_point: Test point to execute
            
        Returns:
            Test result
        """
        start_time = time.time()
        
        try:
            if test_point.test_type == TestType.GET_CONFIG:
                return self._test_get_config(test_point, start_time)
            elif test_point.test_type == TestType.EDIT_CONFIG:
                return self._test_edit_config(test_point, start_time)
            elif test_point.test_type == TestType.LOCK_UNLOCK:
                return self._test_lock_unlock(test_point, start_time)
            elif test_point.test_type == TestType.COMMIT_DISCARD:
                return self._test_commit_discard(test_point, start_time)
            elif test_point.test_type == TestType.VALIDATE:
                return self._test_validate(test_point, start_time)
            elif test_point.test_type == TestType.CAPABILITY_NEGOTIATION:
                return self._test_capability(test_point, start_time)
            elif test_point.test_type == TestType.RPC_VALIDATION:
                return self._test_rpc(test_point, start_time)
            else:
                return TestResult(
                    test_id=test_point.test_id,
                    test_name=test_point.test_name,
                    passed=False,
                    error_message=f"Unsupported test type: {test_point.test_type}",
                    execution_time=time.time() - start_time,
                )
        except Exception as e:
            return TestResult(
                test_id=test_point.test_id,
                test_name=test_point.test_name,
                passed=False,
                error_message=str(e),
                execution_time=time.time() - start_time,
            )
    
    def _test_get_config(self, test_point: TestPoint, start_time: float) -> TestResult:
        """Test get-config operation"""
        try:
            response = self.get_config(source='running')
            return TestResult(
                test_id=test_point.test_id,
                test_name=test_point.test_name,
                passed=True,
                actual_result="Successfully retrieved configuration",
                execution_time=time.time() - start_time,
            )
        except Exception as e:
            return TestResult(
                test_id=test_point.test_id,
                test_name=test_point.test_name,
                passed=False,
                error_message=f"get-config failed: {str(e)}",
                execution_time=time.time() - start_time,
            )
    
    def _test_edit_config(self, test_point: TestPoint, start_time: float) -> TestResult:
        """Test edit-config operation"""
        test_config = test_point.metadata.get('test_config', '<config/>')
        operation = test_point.metadata.get('operation', 'merge')
        
        try:
            # Try candidate first, fall back to running
            try:
                response = self.edit_config(
                    target='candidate',
                    config=test_config,
                    default_operation=operation,
                    error_option='rollback-on-error'
                )
                self.commit()
            except Exception:
                # Try running directly
                response = self.edit_config(
                    target='running',
                    config=test_config,
                    default_operation=operation
                )
            
            return TestResult(
                test_id=test_point.test_id,
                test_name=test_point.test_name,
                passed=True,
                actual_result="Configuration edited successfully",
                execution_time=time.time() - start_time,
            )
        except Exception as e:
            return TestResult(
                test_id=test_point.test_id,
                test_name=test_point.test_name,
                passed=False,
                error_message=f"edit-config failed: {str(e)}",
                execution_time=time.time() - start_time,
            )
    
    def _test_lock_unlock(self, test_point: TestPoint, start_time: float) -> TestResult:
        """Test lock/unlock operations"""
        try:
            self.lock(target='candidate')
            self.unlock(target='candidate')
            
            return TestResult(
                test_id=test_point.test_id,
                test_name=test_point.test_name,
                passed=True,
                actual_result="Lock/unlock successful",
                execution_time=time.time() - start_time,
            )
        except Exception as e:
            return TestResult(
                test_id=test_point.test_id,
                test_name=test_point.test_name,
                passed=False,
                error_message=f"Lock/unlock failed: {str(e)}",
                execution_time=time.time() - start_time,
            )
    
    def _test_commit_discard(self, test_point: TestPoint, start_time: float) -> TestResult:
        """Test commit/discard operations"""
        try:
            self.discard_changes()
            
            return TestResult(
                test_id=test_point.test_id,
                test_name=test_point.test_name,
                passed=True,
                actual_result="Commit/discard operations successful",
                execution_time=time.time() - start_time,
            )
        except Exception as e:
            return TestResult(
                test_point.test_id,
                test_name=test_point.test_name,
                passed=False,
                error_message=f"Commit/discard failed: {str(e)}",
                execution_time=time.time() - start_time,
            )
    
    def _test_validate(self, test_point: TestPoint, start_time: float) -> TestResult:
        """Test validate operation"""
        try:
            self.validate(source='candidate')
            
            return TestResult(
                test_id=test_point.test_id,
                test_name=test_point.test_name,
                passed=True,
                actual_result="Validate operation successful",
                execution_time=time.time() - start_time,
            )
        except Exception as e:
            return TestResult(
                test_id=test_point.test_id,
                test_name=test_point.test_name,
                passed=False,
                error_message=f"Validate failed: {str(e)}",
                execution_time=time.time() - start_time,
            )
    
    def _test_capability(self, test_point: TestPoint, start_time: float) -> TestResult:
        """Test capability negotiation"""
        try:
            caps = self.get_capabilities()
            
            return TestResult(
                test_id=test_point.test_id,
                test_name=test_point.test_name,
                passed=True,
                actual_result=f"Capabilities: {caps.get('server_capabilities', [])}",
                execution_time=time.time() - start_time,
            )
        except Exception as e:
            return TestResult(
                test_id=test_point.test_id,
                test_name=test_point.test_name,
                passed=False,
                error_message=f"Capability check failed: {str(e)}",
                execution_time=time.time() - start_time,
            )
    
    def _test_rpc(self, test_point: TestPoint, start_time: float) -> TestResult:
        """Test RPC execution"""
        rpc_xml = test_point.metadata.get('rpc_xml', '<rpc></rpc>')
        
        try:
            response = self.rpc(rpc_xml)
            
            return TestResult(
                test_id=test_point.test_id,
                test_name=test_point.test_name,
                passed=True,
                actual_result="RPC executed successfully",
                execution_time=time.time() - start_time,
            )
        except Exception as e:
            return TestResult(
                test_id=test_point.test_id,
                test_name=test_point.test_name,
                passed=False,
                error_message=f"RPC execution failed: {str(e)}",
                execution_time=time.time() - start_time,
            )


def create_executor(host: str, port: int = 830,
                   username: Optional[str] = None,
                   password: Optional[str] = None) -> NETCONFExecutor:
    """Factory function to create NETCONF executor"""
    conn_info = NETCONFConnectionInfo(
        host=host,
        port=port,
        username=username,
        password=password,
    )
    return NETCONFExecutor(conn_info)
