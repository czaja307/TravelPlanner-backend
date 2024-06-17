from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import ItineraryViewSet, PlaceViewSet, VisitViewSet, RegisterView, MyTokenObtainPairView, OptimizeRouteView, \
    ItineraryVisitsView

router = DefaultRouter()
router.register(r'itineraries', ItineraryViewSet)
router.register(r'places', PlaceViewSet)
router.register(r'visits', VisitViewSet)

router = DefaultRouter()
router.register(r'itineraries', ItineraryViewSet)
router.register(r'places', PlaceViewSet)
router.register(r'visits', VisitViewSet)

urlpatterns = [
    path('optimize-route/', OptimizeRouteView.as_view(), name='optimize-route'),
    path('itinerary/<int:itinerary_id>/visits/', ItineraryVisitsView.as_view(), name='itinerary-visits'),
    path('register', RegisterView.as_view(), name='register'),
    path('token', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]
