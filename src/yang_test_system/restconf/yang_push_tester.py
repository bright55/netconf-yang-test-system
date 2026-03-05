"""YANG Push Tester - YANG Push subscription testing (RFC 8641)

Based on RFC 8641 - Subscriptions to YANG Datastore and Push
"""

import time
import threading
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

import requests

from .tester import RESTCONFTester, RESTCONFResponse


class SubscriptionType(Enum):
    """YANG Push subscription types"""
    PERIODIC = "periodic"
    ON_CHANGE = "on_change"
    PERIODIC_ON_CHANGE = "periodic_on_change"


class SubscriptionState(Enum):
    """Subscription states"""
    ESTABLISHED = "established"
    MODIFIED = "modified"
    TERMINATED = "terminated"
    ERROR = "error"


@dataclass
class YANGPushSubscription:
    """YANG Push subscription"""
    subscription_id: str
    state: SubscriptionState
    stream: str
    xpath_filter: str
    subscription_type: SubscriptionType
    created_at: float = 0

    def __post_init__(self):
        if self.created_at == 0:
            self.created_at = time.time()


@dataclass
class PushUpdate:
    """YANG Push update notification"""
    subscription_id: str
    datastore_ce: str  # datastore-contents-elemen
    timestamp: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class YANGPushTester:
    """YANG Push subscription tester (RFC 8641)"""

    def __init__(self, base_url: str, username: str, password: str,
                 timeout: int = 30):
        """
        Initialize YANG Push tester

        Args:
            base_url: RESTCONF base URL
            username: Authentication username
            password: Authentication password
            timeout: Request timeout
        """
        self.restconf = RESTCONFTester(base_url, username, password, timeout)
        self.subscriptions: Dict[str, YANGPushSubscription] = {}
        self.notification_callback: Optional[Callable] = None
        self.notification_thread: Optional[threading.Thread] = None
        self.running = False

    def check_capability(self) -> bool:
        """
        Check if device supports YANG Push

        Returns:
            True if YANG Push is supported
        """
        capabilities = self.restconf.get_capabilities()

        caps = capabilities.get('capabilities', [])
        for cap in caps:
            if 'yang-push' in cap:
                return True

        return False

    def create_subscription(self, stream: str = "NETCONF",
                            xpath_filter: str = "/",
                            periodicity: Optional[int] = None,
                            dampening_period: Optional[int] = None,
                            sync_on_start: bool = True) -> Optional[YANGPushSubscription]:
        """
        Create a YANG Push subscription (RFC 8641 Section 3.1)

        Args:
            stream: Stream name (NETCONF, SNMP, etc.)
            xpath_filter: XPath filter for datastore subset
            periodicity: Period in seconds for periodic updates
            dampening_period: Dampening period in seconds
            sync_on_start: Include sync-up update

        Returns:
            YANGPushSubscription or None on failure
        """
        # Build establish-subscription RPC
        subscription_type = SubscriptionType.PERIODIC if periodicity else SubscriptionType.ON_CHANGE

        rpc_input = {
            "establish-subscription": {
                "stream": stream,
                "xpath-filter": xpath_filter,
            }
        }

        if periodicity:
            rpc_input["establish-subscription"]["periodicity"] = periodicity

        if dampening_period:
            rpc_input["establish-subscription"]["dampening-period"] = dampening_period

        if sync_on_start:
            rpc_input["establish-subscription"]["dampening-period"] = 0

        # Send RPC
        response = self.restconf.rpc("establish-subscription", rpc_input)

        if not response.ok:
            print(f"Failed to create subscription: {self.restconf.parse_error(response)}")
            return None

        # Parse response
        data = response.data
        if not data or 'subscription-id' not in data:
            print("No subscription ID in response")
            return None

        subscription_id = str(data['subscription-id'])

        subscription = YANGPushSubscription(
            subscription_id=subscription_id,
            state=SubscriptionState.ESTABLISHED,
            stream=stream,
            xpath_filter=xpath_filter,
            subscription_type=subscription_type,
        )

        self.subscriptions[subscription_id] = subscription
        return subscription

    def modify_subscription(self, subscription_id: str,
                           xpath_filter: Optional[str] = None,
                           periodicity: Optional[int] = None) -> bool:
        """
        Modify an existing subscription (RFC 8641 Section 3.2)

        Args:
            subscription_id: Subscription ID to modify
            xpath_filter: New XPath filter
            periodicity: New periodicity

        Returns:
            True if successful
        """
        if subscription_id not in self.subscriptions:
            print(f"Subscription {subscription_id} not found")
            return False

        rpc_input = {
            "modify-subscription": {
                "subscription-id": int(subscription_id),
            }
        }

        if xpath_filter:
            rpc_input["modify-subscription"]["xpath-filter"] = xpath_filter

        if periodicity:
            rpc_input["modify-subscription"]["periodicity"] = periodicity

        response = self.restconf.rpc("modify-subscription", rpc_input)

        if not response.ok:
            print(f"Failed to modify subscription: {self.restconf.parse_error(response)}")
            return False

        # Update subscription state
        self.subscriptions[subscription_id].state = SubscriptionState.MODIFIED

        if xpath_filter:
            self.subscriptions[subscription_id].xpath_filter = xpath_filter

        if periodicity:
            self.subscriptions[subscription_id].subscription_type = SubscriptionType.PERIODIC

        return True

    def terminate_subscription(self, subscription_id: str) -> bool:
        """
        Terminate a subscription (RFC 8641 Section 3.3)

        Args:
            subscription_id: Subscription ID to terminate

        Returns:
            True if successful
        """
        if subscription_id not in self.subscriptions:
            print(f"Subscription {subscription_id} not found")
            return False

        rpc_input = {
            "terminate-subscription": {
                "subscription-id": int(subscription_id),
            }
        }

        response = self.restconf.rpc("terminate-subscription", rpc_input)

        if not response.ok:
            print(f"Failed to terminate subscription: {self.restconf.parse_error(response)}")
            return False

        # Update subscription state
        self.subscriptions[subscription_id].state = SubscriptionState.TERMINATED

        # Remove from active subscriptions
        del self.subscriptions[subscription_id]

        return True

    def delete_subscription(self, subscription_id: str) -> bool:
        """
        Delete a subscription (alias for terminate)

        Args:
            subscription_id: Subscription ID

        Returns:
            True if successful
        """
        return self.terminate_subscription(subscription_id)

    def get_subscription_info(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """
        Get subscription information

        Args:
            subscription_id: Subscription ID

        Returns:
            Subscription information dictionary
        """
        if subscription_id not in self.subscriptions:
            return None

        sub = self.subscriptions[subscription_id]

        return {
            "subscription-id": sub.subscription_id,
            "state": sub.state.value,
            "stream": sub.stream,
            "xpath-filter": sub.xpath_filter,
            "subscription-type": sub.subscription_type.value,
            "created-at": sub.created_at,
        }

    def list_subscriptions(self) -> List[Dict[str, Any]]:
        """
        List all active subscriptions

        Returns:
            List of subscription info dictionaries
        """
        result = []
        for sub_id in self.subscriptions:
            info = self.get_subscription_info(sub_id)
            if info:
                result.append(info)
        return result

    def set_notification_callback(self, callback: Callable[[PushUpdate], None]):
        """
        Set callback for push notifications

        Args:
            callback: Function to call with PushUpdate
        """
        self.notification_callback = callback

    def start_notification_listener(self, port: int = 8080):
        """
        Start listening for push notifications

        Note: This requires the device to support notification callback.
        For testing purposes, this is a placeholder implementation.

        Args:
            port: Port to listen on
        """
        self.running = True

        def listener():
            # Placeholder for notification listener
            # In production, this would start an HTTP server to receive
            # push notifications from the device
            while self.running:
                time.sleep(1)

        self.notification_thread = threading.Thread(target=listener, daemon=True)
        self.notification_thread.start()

    def stop_notification_listener(self):
        """Stop listening for notifications"""
        self.running = False
        if self.notification_thread:
            self.notification_thread.join(timeout=2)

    def close(self):
        """Clean up resources"""
        # Terminate all subscriptions
        for sub_id in list(self.subscriptions.keys()):
            self.terminate_subscription(sub_id)

        # Stop notification listener
        self.stop_notification_listener()

        # Close RESTCONF session
        self.restconf.close()


def create_yang_push_tester(base_url: str, username: str, password: str,
                            timeout: int = 30) -> YANGPushTester:
    """Factory function to create YANG Push tester"""
    return YANGPushTester(
        base_url=base_url,
        username=username,
        password=password,
        timeout=timeout
    )
