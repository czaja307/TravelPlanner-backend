from datetime import timedelta

import openrouteservice.optimization
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework import status
from rest_framework import viewsets
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Itinerary, Place, Visit
from .permissions import IsOwner
from .serializers import ItinerarySerializer, PlaceSerializer, VisitSerializer, OptimizeRouteSerializer
from .serializers import UserSerializer, MyTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        data['password'] = make_password(data['password'])
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class ItineraryViewSet(viewsets.ModelViewSet):
    queryset = Itinerary.objects.all()
    serializer_class = ItinerarySerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PlaceViewSet(viewsets.ModelViewSet):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset


class VisitViewSet(viewsets.ModelViewSet):
    queryset = Visit.objects.all()
    serializer_class = VisitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(itinerary__user=self.request.user)


class OptimizeRouteView(GenericAPIView):
    serializer_class = OptimizeRouteSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        itinerary_id = serializer.validated_data['itinerary_id']
        places_data = serializer.validated_data['places']

        itinerary = get_object_or_404(Itinerary, pk=itinerary_id)
        places = []
        durations = []

        for place_data in places_data:
            place = get_object_or_404(Place, pk=place_data['place_id'])
            places.append(place)
            durations.append(place_data['duration'])

        ors_client = openrouteservice.Client(key=settings.OPENROUTESERVICE_API_KEY)
        coordinates = [(place.longitude, place.latitude) for place in places]
        start_coordinates = (itinerary.start_place_longitude, itinerary.start_place_latitude)

        days_count = (itinerary.end_date.date() - itinerary.start_date.date()).days + 1
        print(itinerary.end_date)
        print(itinerary.start_date)
        print(days_count)
        start_hour_seconds = itinerary.start_hour.hour * 3600 + itinerary.start_hour.minute * 60
        end_hour_seconds = itinerary.end_hour.hour * 3600 + itinerary.end_hour.minute * 60

        vehicles = [
            openrouteservice.optimization.Vehicle(
                id=day,
                start=start_coordinates,
                end=start_coordinates,
                time_window=[start_hour_seconds, end_hour_seconds],
            ) for day in range(days_count)
        ]

        for vehicle in vehicles:
            print(vehicle.id, vehicle.start, vehicle.end, vehicle.time_window)

        jobs = [
            openrouteservice.optimization.Job(
                id=idx,
                location=coord,
                service=duration * 60  # Duration in seconds
            ) for idx, (coord, duration) in enumerate(zip(coordinates, durations))
        ]

        optimized_route = openrouteservice.optimization.optimization(
            ors_client,
            jobs=jobs,
            vehicles=vehicles,
            geometry=True
        )

        print(optimized_route)

        # Parse optimized route
        visits = []
        day_geometries = {}
        for route in optimized_route['routes']:
            day = route['vehicle'] + 1  # Vehicle ID corresponds to the day (0-indexed)
            day_geometries[day] = route['geometry']

            # The start date for the current day
            current_date = itinerary.start_date + timedelta(days=day - 1)

            for step in route['steps']:
                if step['type'] == 'job':
                    place = places[step['job']]

                    # Calculate the start time by adding the arrival time (in seconds) to the start of the day
                    arrival_seconds = step['arrival']
                    start_time = str(timedelta(seconds=arrival_seconds))

                    visit = Visit(
                        itinerary=itinerary,
                        place=place,
                        day=day,
                        duration=durations[step['job']],
                        start_time=start_time
                    )
                    visits.append(visit)

        with transaction.atomic():
            Visit.objects.filter(itinerary=itinerary).delete()
            Visit.objects.bulk_create(visits)

        response_data = {
            "itinerary": itinerary_id,
            "days": []
        }

        days_group = {}
        for visit in visits:
            if visit.day not in days_group:
                days_group[visit.day] = []
            days_group[visit.day].append({
                "place_name": visit.place.name,
                "start_time": visit.start_time,
                "duration": visit.duration,
                "latitude": visit.place.latitude,
                "longitude": visit.place.longitude,
                "geometry": visit.geometry,
            })

        for day, visits in days_group.items():
            response_data["days"].append({
                "day": day,
                "visits": visits,
                "geometry": day_geometries.get(day),
            })

        return Response(response_data, status=status.HTTP_200_OK)


class ItineraryVisitsView(ListAPIView):
    serializer_class = VisitSerializer

    def get_queryset(self):
        itinerary_id = self.kwargs['itinerary_id']
        itinerary = get_object_or_404(Itinerary, pk=itinerary_id)
        return Visit.objects.filter(itinerary=itinerary).order_by('day', 'start_time')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        itinerary_id = self.kwargs['itinerary_id']
        response_data = {
            "itinerary": itinerary_id,
            "visits": serializer.data
        }
        return Response(response_data, status=status.HTTP_200_OK)
