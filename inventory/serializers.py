from rest_framework import serializers
from django.db import transaction

from .models import (
    Category,
    Product,
    StockHistory,
    Purchase,
    PurchaseItem
)


# =========================
# CATEGORY
# =========================
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ['company']


# =========================
# PRODUCT
# =========================
from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['company', 'quantity', 'buying_price']

# =========================
# STOCK HISTORY
# =========================
class StockHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockHistory
        fields = '__all__'
        read_only_fields = ['company', 'created_at']

    def validate(self, data):
        request = self.context.get('request')

        if not request or not request.user.company:
            raise serializers.ValidationError("Company not found.")

        product = data.get('product')
        quantity = data.get('quantity')
        transaction_type = data.get('transaction_type')

        # ✅ company check
        if product.company != request.user.company:
            raise serializers.ValidationError("Invalid product for this company.")

        # 🔥 CRITICAL FIX → OUT validation
        if transaction_type == 'OUT':
            if product.quantity < quantity:
                raise serializers.ValidationError(
                    f"Only {product.quantity} items available in stock, but you tried to use {quantity}."
                )

        return data

    def create(self, validated_data):
        validated_data['company'] = self.context['request'].user.company
        return super().create(validated_data)


# =========================
# PURCHASE ITEM
# =========================
class PurchaseItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = PurchaseItem
        fields = ['id', 'product', 'product_name', 'quantity', 'cost_price']


# =========================
# PURCHASE (CREATE + LIST)
# =========================
class PurchaseSerializer(serializers.ModelSerializer):
    items = PurchaseItemSerializer(many=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Purchase
        fields = [
            'id',
            'vendor_name',
            'lot_number',
            'purchase_date',
            'status',
            'status_display',
            'items'
        ]
        read_only_fields = ['status']

    # ✅ VALIDATION
    def validate(self, data):
        request = self.context.get('request')

        if not request or not request.user.company:
            raise serializers.ValidationError("Company not found.")

        items = data.get('items', [])

        if not items:
            raise serializers.ValidationError("At least one item is required.")

        for item in items:
            if item['product'].company != request.user.company:
                raise serializers.ValidationError("Invalid product for this company.")

        return data

    # ✅ CREATE (TRANSACTION SAFE)
    def create(self, validated_data):
        items_data = validated_data.pop('items')

        with transaction.atomic():
            purchase = Purchase.objects.create(**validated_data)

            for item in items_data:
                PurchaseItem.objects.create(
                    purchase=purchase,
                    **item
                )

        return purchase


# =========================
# PURCHASE DETAIL (READ)
# =========================
class PurchaseDetailSerializer(serializers.ModelSerializer):
    items = PurchaseItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Purchase
        fields = '__all__'


# =========================
# DASHBOARD
# =========================
class DashboardSerializer(serializers.Serializer):
    total_products = serializers.IntegerField()
    total_stock_quantity = serializers.IntegerField()
    total_stock_value = serializers.DecimalField(max_digits=12, decimal_places=2)

    today_in = serializers.IntegerField()
    today_out = serializers.IntegerField()

    total_profit = serializers.DecimalField(max_digits=12, decimal_places=2)
    today_profit = serializers.DecimalField(max_digits=12, decimal_places=2)

    low_stock_products = serializers.ListField()