import os
import uuid
from datetime import date, time

import django
import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from api.models import Itinerary, DailyRoute, Place, Visit
from api.serializers import DailyRouteSerializer, VisitSerializer, PlaceSerializer, ItinerarySerializer, \
    MyTokenObtainPairSerializer, UserSerializer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
django.setup()


@pytest.fixture
@pytest.mark.django_db
def user(request):
    # Generate a unique username to avoid conflicts
    unique_username = f'testuser_{uuid.uuid4()}'
    test_user = User.objects.create_user(username=unique_username, password='12345')

    # Check if the user was saved in the database
    assert test_user.pk is not None, "User was not saved in the database"

    # Cleanup after the test
    def teardown():
        if test_user.pk is not None:
            test_user.delete()

    request.addfinalizer(teardown)
    return test_user


# Example test using the user fixture
@pytest.mark.django_db
def test_user_creation(user):
    assert user.username.startswith('testuser_')
    assert user.check_password('12345')


@pytest.fixture
@pytest.mark.django_db
def itinerary(user):
    return Itinerary.objects.create(
        user=user,  # Use the created user fixture
        title='Test Itinerary',
        destination='Test Destination',
        description='Test Description',
        start_place_latitude=0.0,
        start_place_longitude=0.0,
        start_date=date(2023, 1, 1),
        end_date=date(2023, 1, 10),
        start_hour=time(9, 0),
        end_hour=time(18, 0),
        photo_url='https://example.com/photo.jpg'
    )


@pytest.mark.django_db
def test_itinerary_creation(itinerary):
    assert itinerary.title == 'Test Itinerary'
    assert itinerary.destination == 'Test Destination'
    assert itinerary.description == 'Test Description'
    assert itinerary.start_place_latitude == 0.0
    assert itinerary.start_place_longitude == 0.0
    assert itinerary.start_date.strftime('%Y-%m-%d') == '2023-01-01'
    assert itinerary.end_date.strftime('%Y-%m-%d') == '2023-01-10'


@pytest.mark.django_db
def test_itinerary_days_count(itinerary):
    assert itinerary.days_count == 10


@pytest.mark.django_db
def test_itinerary_str_representation(itinerary):
    assert str(itinerary) == 'Test Itinerary'


@pytest.mark.django_db
def test_itinerary_update(itinerary):
    itinerary.title = 'Updated Itinerary Title'
    itinerary.save()
    updated_itinerary = Itinerary.objects.get(id=itinerary.id)
    assert updated_itinerary.title == 'Updated Itinerary Title'


@pytest.mark.django_db
def test_itinerary_delete_user(user, itinerary):
    user.delete()
    assert Itinerary.objects.filter(id=itinerary.id).count() == 0


@pytest.mark.django_db
def test_itinerary_filter_by_user(user, itinerary):
    user_itineraries = Itinerary.objects.filter(user=user)
    assert len(user_itineraries) == 1
    assert user_itineraries[0] == itinerary


@pytest.mark.django_db
def test_itinerary_within_date_range(user):
    Itinerary.objects.create(
        user=user,
        title='Within Range Itinerary',
        destination='Range Destination',
        start_date=date(2023, 1, 5),
        end_date=date(2023, 1, 15),
        start_hour=time(9, 0),
        end_hour=time(18, 0)
    )
    itineraries_in_range = Itinerary.objects.filter(
        start_date__lte=date(2023, 1, 10),
        end_date__gte=date(2023, 1, 10)
    )
    assert len(itineraries_in_range) == 1
    assert itineraries_in_range[0].title == 'Within Range Itinerary'


@pytest.mark.django_db
def test_itinerary_within_date_range(user):
    itinerary = Itinerary.objects.create(
        user=user,
        title='Within Range Itinerary',
        destination='Range Destination',
        start_date=date(2023, 1, 5),
        end_date=date(2023, 1, 15),
        start_hour=time(9, 0),
        end_hour=time(18, 0),
        start_place_latitude=0.0,
        start_place_longitude=0.0,
    )
    assert itinerary.start_date == date(2023, 1, 5)
    assert itinerary.end_date == date(2023, 1, 15)
    assert itinerary.start_hour == time(9, 0)
    assert itinerary.end_hour == time(18, 0)


@pytest.mark.django_db
def test_itinerary_exceed_date_range(user):
    itinerary = Itinerary.objects.create(
        user=user,
        title='Exceed Range Itinerary',
        destination='Range Destination',
        start_date=date(2023, 1, 1),
        end_date=date(2023, 1, 20),
        start_hour=time(9, 0),
        end_hour=time(18, 0),
        start_place_latitude=0.0,
        start_place_longitude=0.0,
    )
    assert itinerary.start_date == date(2023, 1, 1)
    assert itinerary.end_date == date(2023, 1, 20)
    assert itinerary.start_hour == time(9, 0)
    assert itinerary.end_hour == time(18, 0)


# Place Model Tests
@pytest.fixture
@pytest.mark.django_db
def place():
    return Place.objects.create(
        name='Test Place',
        description='A place for testing',
        address='123 Test St',
        latitude=0.0,
        longitude=0.0,
        category='museum'
    )


@pytest.mark.django_db
def test_place_creation(place):
    assert place.name == 'Test Place'
    assert place.description == 'A place for testing'
    assert place.address == '123 Test St'
    assert place.latitude == 0.0
    assert place.longitude == 0.0
    assert place.category == 'museum'


@pytest.mark.django_db
def test_place_unique_constraint():
    Place.objects.create(
        name='Unique Place',
        description='First instance',
        address='123 Test St',
        latitude=0.0,
        longitude=0.0,
        category='museum'
    )
    with pytest.raises(ValidationError):
        place = Place(
            name='Unique Place',
            description='Duplicate instance',
            address='123 Test St',
            latitude=0.0,
            longitude=0.0,
            category='museum'
        )
        place.full_clean()


