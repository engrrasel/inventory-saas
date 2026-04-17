from rest_framework import serializers
from .models import Category, Product, StockHistory


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ['company']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['company', 'quantity']


class StockHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockHistory
        fields = '__all__'
        read_only_fields = ['company', 'created_at']

    def validate(self, data):
        product = data.get('product')
        company = self.context['request'].user.company

        # company match check
        if product.company != company:
            raise serializers.ValidationError("Invalid product for this company")

        return data

    def create(self, validated_data):
        validated_data['company'] = self.context['request'].user.company
        return super().create(validated_data)
    

from rest_framework import serializers


class DashboardSerializer(serializers.Serializer):
    total_products = serializers.IntegerField()
    total_stock_quantity = serializers.IntegerField()
    total_stock_value = serializers.DecimalField(max_digits=12, decimal_places=2)

    today_in = serializers.IntegerField()
    today_out = serializers.IntegerField()

    low_stock_products = serializers.ListField()