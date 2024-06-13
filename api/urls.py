from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import ItineraryViewSet, PlaceViewSet, VisitViewSet, RegisterView, MyTokenObtainPairView

router = DefaultRouter()
router.register(r'itineraries', ItineraryViewSet)
router.register(r'places', PlaceViewSet)
router.register(r'visits', VisitViewSet)

router = DefaultRouter()
router.register(r'itineraries', ItineraryViewSet)
router.register(r'places', PlaceViewSet)
router.register(r'visits', VisitViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
