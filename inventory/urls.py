from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet, StockHistoryViewSet
from .views import DashboardAPIView
from .views import StockChartAPIView

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'stock', StockHistoryViewSet)

urlpatterns = [
    path('dashboard/', DashboardAPIView.as_view()),
    path('', include(router.urls)),
    path('dashboard/chart/', StockChartAPIView.as_view()),

]