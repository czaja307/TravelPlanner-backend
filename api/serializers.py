from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Itinerary, Place, Visit, DailyRoute
from .validators import validate_longitude, validate_latitude, validate_daterange, validate_timerange


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data


class ItinerarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Itinerary
        fields = '__all__'

    @staticmethod
    def validate_start_place_longitude(value):
        validate_longitude(value)
        return value

    @staticmethod
    def validate_start_place_latitude(value):
        validate_latitude(value)
        return value

    def validate(self, data):
        validate_daterange(data['start_date'], data['end_date'])
        validate_timerange(data['start_hour'], data['end_hour'])
        return data


class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = '__all__'


class VisitSerializer(serializers.ModelSerializer):
    place_name = serializers.CharField(source='place.name', read_only=True)
    latitude = serializers.FloatField(source='place.latitude', read_only=True)
    longitude = serializers.FloatField(source='place.longitude', read_only=True)

    class Meta:
        model = Visit
        fields = '__all__'


class PlaceDurationSerializer(serializers.Serializer):
    place_id = serializers.IntegerField()
    duration = serializers.FloatField()  # Duration in hours


class OptimizeRouteSerializer(serializers.Serializer):
    itinerary_id = serializers.IntegerField()
    places = serializers.ListField(
        child=PlaceDurationSerializer()
    )


class DailyRouteSerializer(serializers.ModelSerializer):
    itinerary = serializers.PrimaryKeyRelatedField(queryset=Itinerary.objects.all())
    day = serializers.IntegerField()

    class Meta:
        model = DailyRoute
        fields = ['itinerary', 'day', 'geometry']
        extra_kwargs = {
            'itinerary': {'validators': []},
            'day': {'validators': []},
        }

    def validate(self, attrs):
        itinerary = attrs.get('itinerary')
        day = attrs.get('day')
        if DailyRoute.objects.filter(itinerary=itinerary, day=day).exists():
            raise serializers.ValidationError(f"A daily route with itinerary {itinerary} and day {day} already exists.")
        return attrs
