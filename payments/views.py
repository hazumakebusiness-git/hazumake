"""
payments/views.py
ExPay webhook receiver — verifies HMAC-SHA256 signature, updates Order status.

Webhook specification:
    URL: POST /api/wallet/webhook/
    
    ExPay sends these headers:
        Content-Type: application/json
        X-ExPay-Event: (e.g., "PAYMENT_SUCCESS")
        X-ExPay-Timestamp: (seconds since epoch)
        X-ExPay-Signature: t=<timestamp>, v1=<hmac_hex>
        X-ExPay-Delivery: (delivery ID)
        
    Body (JSON):
        {
            "event": "PAYMENT_SUCCESS",
            "orderId": "12345",
            "user_token": "...",
            "status": "SUCCESS|FAILED|PENDING|NOT_FOUND",
            "amount": "1.00",
            "utr": "1234567890",
            "date": "2025-09-05 01:23:45",
            "remark1": "sample",
            "remark2": "sample2"
        }
"""

import hmac
import hashlib
import json
import logging

from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from orders.models import Order
from wallet.models import Wallet, Transaction

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class ExPayWebhookView(View):
    """
    Django webhook receiver for ExPay payment notifications.
    
    - Verifies HMAC-SHA256 signature from ExPay
    - Updates Order status based on payment result
    - Credits wallet on success
    - Always responds HTTP 200 to acknowledge receipt
    """

    def post(self, request):
        """
        Handle ExPay webhook POST request.
        
        Returns:
            JSON response with status "ok" and HTTP 200
            (Always returns 200 to acknowledge receipt to ExPay)
        """
        raw_body = request.body
        sig_header = request.headers.get("X-ExPay-Signature", "")
        timestamp = request.headers.get("X-ExPay-Timestamp", "")

        # Verify signature
        if not self._verify_signature(raw_body, timestamp, sig_header):
            logger.warning(
                "ExPay webhook: signature mismatch. Expected v1=%s",
                sig_header,
            )
            # Still return 200 — ExPay just needs acknowledgment
            return JsonResponse({"status": "ok"}, status=200)

        # Parse JSON body
        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError:
            logger.error("ExPay webhook: invalid JSON body")
            return JsonResponse({"status": "ok"}, status=200)

        # Extract fields
        event = data.get("event")
        order_id = data.get("orderId")
        status = data.get("status")
        utr = data.get("utr", "")
        amount = data.get("amount", "0")

        logger.info(
            "ExPay webhook event=%s order=%s status=%s utr=%s",
            event,
            order_id,
            status,
            utr,
        )

        # Find the Order — use smile_order_id as the lookup key
        try:
            order = Order.objects.get(smile_order_id=order_id)
        except Order.DoesNotExist:
            logger.warning("ExPay webhook: unknown order_id %s", order_id)
            return JsonResponse({"status": "ok"}, status=200)

        # Handle payment success
        if event == "PAYMENT_SUCCESS" and status == "SUCCESS":
            try:
                self._mark_order_completed(order, utr, amount)
            except Exception as exc:
                logger.exception("Error marking order %s completed: %s", order_id, exc)
                return JsonResponse({"status": "ok"}, status=200)

        # Handle payment failure
        elif status in ("FAILED", "CANCELLED"):
            try:
                order.status = "FAILED"
                order.save()
                logger.info("Order %s marked FAILED: %s (utr=%s)", order_id, status, utr)
            except Exception as exc:
                logger.exception("Error marking order %s failed: %s", order_id, exc)

        # PENDING → leave as is, will be polled or webhook'd again

        return JsonResponse({"status": "ok"}, status=200)

    @staticmethod
    def _verify_signature(raw_body, timestamp, sig_header):
        """
        Verify HMAC-SHA256 signature from ExPay.
        
        Signature format in header: "t=<timestamp>, v1=<hmac_hex>"
        
        signed_payload = f"{timestamp}.{raw_body}"
        expected = hmac_sha256(EXPAY_WEBHOOK_SECRET, signed_payload)
        
        Args:
            raw_body: Raw request body (bytes)
            timestamp: X-ExPay-Timestamp header
            sig_header: X-ExPay-Signature header
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not sig_header or not timestamp:
            logger.warning("ExPay webhook: missing signature or timestamp header")
            return False

        # Parse signature header: "t=<ts>, v1=<hex>"
        parts = {}
        for part in sig_header.split(","):
            if "=" in part:
                key, value = part.split("=", 1)
                parts[key.strip()] = value.strip()

        v1 = parts.get("v1")
        if not v1:
            logger.warning("ExPay webhook: missing v1 in signature header")
            return False

        # Construct signed payload
        try:
            body_str = raw_body.decode("utf-8")
        except UnicodeDecodeError:
            logger.warning("ExPay webhook: could not decode body as UTF-8")
            return False

        signed_payload = f"{timestamp}.{body_str}"

        # Compute expected signature
        expected = hmac.new(
            settings.EXPAY_WEBHOOK_SECRET.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Compare using constant-time comparison
        result = hmac.compare_digest(expected, v1)
        if not result:
            logger.warning(
                "ExPay webhook: signature mismatch. Expected=%s, Got=%s",
                expected,
                v1,
            )
        return result

    @staticmethod
    def _mark_order_completed(order, utr, amount):
        """
        Mark order as completed and credit user's wallet.
        
        Args:
            order: Order instance
            utr: ExPay UTR (Unique Transaction Reference)
            amount: Amount transacted
        """
        order.status = "COMPLETED"
        order.save()

        # Credit wallet with order amount (usually coins)
        wallet = order.user.wallet
        try:
            # Assuming order.smile_product_id or similar indicates the amount in coins
            # Adjust based on your Order model structure
            coin_amount = order.quantity  # or however you store the coin count

            wallet.balance += coin_amount
            wallet.save()

            # Record transaction
            Transaction.objects.create(
                wallet=wallet,
                type="CREDIT",
                amount=coin_amount,
                balance_after=wallet.balance,
                note=f"Order completed via ExPay (UTR: {utr})",
            )

            logger.info(
                "Order %s completed. User %s credited with %s coins (UTR: %s)",
                order.id,
                order.user.email,
                coin_amount,
                utr,
            )
        except Exception as exc:
            logger.error(
                "Error crediting wallet for order %s: %s",
                order.id,
                exc,
            )
            raise
