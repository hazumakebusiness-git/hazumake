import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hazu.settings')
django.setup()

from hazu.services.smileone import create_order, get_product_list, get_role


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Standalone Smile.one flow test script')
    parser.add_argument('--game', default='mobilelegends', help='Smile.one game name')
    parser.add_argument('--productid', required=True, help='Smile.one product id')
    parser.add_argument('--userid', required=True, help='Player userid/uid')
    parser.add_argument('--zoneid', default='', help='Optional zone id/server id')
    args = parser.parse_args()

    print('Smile.one smoke test')
    print('  game:', args.game)
    print('  productid:', args.productid)
    print('  userid:', args.userid)
    print('  zoneid:', args.zoneid)

    products = get_product_list(args.game)
    print('Product list count:', len(products))
    print('Sample products:', products[:3])

    username = get_role(args.game, args.productid, args.userid, args.zoneid)
    print('Verified username:', username)

    order_id = create_order(args.game, args.productid, args.userid, args.zoneid)
    print('Created order ID:', order_id)