@pytest.mark.django_db
def test_place_estimated_duration(place):
    assert place.get_estimated_duration() == 180


# Visit Model Tests
@pytest.fixture
@pytest.mark.django_db
def visit(itinerary, place):
    return Visit.objects.create(
        itinerary=itinerary,
        place=place,
        day=1,
        duration=120,
        start_time=time(10, 0)
    )


@pytest.mark.django_db
def test_visit_creation(visit):
    assert visit.itinerary.title == 'Test Itinerary'
    assert visit.place.name == 'Test Place'
    assert visit.day == 1
    assert visit.duration == 120
    assert visit.start_time == time(10, 0)


@pytest.mark.django_db
def test_visit_unique_constraint(itinerary, place):
    Visit.objects.create(
        itinerary=itinerary,
        place=place,
        day=1,
        duration=120,
        start_time=time(10, 0)
    )
    with pytest.raises(ValidationError):
        visit = Visit(
            itinerary=itinerary,
            place=place,
            day=1,
            duration=60,
            start_time=time(11, 0)
        )
        visit.full_clean()


@pytest.mark.django_db
def test_visit_str_representation(visit):
    assert str(visit) == 'Day 1 - Test Place'


# DailyRoute Model Tests
@pytest.fixture
@pytest.mark.django_db
def daily_route(itinerary):
    encoded_polyline = '??_ibE?_seK_seK_seK'
    return DailyRoute.objects.create(
        itinerary=itinerary,
        day=1,
        geometry=encoded_polyline
    )


@pytest.mark.django_db
def test_daily_route_creation(daily_route):
    assert daily_route.itinerary.title == 'Test Itinerary'
    assert daily_route.day == 1
    assert daily_route.geometry == '??_ibE?_seK_seK_seK'


@pytest.mark.django_db
def test_daily_route_unique_constraint(itinerary):
    DailyRoute.objects.create(
        itinerary=itinerary,
        day=1,
        geometry='??_ibE?_seK_seK_seK'
    )
    with pytest.raises(ValidationError):
        daily_route = DailyRoute(
            itinerary=itinerary,
            day=1,
            geometry='??_ibE?_seK_seK_seK'
        )
        daily_route.full_clean()


@pytest.mark.django_db
def test_daily_route_str_representation(daily_route):
    assert str(daily_route) == 'Day 1 - Test Itinerary'


# SERIALIZERS TESTS

@pytest.mark.django_db
def test_user_serializer():
    data = {'username': 'testuser', 'email': 'testuser@example.com', 'password': 'password123'}
    serializer = UserSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    user = serializer.save()
    assert User.objects.count() == 1
    assert user.check_password('password123')


@pytest.mark.django_db
def test_token_obtain_pair_serializer(user):
    data = {'username': user.username, 'password': '12345'}
    serializer = MyTokenObtainPairSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    token_data = serializer.validated_data
    assert 'access' in token_data
    assert 'refresh' in token_data
    assert 'user' in token_data
    assert token_data['user']['username'] == user.username


@pytest.mark.django_db
def test_itinerary_serializer(user):
    data = {
        'user': user.id,
        'title': 'Test Itinerary',
        'destination': 'Test Destination',
        'description': 'Test Description',
        'start_place_latitude': 0.0,
        'start_place_longitude': 0.0,
        'start_date': date(2023, 1, 1),
        'end_date': date(2023, 1, 10),
        'start_hour': time(9, 0),
        'end_hour': time(18, 0),
        'photo_url': 'https://example.com/photo.jpg'
    }
    serializer = ItinerarySerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    itinerary = serializer.save()
    assert Itinerary.objects.count() == 1
    assert itinerary.title == 'Test Itinerary'


@pytest.mark.django_db
def test_itinerary_serializer_invalid_latitude(user):
    data = {
        'user': user.id,
        'title': 'Test Itinerary',
        'destination': 'Test Destination',
        'description': 'Test Description',
        'start_place_latitude': 100.0,  # Invalid latitude
        'start_place_longitude': 0.0,
        'start_date': date(2023, 1, 1),
        'end_date': date(2023, 1, 10),
        'start_hour': time(9, 0),
        'end_hour': time(18, 0),
        'photo_url': 'https://example.com/photo.jpg'
    }
    serializer = ItinerarySerializer(data=data)
    assert not serializer.is_valid()
    assert 'start_place_latitude' in serializer.errors


@pytest.mark.django_db
def test_place_serializer():
    data = {
        'name': 'Test Place',
        'description': 'A place for testing',
        'address': '123 Test St',
        'latitude': 0.0,
        'longitude': 0.0,
        'category': 'museum'
    }
    serializer = PlaceSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    place = serializer.save()
    assert Place.objects.count() == 1
    assert place.name == 'Test Place'


@pytest.mark.django_db
def test_visit_serializer(itinerary, place):
    data = {
        'itinerary': itinerary.id,
        'place': place.id,
        'day': 1,
        'duration': 120,
        'start_time': time(10, 0)
    }
    serializer = VisitSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    visit = serializer.save()
    assert Visit.objects.count() == 1
    assert visit.itinerary == itinerary
    assert visit.place == place


@pytest.mark.django_db
def test_daily_route_serializer(itinerary):
    data = {
        'itinerary': itinerary.id,
        'day': 1,
        'geometry': '??_ibE?_seK_seK_seK'  # Encoded polyline
    }
    serializer = DailyRouteSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    daily_route = serializer.save()
    assert DailyRoute.objects.count() == 1
    assert daily_route.itinerary == itinerary
    assert daily_route.day == 1
