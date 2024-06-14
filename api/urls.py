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
    path('', include(router.urls)),
    path('register', RegisterView.as_view(), name='register'),
    path('token', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh', TokenRefreshView.as_view(), name='token_refresh'),
]
