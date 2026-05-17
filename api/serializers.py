from rest_framework import serializers
from products.models import Product, Game
from orders.models import Order
from wallet.models import Wallet, Transaction
from accounts.models import CustomUser


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ['id', 'name', 'short_name', 'slug', 'field_preset',
                  'checkout_fields', 'is_active', 'sort_order']


class ProductSerializer(serializers.ModelSerializer):
    game = GameSerializer(read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'smile_product_id', 'type', 'diamond_amount',
                  'price_brl', 'price_coins', 'price_inr', 'game', 'is_active']


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'type', 'amount', 'balance_after',
                  'note', 'created_at']


class WalletSerializer(serializers.ModelSerializer):
    transactions = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = ['id', 'balance', 'currency', 'transactions']

    def get_transactions(self, obj):
        txns = obj.transactions.all().order_by('-created_at')[:20]
        return TransactionSerializer(txns, many=True).data


class OrderSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'product', 'product_id', 'game',
            'player_uid', 'player_sid', 'player_fields',
            'quantity', 'total_coins', 'total_inr',
            'payment_method', 'payment_status', 'status',
            'smile_product_id', 'smile_order_id',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_coins', 'total_inr', 'payment_status',
            'status', 'smile_product_id', 'smile_order_id',
            'created_at', 'updated_at'
        ]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password']
        read_only_fields = ['id']

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        return user