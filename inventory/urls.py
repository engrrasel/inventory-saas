from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    ProductViewSet,
    StockHistoryViewSet,
    PurchaseViewSet,
    DashboardAPIView,
    StockChartAPIView
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'stock', StockHistoryViewSet)
router.register(r'purchases', PurchaseViewSet)  # 🔥 ADD THIS

urlpatterns = [
    path('dashboard/', DashboardAPIView.as_view()),
    path('dashboard/chart/', StockChartAPIView.as_view()),

    path('', include(router.urls)),
]