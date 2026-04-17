from rest_framework import viewsets, permissions, filters
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend

from .models import Category, Product, StockHistory
from .serializers import CategorySerializer, ProductSerializer, StockHistorySerializer

from datetime import timedelta


# ✅ Custom Permission (Company required)
class IsCompanyUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'company')
            and request.user.company is not None
        )


# =========================
# ✅ CATEGORY VIEWSET
# =========================
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()   # 🔥 ADD THIS
    serializer_class = CategorySerializer
    permission_classes = [IsCompanyUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        return Category.objects.filter(company=self.request.user.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


# =========================
# ✅ PRODUCT VIEWSET
# =========================
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()   # 🔥 ADD THIS
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
# ✅ STOCK HISTORY VIEWSET
# =========================
class StockHistoryViewSet(viewsets.ModelViewSet):
    queryset = StockHistory.objects.all()   # 🔥 ADD THIS
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


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.db.models import Sum, F
from django.utils.timezone import now

from .models import Product, StockHistory
from .serializers import DashboardSerializer


class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = request.user.company

        # 🔹 Total Products
        total_products = Product.objects.filter(company=company).count()

        # 🔹 Total Stock Quantity
        total_stock_quantity = Product.objects.filter(company=company).aggregate(
            total=Sum('quantity')
        )['total'] or 0

        # 🔹 Total Stock Value (price × quantity)
        total_stock_value = Product.objects.filter(company=company).aggregate(
            total=Sum(F('price') * F('quantity'))
        )['total'] or 0

        # 🔹 Today date
        today = now().date()

        # 🔹 Today IN
        today_in = StockHistory.objects.filter(
            company=company,
            transaction_type='IN',
            created_at__date=today
        ).aggregate(total=Sum('quantity'))['total'] or 0

        # 🔹 Today OUT
        today_out = StockHistory.objects.filter(
            company=company,
            transaction_type='OUT',
            created_at__date=today
        ).aggregate(total=Sum('quantity'))['total'] or 0

        # 🔹 Low stock (quantity < 5)
        low_stock = Product.objects.filter(
            company=company,
            quantity__lt=5
        ).values('id', 'name', 'quantity')

        data = {
            "total_products": total_products,
            "total_stock_quantity": total_stock_quantity,
            "total_stock_value": total_stock_value,
            "today_in": today_in,
            "today_out": today_out,
            "low_stock_products": list(low_stock)
        }

        serializer = DashboardSerializer(data)
        return Response(serializer.data)
    


class StockChartAPIView(APIView):
    permission_classes = [IsAuthenticated]

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