"""NETCONF Client - Handle NETCONF protocol operations

Based on RFC 6241 - Network Configuration Protocol
"""

import socket
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

try:
    from ncclient import manager
    from ncclient.xml_ import NCElement, NCReply
    NCCLIENT_AVAILABLE = True
except ImportError:
    NCCLIENT_AVAILABLE = False


@dataclass
class NETCONFConnectionInfo:
    """NETCONF connection information"""
    host: str
    port: int = 830
    username: Optional[str] = None
    password: Optional[str] = None
    hostkey_verify: bool = False
    transport: str = 'ssh'
    timeout: int = 30


class NETCONFClient:
    """NETCONF client for device communication"""
    
    def __init__(self, host: str, port: int = 830,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 hostkey_verify: bool = False,
                 transport: str = 'ssh',
                 timeout: int = 30):
        """
        Initialize NETCONF client
        
        Args:
            host: Device hostname or IP
            port: NETCONF port (default 830 for SSH)
            username: SSH username
            password: SSH password
            hostkey_verify: Verify host SSH keys
            transport: Transport type (ssh, telnet)
            timeout: Connection timeout in seconds
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.transport = transport
        self.hostkey_verify = hostkey_verify
        self.timeout = timeout
        self.mgr = None
        self.connected = False
        
        if not NCCLIENT_AVAILABLE:
            raise ImportError("ncclient is not installed. Install with: pip install ncclient")
    
    def connect(self) -> bool:
        """
        Connect to NETCONF server
        
        Returns:
            True if connection successful, False otherwise
        """
        if not NCCLIENT_AVAILABLE:
            raise ImportError("ncclient is not installed")
        
        try:
            self.mgr = manager.connect(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                hostkey_verify=self.hostkey_verify,
                device_params={'name': 'default'},
                timeout=self.timeout,
            )
            self.connected = True
            return True
            
        except Exception as e:
            self.connected = False
            raise ConnectionError(f"Failed to connect to {self.host}:{self.port}: {str(e)}")
    
    def disconnect(self):
        """Close NETCONF session"""
        if self.mgr and self.connected:
            try:
                self.mgr.close_session()
            except Exception:
                pass
        self.connected = False
        self.mgr = None
    
    def is_connected(self) -> bool:
        """Check if connected"""
        return self.connected and self.mgr is not None
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get server capabilities
        
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
    
    def get_config(self, source: str = 'running', filter: Optional[str] = None) -> NCElement:
        """
        Get configuration data
        
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
        Get configuration and state data
        
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
        Edit configuration data
        
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
        Copy configuration data
        
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
        Delete configuration data
        
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
        Lock configuration datastore
        
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
        Unlock configuration datastore
        
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
        Commit candidate configuration
        
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
        Discard candidate configuration changes
        
        Returns:
            Reply from device
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to device")
        
        return self.mgr.discard_changes()
    
    def validate(self, source: str = 'candidate') -> NCReply:
        """
        Validate configuration
        
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
        Send custom RPC
        
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
        Close NETCONF session
        
        Returns:
            Reply from device
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to device")
        
        return self.mgr.close_session()
    
    def kill_session(self, session_id: int) -> NCReply:
        """
        Kill another session
        
        Args:
            session_id: Session ID to kill
            
        Returns:
            Reply from device
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to device")
        
        return self.mgr.kill_session(session_id=session_id)
    
    def get_session_id(self) -> Optional[int]:
        """Get current session ID"""
        if self.mgr:
            return self.mgr.session_id
        return None
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
        return False


def create_client(host: str, port: int = 830,
                  username: Optional[str] = None,
                  password: Optional[str] = None) -> NETCONFClient:
    """Factory function to create NETCONF client"""
    return NETCONFClient(
        host=host,
        port=port,
        username=username,
        password=password
    )
