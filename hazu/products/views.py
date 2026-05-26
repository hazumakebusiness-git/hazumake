import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q
from django.views.decorators.http import require_POST
from .models import Product, Game
from hazu.smile_api import verify_player
import logging
logger = logging.getLogger(__name__)

def home(request):
    featured_games = Game.objects.filter(
        is_active=True,
        is_featured=True
    ).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    ).order_by('sort_order')[:6]

    latest_products = Product.objects.filter(
        is_active=True
    ).order_by('-created_at')[:3]

    return render(request, 'home.html', {
        'featured_games': featured_games,
        'latest_products': latest_products,
    })

def shop(request):
    # Main shop — shows game selection grid
    games = Game.objects.filter(is_active=True).prefetch_related('products')
    # Annotate with active product count
    games = games.annotate(product_count=Count('products', filter=Q(products__is_active=True)))
    return render(request, 'products/shop.html', {'games': games})

def game_shop(request, game_slug):
    game = get_object_or_404(Game, slug=game_slug, is_active=True)
    product_type = request.GET.get('type')
    products = Product.objects.filter(game=game, is_active=True).order_by('price_coins')
    if product_type:
        products = products.filter(type=product_type)
    available_types = Product.objects.filter(game=game, is_active=True).values_list('type', flat=True).distinct()
    return render(request, 'products/game_shop.html', {
        'game': game,
        'products': products,
        'available_types': available_types,
        'active_type': product_type,
    })

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    wallet = None
    if request.user.is_authenticated:
        wallet = request.user.wallet
    # Determine supplier game slug; prefer supplier_game_code but sanitize
    # (remove spaces and lowercase) so external APIs like Smile.one receive
    # the expected identifier (e.g. "mobilelegends").
    raw_game_slug = ''
    if product.game:
        raw_game_slug = product.game.supplier_game_code or product.game.slug or ''
    game_slug = raw_game_slug.replace(' ', '').replace('-', '').lower()

    return render(request, 'products/product_detail.html', {
        'product': product,
        'game': product.game,
        'checkout_fields': product.game.checkout_fields if product.game else [],
        'game_slug': game_slug,
        'wallet': wallet,
    })


@login_required
@require_POST
def verify_player_view(request, slug):
    game = get_object_or_404(Game, slug=slug, is_active=True)

    try:
        body = json.loads(request.body)
        player_uid = str(body.get('uid') or body.get('userid', '')).strip()
        player_sid = str(body.get('sid') or body.get('zoneid', '')).strip()
        product_id = str(body.get('productid') or body.get('product_id', '')).strip()
    except (ValueError, AttributeError):
        return JsonResponse({'status': 400, 'message': 'Invalid JSON'}, status=400)

    if not player_uid or not product_id:
        return JsonResponse({'status': 400, 'success': False, 'message': 'uid and productid are required'}, status=400)

    from hazu.smile_api import verify_player
    game_slug = game.supplier_game_code or game.slug
    print('VERIFY PLAYER VIEW CALL', {'slug': slug, 'game_slug': game_slug, 'uid': player_uid, 'sid': player_sid, 'productid': product_id})
    username = verify_player(
        game_slug=game_slug,
        product_id=product_id,
        player_uid=player_uid,
        player_sid=player_sid,
    )
    print('VERIFY PLAYER VIEW RESULT', {'username': username})
    logger.info("getrole raw: %s", username)

    if username:
        return JsonResponse({
            'status': 200,
            'success': True,
            'nickname': username,
            'uid': player_uid,
            'zone': player_sid,
        })
    return JsonResponse({'status': 400, 'success': False, 'message': 'Verification failed. Try again.'}, status=400)