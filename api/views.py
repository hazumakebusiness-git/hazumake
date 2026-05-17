import json
import logging
import urllib.error
import urllib.request
from datetime import timedelta
try:
    import razorpay
except ImportError:
    razorpay = None
from django.conf import settings
from django.db import transaction as db_transaction
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from products.models import Product, Game
from orders.models import Order
from wallet.models import Wallet, Transaction
from accounts.models import CustomUser, OTPCode
from accounts.otp_utils import (
    build_username_from_identifier, generate_otp,
    send_email_otp, send_sms_otp,
)
from hazu.smile_api import create_order as smile_create_order
from .serializers import (
    ProductSerializer, GameSerializer, WalletSerializer,
    OrderSerializer, RegisterSerializer, TransactionSerializer
)

logger = logging.getLogger(__name__)


# ─── AUTH ─────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    user = serializer.save()
    refresh = RefreshToken.for_user(user)
    return Response({
        'user_id': str(user.id),
        'username': user.username,
        'email': user.email,
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    email = request.data.get('email', '').strip().lower()
    password = request.data.get('password', '')

    if not email or not password:
        return Response(
            {'error': 'Email and password are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return Response(
            {'error': 'Invalid credentials.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.check_password(password):
        return Response(
            {'error': 'Invalid credentials.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        return Response(
            {'error': 'Account is disabled.'},
            status=status.HTTP_403_FORBIDDEN
        )

    refresh = RefreshToken.for_user(user)
    return Response({
        'user_id': str(user.id),
        'username': user.username,
        'email': user.email,
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
    access_token = (request.data.get('access_token') or '').strip()
    if not access_token:
        return Response(
            {'error': 'access_token is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    userinfo_url = 'https://www.googleapis.com/oauth2/v3/userinfo'
    req = urllib.request.Request(
        userinfo_url,
        headers={
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError:
        return Response(
            {'error': 'Invalid Google access token.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception:
        logger.exception('Google token verification failed')
        return Response(
            {'error': 'Failed to verify Google token.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    email = (payload.get('email') or '').strip().lower()
    if not email:
        return Response(
            {'error': 'Google user email is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    first_name = payload.get('given_name', '')
    last_name = payload.get('family_name', '')
    username = email

    user, created = CustomUser.objects.get_or_create(
        email=email,
        defaults={
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'is_active': True,
            'is_email_verified': True,
        }
    )

    if not created and not user.is_active:
        return Response(
            {'error': 'Account is disabled.'},
            status=status.HTTP_403_FORBIDDEN
        )

    if created:
        user.set_unusable_password()
        user.save()

    refresh = RefreshToken.for_user(user)
    return Response({
        'user_id': str(user.id),
        'username': user.username,
        'email': user.email,
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    })


def _is_email_identifier(identifier: str) -> bool:
    return '@' in identifier


def _is_phone_identifier(identifier: str) -> bool:
    return identifier.startswith('+')


def _resolve_user_by_identifier(identifier: str):
    if _is_email_identifier(identifier):
        return CustomUser.objects.filter(email__iexact=identifier.strip().lower()).first()
    if _is_phone_identifier(identifier):
        return CustomUser.objects.filter(phone=identifier.strip()).first()
    return None


def _create_new_user(identifier: str):
    identifier = identifier.strip()
    if _is_email_identifier(identifier):
        email = identifier.lower()
        username = build_username_from_identifier(email)
        if CustomUser.objects.filter(username=username).exists():
            username = f'{username}_{get_random_string(6)}'
        user = CustomUser.objects.create(
            email=email,
            username=username,
            is_active=True,
            is_email_verified=True,
        )
    else:
        phone = identifier
        email = f'{phone}@phone.hazumake'
        username = build_username_from_identifier(phone)
        if CustomUser.objects.filter(username=username).exists():
            username = f'{username}_{get_random_string(6)}'
        user = CustomUser.objects.create(
            email=email,
            username=username,
            phone=phone,
            is_active=True,
            is_email_verified=False,
        )
    user.set_unusable_password()
    user.save()
    return user


@api_view(['POST'])
@permission_classes([AllowAny])
def otp_request(request):
    identifier = (request.data.get('identifier') or '').strip()
    if not identifier:
        return Response(
            {'error': 'identifier is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not (_is_email_identifier(identifier) or _is_phone_identifier(identifier)):
        return Response(
            {'error': 'identifier must be an email or phone number starting with +.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    identifier = identifier.strip()
    now = timezone.now()
    active_otp = OTPCode.objects.filter(
        identifier=identifier,
        is_used=False,
        expires_at__gt=now,
    ).order_by('-created_at').first()

    if active_otp and (now - active_otp.created_at).total_seconds() < 60:
        return Response(
            {'error': 'OTP was recently sent. Please wait before requesting again.'},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    with db_transaction.atomic():
        OTPCode.objects.filter(identifier=identifier, is_used=False).update(is_used=True)
        code = generate_otp()
        user = _resolve_user_by_identifier(identifier)
        otp = OTPCode.objects.create(
            user=user,
            identifier=identifier,
            code=code,
            expires_at=now + timedelta(minutes=10),
        )

    try:
        if _is_email_identifier(identifier):
            send_email_otp(identifier, code)
            method = 'email'
        else:
            send_sms_otp(identifier, code)
            method = 'sms'
    except Exception as exc:
        logger.exception('OTP delivery failed')
        return Response(
            {'error': str(exc)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response({'message': 'OTP sent', 'method': method})


@api_view(['POST'])
@permission_classes([AllowAny])
def otp_verify(request):
    identifier = (request.data.get('identifier') or '').strip()
    code = (request.data.get('code') or '').strip()
    if not identifier or not code:
        return Response(
            {'error': 'identifier and code are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    now = timezone.now()
    otp = OTPCode.objects.filter(
        identifier=identifier,
        code=code,
        is_used=False,
        expires_at__gt=now,
    ).order_by('-created_at').first()

    if not otp:
        return Response(
            {'error': 'Invalid or expired OTP.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    with db_transaction.atomic():
        otp.is_used = True
        otp.save(update_fields=['is_used'])

        user = otp.user or _resolve_user_by_identifier(identifier)
        created = False
        if not user:
            user = _create_new_user(identifier)
            created = True

    if not user.is_active:
        return Response(
            {'error': 'Account is disabled.'},
            status=status.HTTP_403_FORBIDDEN
        )

    refresh = RefreshToken.for_user(user)
    payload = {
        'user_id': str(user.id),
        'username': user.username,
        'email': user.email,
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }
    if created:
        payload['is_new_user'] = True

    return Response(payload)


# ─── PRODUCTS ─────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def product_list(request):
    products = Product.objects.filter(is_active=True).select_related('game')
    game_slug = request.query_params.get('game')
    product_type = request.query_params.get('type')

    if game_slug:
        products = products.filter(game__slug=game_slug)
    if product_type:
        products = products.filter(type=product_type)

    products = products.order_by('price_coins')
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def product_detail(request, pk):
    try:
        product = Product.objects.select_related('game').get(
            pk=pk, is_active=True
        )
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    serializer = ProductSerializer(product)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def game_list(request):
    games = Game.objects.filter(is_active=True).order_by('sort_order')
    serializer = GameSerializer(games, many=True)
    return Response(serializer.data)


# ─── WALLET ───────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def wallet_detail(request):
    try:
        wallet = request.user.wallet
    except Wallet.DoesNotExist:
        return Response(
            {'error': 'Wallet not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    serializer = WalletSerializer(wallet)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def wallet_topup_initiate(request):
    amount_str = request.data.get('amount_inr')

    if not amount_str:
        return Response(
            {'error': 'amount_inr is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        amount = float(amount_str)
        if amount < 10:
            raise ValueError
    except (ValueError, TypeError):
        return Response(
            {'error': 'Minimum top-up amount is ₹10.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if razorpay is None:
        return Response(
            {'error': 'Payment gateway library is not installed.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        return Response(
            {'error': 'Payment gateway not configured.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    try:
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        order = client.order.create({
            'amount': int(amount * 100),
            'currency': 'INR',
            'payment_capture': 1,
        })
        return Response({
            'order_id': order['id'],
            'amount_paise': order['amount'],
            'key_id': settings.RAZORPAY_KEY_ID,
        })
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def wallet_topup_verify(request):
    razorpay_payment_id = request.data.get('razorpay_payment_id')
    razorpay_order_id = request.data.get('razorpay_order_id')
    razorpay_signature = request.data.get('razorpay_signature')

    if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
        return Response(
            {'error': 'All three Razorpay fields are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if razorpay is None:
        return Response(
            {'error': 'Payment gateway library is not installed.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    try:
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature,
        })
    except razorpay.errors.SignatureVerificationError:
        return Response(
            {'error': 'Payment verification failed. Signature mismatch.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        payment = client.payment.fetch(razorpay_payment_id)
        amount_inr = payment['amount'] / 100
    except Exception as e:
        return Response(
            {'error': f'Could not fetch payment details: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # BUG 4: Check for replay attack - verify payment hasn't been processed already
    if Transaction.objects.filter(razorpay_payment_id=razorpay_payment_id).exists():
        return Response(
            {'error': 'Payment already processed.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    with db_transaction.atomic():
        wallet = request.user.wallet
        wallet.balance += amount_inr
        wallet.save()
        Transaction.objects.create(
            wallet=wallet,
            type='CREDIT',
            amount=amount_inr,
            balance_after=wallet.balance,
            note=f'Wallet top-up via Razorpay ({razorpay_payment_id})',
            razorpay_payment_id=razorpay_payment_id,
        )

    return Response({
        'message': f'₹{amount_inr:.0f} added to your wallet.',
        'new_balance': float(wallet.balance),
    })


# ─── ORDERS ───────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def order_list_create(request):

    if request.method == 'GET':
        orders = Order.objects.filter(
            user=request.user
        ).select_related('product', 'game').order_by('-created_at')

        page_size = 20
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        total = orders.count()
        serializer = OrderSerializer(orders[start:end], many=True)
        return Response({
            'count': total,
            'page': page,
            'total_pages': (total + page_size - 1) // page_size,
            'results': serializer.data,
        })

    if request.method == 'POST':
        product_id = request.data.get('product_id')
        player_fields = request.data.get('player_fields', {})
        player_uid = (request.data.get('player_uid') or '').strip()
        player_sid = (request.data.get('player_sid') or '').strip()
        
        # BUG 3: Add quantity validation with error handling
        try:
            quantity = int(request.data.get('quantity', 1))
        except (ValueError, TypeError):
            return Response(
                {'error': 'quantity must be a valid integer.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if quantity < 1:
            return Response(
                {'error': 'quantity must be at least 1.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not player_uid:
            return Response(
                {'error': 'player_uid is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment_method = request.data.get('payment_method', 'WALLET')

        if not product_id:
            return Response(
                {'error': 'product_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product = Product.objects.select_related('game').get(
                pk=product_id, is_active=True
            )
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validate player_fields against game checkout_fields
        game = product.game
        if game:
            for field_spec in game.checkout_fields:
                if field_spec.get('required'):
                    if not player_fields.get(field_spec['name']):
                        return Response(
                            {'error': f"{field_spec['label']} is required."},
                            status=status.HTTP_400_BAD_REQUEST
                        )

        total_coins = product.price_coins * quantity
        total_inr = product.price_inr * quantity

        if payment_method == 'WALLET':
            wallet = request.user.wallet
            if wallet.balance < total_inr:
                return Response(
                    {'error': 'Insufficient wallet balance.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            with db_transaction.atomic():
                wallet.balance -= total_inr
                wallet.save()
                Transaction.objects.create(
                    wallet=wallet,
                    type='DEBIT',
                    amount=total_inr,
                    balance_after=wallet.balance,
                    note=f'Purchase: {product.name} x{quantity}',
                )
                order = Order.objects.create(
                    user=request.user,
                    product=product,
                    game=game,
                    player_uid=player_uid,
                    player_sid=player_sid,
                    player_fields=player_fields,
                    quantity=quantity,
                    total_coins=total_coins,
                    total_inr=total_inr,
                    payment_method='WALLET',
                    payment_status='PAID',
                    status='PROCESSING',
                )
                smile_create_order(
                    game.slug if game else '',
                    product.smile_product_id,
                    player_uid,
                    player_sid,
                )

            serializer = OrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif payment_method == 'GATEWAY':
            with db_transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    product=product,
                    game=game,
                    player_uid=player_uid,
                    player_sid=player_sid,
                    player_fields=player_fields,
                    quantity=quantity,
                    total_coins=total_coins,
                    total_inr=total_inr,
                    payment_method='GATEWAY',
                    payment_status='UNPAID',
                    status='PENDING',
                )

            return Response({'order_id': str(order.id)}, status=status.HTTP_201_CREATED)

        return Response(
            {'error': 'Invalid payment_method. Use WALLET or GATEWAY.'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail(request, pk):
    try:
        order = Order.objects.select_related(
            'product', 'game'
        ).get(pk=pk, user=request.user)
    except Order.DoesNotExist:
        return Response(
            {'error': 'Order not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    serializer = OrderSerializer(order)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def order_razorpay_verify(request):
    return Response(
        {'error': 'Gateway order verification is not available in this deployment.'},
        status=status.HTTP_501_NOT_IMPLEMENTED
    )