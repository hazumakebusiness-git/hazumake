from decimal import Decimal
from django.db import migrations


def create_smile_games_and_products(apps, schema_editor):
    Game = apps.get_model('products', 'Game')
    Product = apps.get_model('products', 'Product')

    game_definitions = [
        {
            'slug': 'mobilelegends',
            'name': 'Mobile Legends: Bang Bang',
            'short_name': 'MLBB',
            'field_preset': 'MLBB',
            'checkout_fields': [
                {'name': 'player_id', 'label': 'Player ID', 'required': True},
                {'name': 'zone_id', 'label': 'Zone ID', 'required': True},
            ],
            'sort_order': 1,
        },
        {
            'slug': 'hago',
            'name': 'Hago',
            'short_name': 'HAGO',
            'field_preset': 'FREEFIRE',
            'checkout_fields': [
                {'name': 'player_id', 'label': 'Player ID', 'required': True},
            ],
            'sort_order': 2,
        },
        {
            'slug': 'honkai',
            'name': 'Honkai: Star Rail',
            'short_name': 'HONKAI',
            'field_preset': 'HONKAI',
            'checkout_fields': [
                {'name': 'player_id', 'label': 'UID', 'required': True},
                {'name': 'server', 'label': 'Server', 'required': False},
            ],
            'sort_order': 3,
        },
        {
            'slug': 'pubgmobile',
            'name': 'PUBG Mobile',
            'short_name': 'PUBG',
            'field_preset': 'BGMI',
            'checkout_fields': [
                {'name': 'player_id', 'label': 'Player ID', 'required': True},
            ],
            'sort_order': 4,
        },
        {
            'slug': 'identityv',
            'name': 'Identity V',
            'short_name': 'IDV',
            'field_preset': 'FREEFIRE',
            'checkout_fields': [
                {'name': 'player_id', 'label': 'Player ID', 'required': True},
            ],
            'sort_order': 5,
        },
    ]

    product_definitions = {
        'mobilelegends': [
            {'smile_product_id': '26148', 'name': 'Limited-Time Value Pack', 'price_brl': '1.20'},
            {'smile_product_id': '26555', 'name': 'Weekly Elite Bundle', 'price_brl': '4.00'},
            {'smile_product_id': '26556', 'name': 'Monthly Epic Bundle', 'price_brl': '19.75'},
            {'smile_product_id': '22590', 'name': '55 Diamond', 'price_brl': '4.00'},
            {'smile_product_id': '22591', 'name': '165 Diamond', 'price_brl': '11.99'},
            {'smile_product_id': '22592', 'name': '275 Diamond', 'price_brl': '19.75'},
            {'smile_product_id': '22593', 'name': '565 Diamond', 'price_brl': '40.50'},
            {'smile_product_id': '13', 'name': '78+8 Diamond', 'price_brl': '6.25'},
            {'smile_product_id': '23', 'name': '156+16 Diamond', 'price_brl': '12.50'},
            {'smile_product_id': '25', 'name': '234+23 Diamond', 'price_brl': '18.67'},
            {'smile_product_id': '26', 'name': '625+81 Diamond', 'price_brl': '50.00'},
            {'smile_product_id': '27', 'name': '1860+335 Diamond', 'price_brl': '150.00'},
            {'smile_product_id': '28', 'name': '3099+589 Diamond', 'price_brl': '250.00'},
            {'smile_product_id': '29', 'name': '4649+883 Diamond', 'price_brl': '375.00'},
            {'smile_product_id': '30', 'name': '7740+1548 Diamond', 'price_brl': '625.00'},
            {'smile_product_id': '33', 'name': 'Twilight Pass', 'price_brl': '41.25'},
            {'smile_product_id': '16642', 'name': 'Weekly Diamond Pass', 'price_brl': '8.00'},
        ],
        'hago': [
            {'smile_product_id': '164', 'name': '6,570 Diamonds', 'price_brl': '3.89'},
            {'smile_product_id': '165', 'name': '13,409 Diamonds', 'price_brl': '7.88'},
            {'smile_product_id': '166', 'name': '32,123 Diamonds', 'price_brl': '18.85'},
            {'smile_product_id': '167', 'name': '65,136 Diamonds', 'price_brl': '37.81'},
            {'smile_product_id': '168', 'name': '129,547 Diamonds', 'price_brl': '74.71'},
            {'smile_product_id': '169', 'name': '269,628 Diamonds', 'price_brl': '154.51'},
        ],
        'honkai': [
            {'smile_product_id': '18356', 'name': '60 Oneiric Shard', 'price_brl': '4.90'},
            {'smile_product_id': '18357', 'name': '300+30 Oneiric Shard', 'price_brl': '24.90'},
            {'smile_product_id': '18358', 'name': '980+110 Oneiric Shard', 'price_brl': '79.90'},
            {'smile_product_id': '18359', 'name': '1980+260 Oneiric Shard', 'price_brl': '149.90'},
            {'smile_product_id': '18360', 'name': '3280+600 Oneiric Shard', 'price_brl': '249.90'},
            {'smile_product_id': '18361', 'name': '6480+1600 Oneiric Shard', 'price_brl': '499.90'},
            {'smile_product_id': '18362', 'name': 'Express Supply Pass', 'price_brl': '24.90'},
        ],
        'pubgmobile': [
            {'smile_product_id': '617', 'name': '60 UC', 'price_brl': '4.71'},
            {'smile_product_id': '441', 'name': '300+25 UC', 'price_brl': '23.79'},
            {'smile_product_id': '442', 'name': '600+60 UC', 'price_brl': '47.58'},
            {'smile_product_id': '443', 'name': '1500+300 UC', 'price_brl': '119.05'},
            {'smile_product_id': '444', 'name': '3000+850 UC', 'price_brl': '238.19'},
            {'smile_product_id': '445', 'name': '6000+2100 UC', 'price_brl': '476.39'},
        ],
        'identityv': [
            {'smile_product_id': '26516', 'name': '60+6 Echoes', 'price_brl': '5.09'},
            {'smile_product_id': '26518', 'name': '305+30 Echoes', 'price_brl': '25.66'},
            {'smile_product_id': '26519', 'name': '690+69 Echoes', 'price_brl': '51.38'},
            {'smile_product_id': '26521', 'name': '3330+333 Echoes', 'price_brl': '257.09'},
            {'smile_product_id': '26522', 'name': '6590+659 Echoes', 'price_brl': '514.23'},
        ],
    }

    for index, game_data in enumerate(game_definitions, start=1):
        defaults = {
            'name': game_data['name'],
            'short_name': game_data['short_name'],
            'description': '',
            'field_preset': game_data['field_preset'],
            'checkout_fields': game_data['checkout_fields'],
            'is_active': True,
            'is_featured': False,
            'sort_order': game_data['sort_order'],
        }

        game = Game.objects.filter(slug=game_data['slug']).first()
        if not game:
            game = Game.objects.filter(short_name=game_data['short_name']).first()

        if game:
            for attr, value in defaults.items():
                setattr(game, attr, value)
            game.slug = game_data['slug']
            game.save()
        else:
            Game.objects.create(slug=game_data['slug'], **defaults)

    for slug, products in product_definitions.items():
        game = Game.objects.get(slug=slug)
        for product_data in products:
            price_brl = Decimal(product_data['price_brl'])
            price_inr = (price_brl * Decimal('19.07')).quantize(Decimal('0.01'))
            Product.objects.update_or_create(
                smile_product_id=str(product_data['smile_product_id']),
                defaults={
                    'game': game,
                    'name': product_data['name'],
                    'description': '',
                    'type': 'DIAMOND',
                    'diamond_amount': None,
                    'price_brl': price_brl,
                    'price_coins': 0,
                    'price_inr': price_inr,
                    'supplier_product_code': str(product_data['smile_product_id']),
                    'is_active': True,
                }
            )


def reverse_smile_games_and_products(apps, schema_editor):
    Game = apps.get_model('products', 'Game')
    Product = apps.get_model('products', 'Product')
    Product.objects.filter(smile_product_id__in=[
        '26148', '26555', '26556', '22590', '22591', '22592', '22593', '13', '23',
        '25', '26', '27', '28', '29', '30', '33', '16642',
        '164', '165', '166', '167', '168', '169',
        '18356', '18357', '18358', '18359', '18360', '18361', '18362',
        '617', '441', '442', '443', '444', '445',
        '26516', '26518', '26519', '26521', '26522',
    ]).delete()
    Game.objects.filter(slug__in=[
        'mobilelegends', 'hago', 'honkai', 'pubgmobile', 'identityv'
    ]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0005_product_price_brl_product_smile_product_id'),
    ]

    operations = [
        migrations.RunPython(create_smile_games_and_products, reverse_code=reverse_smile_games_and_products),
    ]
