from decimal import Decimal

from django.conf import settings
from django.db import migrations


def create_mobilelegends_products(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Game = apps.get_model('products', 'Game')

    try:
        game = Game.objects.get(slug='mobilelegends')
    except Game.DoesNotExist:
        return

    Product.objects.filter(game=game).update(is_active=False)

    products = [
        {'name': '55 Diamonds', 'smile_product_id': '22590', 'price_brl': 4.00, 'price_coins': 400, 'type': 'DIAMOND', 'diamond_amount': 55},
        {'name': '78+8 Diamonds', 'smile_product_id': '13', 'price_brl': 6.25, 'price_coins': 625, 'type': 'DIAMOND', 'diamond_amount': 86},
        {'name': '156+16 Diamonds', 'smile_product_id': '23', 'price_brl': 12.50, 'price_coins': 1250, 'type': 'DIAMOND', 'diamond_amount': 172},
        {'name': '165 Diamonds', 'smile_product_id': '22591', 'price_brl': 11.99, 'price_coins': 1199, 'type': 'DIAMOND', 'diamond_amount': 165},
        {'name': '234+23 Diamonds', 'smile_product_id': '25', 'price_brl': 18.67, 'price_coins': 1867, 'type': 'DIAMOND', 'diamond_amount': 257},
        {'name': '275 Diamonds', 'smile_product_id': '22592', 'price_brl': 19.75, 'price_coins': 1975, 'type': 'DIAMOND', 'diamond_amount': 275},
        {'name': '565 Diamonds', 'smile_product_id': '22593', 'price_brl': 40.50, 'price_coins': 4050, 'type': 'DIAMOND', 'diamond_amount': 565},
        {'name': '625+81 Diamonds', 'smile_product_id': '26', 'price_brl': 50.00, 'price_coins': 5000, 'type': 'DIAMOND', 'diamond_amount': 706},
        {'name': '1860+335 Diamonds', 'smile_product_id': '27', 'price_brl': 150.00, 'price_coins': 15000, 'type': 'DIAMOND', 'diamond_amount': 2195},
        {'name': '3099+589 Diamonds', 'smile_product_id': '28', 'price_brl': 250.00, 'price_coins': 25000, 'type': 'DIAMOND', 'diamond_amount': 3688},
        {'name': '4649+883 Diamonds', 'smile_product_id': '29', 'price_brl': 375.00, 'price_coins': 37500, 'type': 'DIAMOND', 'diamond_amount': 5532},
        {'name': '7740+1548 Diamonds', 'smile_product_id': '30', 'price_brl': 625.00, 'price_coins': 62500, 'type': 'DIAMOND', 'diamond_amount': 9288},
        {'name': 'Weekly Elite Bundle', 'smile_product_id': '26555', 'price_brl': 4.00, 'price_coins': 400, 'type': 'BUNDLE', 'diamond_amount': None},
        {'name': 'Monthly Epic Bundle', 'smile_product_id': '26556', 'price_brl': 19.75, 'price_coins': 1975, 'type': 'BUNDLE', 'diamond_amount': None},
        {'name': 'Twilight Pass', 'smile_product_id': '33', 'price_brl': 41.25, 'price_coins': 4125, 'type': 'STARLIGHT', 'diamond_amount': None},
        {'name': 'Weekly Diamond Pass', 'smile_product_id': '16642', 'price_brl': 8.00, 'price_coins': 800, 'type': 'STARLIGHT', 'diamond_amount': None},
    ]

    for p in products:
        price_inr = (
            Decimal(str(p['price_brl'])) * Decimal(str(settings.SMILE_BRL_TO_INR))
        ).quantize(Decimal('0.01'))

        Product.objects.update_or_create(
            game=game,
            smile_product_id=p['smile_product_id'],
            defaults={
                'name': p['name'],
                'type': p['type'],
                'diamond_amount': p['diamond_amount'],
                'price_brl': p['price_brl'],
                'price_coins': p['price_coins'],
                'price_inr': price_inr,
                'is_active': True,
            },
        )


def delete_mobilelegends_products(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.filter(game__slug='mobilelegends').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0006_seed_smile_games_products'),
    ]

    operations = [
        migrations.RunPython(create_mobilelegends_products, delete_mobilelegends_products),
    ]
