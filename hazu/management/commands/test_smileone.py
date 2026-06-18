from django.core.management.base import BaseCommand
from hazu.services.smileone import create_order, get_product_list, get_role


class Command(BaseCommand):
    help = 'Run a Smile.one smoke test for product list, player verification, and create order.'

    def add_arguments(self, parser):
        parser.add_argument('--game', default='mobilelegends', help='Smile.one game name (default: mobilelegends)')
        parser.add_argument('--productid', required=True, help='Smile.one productid to test')
        parser.add_argument('--userid', required=True, help='Player userid/uid for get_role/create_order')
        parser.add_argument('--zoneid', default='', help='Optional zoneid/server id')

    def handle(self, *args, **options):
        game = options['game']
        productid = options['productid']
        userid = options['userid']
        zoneid = options['zoneid']

        self.stdout.write(self.style.SUCCESS('Starting Smile.one smoke test...'))

        self.stdout.write('1) Fetching product list...')
        products = get_product_list(game)
        if products:
            self.stdout.write(self.style.SUCCESS(f'  ✅ Retrieved {len(products)} products'))
        else:
            self.stdout.write(self.style.ERROR('  ❌ Product list returned empty or failed'))

        self.stdout.write('2) Verifying player role...')
        username = get_role(game, productid, userid, zoneid)
        if username:
            self.stdout.write(self.style.SUCCESS(f'  ✅ Player verified as {username}'))
        else:
            self.stdout.write(self.style.ERROR('  ❌ Player verification failed'))

        self.stdout.write('3) Creating Smile.one order...')
        order_id = create_order(game, productid, userid, zoneid)
        if order_id:
            self.stdout.write(self.style.SUCCESS(f'  ✅ Order created: {order_id}'))
        else:
            self.stdout.write(self.style.ERROR('  ❌ Order creation failed'))
