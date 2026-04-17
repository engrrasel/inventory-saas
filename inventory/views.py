from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from django.utils.timezone import now
from django_filters.rest_framework import DjangoFilterBackend

from datetime import timedelta

from .models import Category, Product, StockHistory, Purchase
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    StockHistorySerializer,
    PurchaseSerializer,
    DashboardSerializer
)


# =========================
# ✅ PERMISSION
# =========================
class IsCompanyUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'company')
            and request.user.company is not None
        )


# =========================
# ✅ CATEGORY
# =========================
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()  # 🔥 MUST for router
    serializer_class = CategorySerializer
    permission_classes = [IsCompanyUser]

    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        return Category.objects.filter(company=self.request.user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


# =========================
# ✅ PRODUCT
# =========================
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()  # 🔥 MUST
    serializer_class = ProductSerializer
    permission_classes = [IsCompanyUser]

    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        return Product.objects.filter(company=self.request.user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)

    def perform_update(self, serializer):
        serializer.save(company=self.request.user.company)


# =========================
# ✅ STOCK HISTORY
# =========================
class StockHistoryViewSet(viewsets.ModelViewSet):
    queryset = StockHistory.objects.all()  # 🔥 MUST
    serializer_class = StockHistorySerializer
    permission_classes = [IsCompanyUser]

    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['product__name', 'transaction_type']
    filterset_fields = ['transaction_type', 'product']

    def get_queryset(self):
        return StockHistory.objects.filter(
            company=self.request.user.company
        ).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


# =========================
# 📊 DASHBOARD
# =========================
class DashboardAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        company = request.user.company
        today = now().date()

        total_products = Product.objects.filter(company=company).count()

        total_stock_quantity = Product.objects.filter(company=company).aggregate(
            total=Sum('quantity')
        )['total'] or 0

        total_stock_value = Product.objects.filter(company=company).aggregate(
            total=Sum(F('selling_price') * F('quantity'))
        )['total'] or 0

        today_in = StockHistory.objects.filter(
            company=company,
            transaction_type='IN',
            created_at__date=today
        ).aggregate(total=Sum('quantity'))['total'] or 0

        today_out = StockHistory.objects.filter(
            company=company,
            transaction_type='OUT',
            created_at__date=today
        ).aggregate(total=Sum('quantity'))['total'] or 0

        profit_expr = ExpressionWrapper(
            (F('product__selling_price') - F('product__buying_price')) * F('quantity'),
            output_field=DecimalField()
        )

        total_profit = StockHistory.objects.filter(
            company=company,
            transaction_type='OUT'
        ).aggregate(total=Sum(profit_expr))['total'] or 0

        today_profit = StockHistory.objects.filter(
            company=company,
            transaction_type='OUT',
            created_at__date=today
        ).aggregate(total=Sum(profit_expr))['total'] or 0

        low_stock = Product.objects.filter(
            company=company,
            quantity__lt=5
        ).values('id', 'name', 'quantity')

        return Response({
            "total_products": total_products,
            "total_stock_quantity": total_stock_quantity,
            "total_stock_value": total_stock_value,
            "today_in": today_in,
            "today_out": today_out,
            "total_profit": total_profit,
            "today_profit": today_profit,
            "low_stock_products": list(low_stock)
        })


# =========================
# 📈 CHART
# =========================
class StockChartAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        company = request.user.company
        today = now().date()
        days = []

        for i in range(6, -1, -1):
            day = today - timedelta(days=i)

            day_in = StockHistory.objects.filter(
                company=company,
                transaction_type='IN',
                created_at__date=day
            ).aggregate(total=Sum('quantity'))['total'] or 0

            day_out = StockHistory.objects.filter(
                company=company,
                transaction_type='OUT',
                created_at__date=day
            ).aggregate(total=Sum('quantity'))['total'] or 0

            days.append({
                "date": day.strftime("%Y-%m-%d"),
                "in": day_in,
                "out": day_out
            })

        return Response(days)


# =========================
# 🧾 PURCHASE
# =========================
class PurchaseViewSet(viewsets.ModelViewSet):
    queryset = Purchase.objects.all()  # 🔥 MUST
    serializer_class = PurchaseSerializer
    permission_classes = [IsCompanyUser]

    def get_queryset(self):
        return Purchase.objects.filter(
            company=self.request.user.company
        ).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        purchase = self.get_object()

        if purchase.status == Purchase.APPROVED:
            return Response({"error": "Already approved"}, status=400)

        try:
            purchase.approve(request.user)
            return Response({
                "message": "Purchase approved successfully",
                "purchase_id": purchase.id
            })
        except Exception as e:
            return Response({"error": str(e)}, status=400)