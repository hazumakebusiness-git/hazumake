import json
import logging
from decimal import Decimal

import razorpay
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

from hazu.smile_api import create_order as smile_create_order
from products.models import Product
from wallet.models import Transaction
from .models import Order


@login_required
def orders(request):
    orders_list = request.user.orders.all().order_by('-created_at')
    paginator = Paginator(orders_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'orders/orders.html', {
        'orders': page_obj,
        'page_obj': page_obj,
    })


@login_required
@require_POST
def place_order(request):
    if request.content_type == 'application/json':
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return HttpResponseBadRequest('Invalid JSON body.')
    else:
        payload = request.POST

    product_id = payload.get('product_id')
    payment_method = payload.get('payment_method')

    try:
        quantity = int(payload.get('quantity', 1))
        if quantity < 1:
            return HttpResponseBadRequest('Invalid quantity.')
    except (ValueError, TypeError):
        return HttpResponseBadRequest('quantity must be a valid integer.')

    product = get_object_or_404(Product, pk=product_id, is_active=True)
    total_coins = product.price_coins * quantity
    total_inr = product.price_inr * quantity

    # Collect player_fields__ prefixed keys from JSON or POST data
    player_fields = {}
    for key, value in payload.items():
        if key.startswith('player_fields__'):
            field_name = key.replace('player_fields__', '')
            player_fields[field_name] = str(value).strip()

    # Validate required checkout fields
    game = product.game
    if game:
        for field_spec in game.checkout_fields:
            if field_spec.get('required') and not player_fields.get(field_spec['name']):
                messages.error(request, f"{field_spec['label']} is required.")
                return redirect('product_detail', pk=product.id)

    # ─── WALLET PAYMENT ───────────────────────────────────────────
    if payment_method == 'WALLET':
        wallet = request.user.wallet

        if wallet.balance < total_inr:
            messages.error(request, 'Insufficient wallet balance.')
            return redirect(request.META.get('HTTP_REFERER', '/shop/'))

        wallet.balance = wallet.balance - total_inr
        wallet.save()

        Transaction.objects.create(
            wallet=wallet,
            type='DEBIT',
            amount=total_inr,
            balance_after=wallet.balance,
            note=f'Purchase: {product.name} x{quantity}',
        )

        player_uid = (
            player_fields.get('uid') or
            player_fields.get('player_id') or
            player_fields.get('user_id') or
            next(iter(player_fields.values()), '')
        )
        player_sid = (
            player_fields.get('sid') or
            player_fields.get('zone_id') or
            player_fields.get('server_id') or
            ''
        )

        logger.info("player_fields keys: %s", list(player_fields.keys()))
        logger.info("player_uid resolved: %s | player_sid: %s", player_uid, player_sid)

        order = Order.objects.create(
            user=request.user,
            product=product,
            game=game,
            quantity=quantity,
            player_uid=player_uid,
            player_sid=player_sid,
            player_fields=player_fields,
            total_coins=total_coins,
            total_inr=total_inr,
            payment_method='WALLET',
            payment_status='PAID',
            status='PROCESSING',
        )

        game_slug = (game.supplier_game_code or game.slug or '') if game else ''
        game_slug = game_slug.replace(' ', '').replace('-', '').lower()
        smile_order_id = smile_create_order(
            game_slug=game_slug,
            product_id=product.smile_product_id,
            player_uid=player_uid,
            player_sid=player_sid,
        )

        if smile_order_id:
            order.smile_order_id = smile_order_id
            order.status = 'COMPLETED'
            order.save()
            messages.success(request, f'✅ {product.name} delivered! Order ID: {smile_order_id}')
        else:
            order.status = 'FAILED'
            order.notes = 'Smile.one fulfillment failed.'
            order.save()
            messages.error(request, '⚠️ Payment deducted but delivery failed. Contact support with your order ID.')

        return redirect('orders')

    # ─── RAZORPAY PAYMENT ─────────────────────────────────────────
    if payment_method == 'RAZORPAY':
        try:
            amount_paise = int(total_inr * Decimal('100'))
        except Exception:
            return HttpResponseBadRequest('Invalid amount value.')

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        razorpay_order = client.order.create({
            'amount': amount_paise,
            'currency': 'INR',
            'payment_capture': 1,
        })

        request.session['pending_razorpay'] = {
            'product_id': str(product.id),
            'player_fields': player_fields,
            'quantity': quantity,
            'total_coins': total_coins,
            'total_inr': str(total_inr),
            'razorpay_order_id': razorpay_order['id'],
        }

        return JsonResponse({
            'razorpay_order_id': razorpay_order['id'],
            'amount_paise': razorpay_order['amount'],
            'key_id': settings.RAZORPAY_KEY_ID,
        })

    return HttpResponseBadRequest('Invalid payment method.')


@login_required
@require_POST
def razorpay_order_success(request):
    session_data = request.session.get('pending_razorpay')
    if not session_data:
        messages.error(request, 'Payment session expired. Please try again.')
        return redirect('orders')

    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_order_id = request.POST.get('razorpay_order_id')
    razorpay_signature = request.POST.get('razorpay_signature')

    if not (razorpay_payment_id and razorpay_order_id and razorpay_signature):
        messages.error(request, 'Payment verification failed.')
        return redirect('orders')

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature,
        })
    except razorpay.errors.SignatureVerificationError:
        messages.error(request, 'Payment verification failed.')
        return redirect('orders')

    product = get_object_or_404(Product, pk=session_data['product_id'])
    quantity = int(session_data['quantity'])
    total_coins = int(session_data['total_coins'])
    total_inr = Decimal(session_data['total_inr'])
    player_fields = session_data['player_fields']

    player_uid = (
        player_fields.get('uid') or
        player_fields.get('player_id') or
        player_fields.get('user_id') or
        next(iter(player_fields.values()), '')
    )
    player_sid = (
        player_fields.get('sid') or
        player_fields.get('zone_id') or
        player_fields.get('server_id') or
        ''
    )

    logger.info("player_fields keys: %s", list(player_fields.keys()))
    logger.info("player_uid resolved: %s | player_sid: %s", player_uid, player_sid)

    order = Order.objects.create(
        user=request.user,
        product=product,
        game=product.game,
        quantity=quantity,
        player_uid=player_uid,
        player_sid=player_sid,
        player_fields=player_fields,
        total_coins=total_coins,
        total_inr=total_inr,
        payment_method='RAZORPAY',
        payment_status='PAID',
        status='PROCESSING',
    )

    game = product.game
    game_slug = (game.supplier_game_code or game.slug or '') if game else ''
    game_slug = game_slug.replace(' ', '').replace('-', '').lower()
    smile_order_id = smile_create_order(
        game_slug=game_slug,
        product_id=product.smile_product_id,
        player_uid=player_uid,
        player_sid=player_sid,
    )

    if smile_order_id:
        order.smile_order_id = smile_order_id
        order.status = 'COMPLETED'
        order.save()
        messages.success(request, f'✅ {product.name} delivered! Order ID: {smile_order_id}')
    else:
        order.status = 'FAILED'
        order.notes = 'Smile.one fulfillment failed.'
        order.save()
        messages.error(request, '⚠️ Payment received but delivery failed. Contact support.')

    request.session.pop('pending_razorpay', None)
    return redirect('orders')


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, id=pk, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})