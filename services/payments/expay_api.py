"""
services/payments/expay_api.py
ExPay payment gateway client — replaces KhilaadiXPro/Razorpay.

Configuration required in settings.py:
    EXPAY_USER_TOKEN     = os.getenv('EXPAY_USER_TOKEN')
    EXPAY_WEBHOOK_SECRET = os.getenv('EXPAY_WEBHOOK_SECRET')
    EXPAY_REDIRECT_URL   = os.getenv('EXPAY_REDIRECT_URL', 'https://hazumakestore.com/payment/return/')
"""

import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://exgateway2.in/api"
TIMEOUT = 15


class ExPayError(Exception):
    """ExPay API error with optional raw response data."""
    
    def __init__(self, message, raw=None):
        super().__init__(message)
        self.raw = raw or {}


class ExPayAPI:
    """
    ExPay payment gateway client.
    
    Provides methods to create orders, check payment status, and handle webhooks.
    """

    def __init__(self):
        """Initialize with credentials from Django settings."""
        self.user_token = settings.EXPAY_USER_TOKEN
        self.webhook_secret = settings.EXPAY_WEBHOOK_SECRET
        self.redirect_url = getattr(
            settings, "EXPAY_REDIRECT_URL", "https://hazumakestore.com/payment/return/"
        )

    def _post(self, endpoint, payload):
        """
        Make a POST request to ExPay API endpoint.
        
        Args:
            endpoint: API endpoint (e.g., "create-order")
            payload: Dictionary of form data
            
        Returns:
            Parsed JSON response
            
        Raises:
            ExPayError: If request fails or response indicates error
        """
        url = f"{BASE_URL}/{endpoint}"
        try:
            resp = requests.post(
                url,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
        except requests.exceptions.Timeout:
            logger.error("ExPay request timeout to %s", endpoint)
            raise ExPayError("ExPay request timed out")
        except requests.exceptions.RequestException as exc:
            logger.error("ExPay HTTP error to %s: %s", endpoint, exc)
    # Get the actual error response from gateway
            if hasattr(exc, 'response') and exc.response is not None:
                logger.error("ExPay response body: %s", exc.response.text)
                raise ExPayError(f"HTTP error: {exc} | Gateway says: {exc.response.text}")
            raise ExPayError(f"HTTP error: {exc}")

        try:
            data = resp.json()
        except ValueError as exc:
            logger.error("ExPay non-JSON response from %s: %s", endpoint, resp.text[:300])
            raise ExPayError(f"Non-JSON response: {resp.text[:300]}")

        if not data.get("status"):
            error_msg = data.get("message", "ExPay error")
            logger.error("ExPay API error in %s: %s", endpoint, error_msg)
            raise ExPayError(error_msg, raw=data)

        return data

    def create_order(self, customer_mobile, amount, order_id, remark1="", remark2=""):
        """
        Create a payment order with ExPay.
        
        Args:
            customer_mobile: Customer phone number
            amount: Payment amount (in INR)
            order_id: Unique order ID from your system
            remark1: Optional remark field 1
            remark2: Optional remark field 2
            
        Returns:
            Dict with keys:
                - orderId: ExPay's order ID (use this for status checks)
                - payment_url: Hosted payment page URL for customer redirect
                
        Raises:
            ExPayError: If API call fails
            
        Note:
            Order automatically fails if not paid within 30 minutes.
        """
        payload = {
            "customer_mobile": str(customer_mobile),
            "user_token": self.user_token,
            "amount": str(amount),
            "order_id": str(order_id),
            "redirect_url": self.redirect_url,
            "remark1": str(remark1),
            "remark2": str(remark2),
        }
        data = self._post("create-order", payload)
        return data["result"]

    def check_order_status(self, order_id):
        """
        Check the payment status of an order.
        
        Args:
            order_id: Your system's order ID (not ExPay's orderId)
            
        Returns:
            Dict with keys:
                - txnStatus: "SUCCESS", "FAILED", "PENDING", or "NOT_FOUND"
                - orderId: ExPay's order ID
                - amount: Amount charged
                - date: Transaction date
                - utr: UTR (Unique Transaction Reference) if successful
                - remark1, remark2: Your remark fields
                
        Raises:
            ExPayError: If API call fails
        """
        payload = {
            "user_token": self.user_token,
            "order_id": str(order_id),
        }
        data = self._post("check-order-status", payload)
        return data.get("result", {})


_client = None


def get_client():
    """Get or create the global ExPayAPI client instance."""
    global _client
    if _client is None:
        _client = ExPayAPI()
    return _client
