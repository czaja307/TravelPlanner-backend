from datetime import timedelta

import openrouteservice.optimization
from django.conf import settings
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

    def create(self, request, *args, **kwargs):
        data = request.data
        name = data.get('name')
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        # Check if a place with the same name, latitude, and longitude exists
        place, created = Place.objects.get_or_create(
            name=name,
            latitude=latitude,
            longitude=longitude,
            defaults=data
        )

        serializer = self.get_serializer(place)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class VisitViewSet(viewsets.ModelViewSet):
    queryset = Visit.objects.all()
    serializer_class = VisitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(itinerary__user=self.request.user)


class OptimizeRouteView(GenericAPIView):
    serializer_class = OptimizeRouteSerializer

    MAX_VEHICLES_PER_OPTIMIZATION = 3

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        itinerary_id = serializer.validated_data['itinerary_id']
        places_data = serializer.validated_data['places']

        itinerary, places, durations = self.validate_and_fetch(itinerary_id, places_data)
        days_count = (itinerary.end_date - itinerary.start_date).days + 1

        # Calculate the number of segments needed
        num_segments = -(-days_count // self.MAX_VEHICLES_PER_OPTIMIZATION)

        # Split places and durations based on the number of segments
        segment_size = len(places) // num_segments + (len(places) % num_segments > 0)
        segments = [places[i:i + segment_size] for i in range(0, len(places), segment_size)]
        print(segments)
        duration_segments = [durations[i:i + segment_size] for i in range(0, len(durations), segment_size)]
        print(duration_segments)

        visits = []
        status_codes = []
        all_day_geometries = {}

        for segment_index, (segment, duration_segment) in enumerate(zip(segments, duration_segments)):
            segment_days_count = min(days_count - segment_index * self.MAX_VEHICLES_PER_OPTIMIZATION,
                                     self.MAX_VEHICLES_PER_OPTIMIZATION)

            optimized_route, status_code = self.optimize_segment(itinerary, segment, duration_segment,
                                                                 segment_days_count)

            print(optimized_route)

            if 'error' in optimized_route:
                return Response({"error": optimized_route['error']}, status=status.HTTP_400_BAD_REQUEST)

            status_codes.append(status_code)
            segment_visits, day_geometries = self.parse_optimized_route(itinerary, optimized_route, segment,
                                                                        duration_segment,
                                                                        segment_index * self.MAX_VEHICLES_PER_OPTIMIZATION)
            visits.extend(segment_visits)
            all_day_geometries.update(day_geometries)

        self.save_visits(itinerary, visits)

        response_data = self.prepare_response_data(itinerary_id, visits, days_count, all_day_geometries)
        response_data["status"] = max(status_codes)

        return Response(response_data, status=status.HTTP_200_OK)

    def validate_and_fetch(self, itinerary_id, places_data):
        itinerary = get_object_or_404(Itinerary, pk=itinerary_id)
        places = []
        durations = []

        for place_data in places_data:
            place = get_object_or_404(Place, pk=place_data['place_id'])
            places.append(place)
            durations.append(place_data['duration'])

        return itinerary, places, durations

    def create_vehicles(self, itinerary, days_count):
        start_coordinates = (itinerary.start_place_longitude, itinerary.start_place_latitude)
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
        return vehicles

    def create_jobs(self, places, durations):
        coordinates = [(place.longitude, place.latitude) for place in places]
        jobs = [
            openrouteservice.optimization.Job(
                id=idx,
                location=coord,
                service=duration * 60  # Duration in seconds
            ) for idx, (coord, duration) in enumerate(zip(coordinates, durations))
        ]
        return jobs

    def optimize_segment(self, itinerary, places, durations, days_count):
        ors_client = openrouteservice.Client(key=settings.OPENROUTESERVICE_API_KEY)
        vehicles = self.create_vehicles(itinerary, days_count)
        jobs = self.create_jobs(places, durations)

        optimized_route = openrouteservice.optimization.optimization(
            ors_client,
            jobs=jobs,
            vehicles=vehicles,
            geometry=True
        )

        # Initialize status code
        status_code = 0

        # Check for unused vehicles
        used_vehicles = set(route['vehicle'] for route in optimized_route['routes'])
        unused_vehicles = len(used_vehicles) < len(vehicles)

        # Check for discarded places
        unassigned_jobs = optimized_route.get('unassigned', {})
        discarded_places = bool(unassigned_jobs)

        if unused_vehicles and discarded_places:
            status_code = 3
        elif discarded_places:
            status_code = 1
        elif unused_vehicles:
            status_code = 2

        return optimized_route, status_code

    def parse_optimized_route(self, itinerary, optimized_route, places, durations, start_day_offset):
        visits = []
        day_geometries = {}
        for route in optimized_route['routes']:
            day = route['vehicle'] + 1 + start_day_offset  # Adjust for the segment offset
            day_geometries[day] = route['geometry']

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

        return visits, day_geometries

    def save_visits(self, itinerary, visits):
        with transaction.atomic():
            Visit.objects.filter(itinerary=itinerary).delete()
            Visit.objects.bulk_create(visits)

    def prepare_response_data(self, itinerary_id, visits, total_days, all_day_geometries):
        response_data = {
            "itinerary": itinerary_id,
            "days": []
        }

        days_group = {day: [] for day in range(1, total_days + 1)}

        for visit in visits:
            days_group[visit.day].append({
                "place_name": visit.place.name,
                "start_time": visit.start_time,
                "duration": visit.duration,
                "latitude": visit.place.latitude,
                "longitude": visit.place.longitude,
            })

        for day, visits in days_group.items():
            response_data["days"].append({
                "day": day,
                "visits": visits,
                "geometry": all_day_geometries.get(day)
            })

        return response_data


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
