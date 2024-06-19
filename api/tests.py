import pytest
from django.contrib.auth.models import User
from api.models import Itinerary, Place, Visit, DailyRoute, PlaceCategory


@pytest.fixture
def user(db):
    return User.objects.create_user(username='testuser', password='password')

@pytest.fixture
def itinerary(user):
    return Itinerary.objects.create(
        user=user,
        title='Test Itinerary',
        destination='Test Destination',
        description='Test Description',
        start_place_latitude=0.0,
        start_place_longitude=0.0,
        start_date='2023-01-01',
        end_date='2023-01-10',
        start_hour='09:00:00',
        end_hour='18:00:00',
        photo_url='http://example.com/photo.jpg'
    )

@pytest.fixture
def place(db):
    return Place.objects.create(
        name='Test Place',
        description='Test Description',
        address='123 Test St',
        latitude=0.0,
        longitude=0.0,
        category=PlaceCategory.OTHER
    )

@pytest.fixture
def visit(itinerary, place):
    return Visit.objects.create(
        itinerary=itinerary,
        place=place,
        day=1,
        duration=60,
        start_time='10:00:00'
    )

@pytest.fixture
def daily_route(itinerary):
    return DailyRoute.objects.create(
        itinerary=itinerary,
        day=1,
        geometry='Test Geometry'
    )

def test_itinerary_creation(itinerary):
    assert itinerary.title == 'Test Itinerary'
    assert itinerary.destination == 'Test Destination'
    assert itinerary.description == 'Test Description'
    assert itinerary.start_place_latitude == 0.0
    assert itinerary.start_place_longitude == 0.0
    assert itinerary.start_date.strftime('%Y-%m-%d') == '2023-01-01'
    assert itinerary.end_date.strftime('%Y-%m-%d') == '2023-01-10'
    assert itinerary.start_hour.strftime('%H:%M:%S') == '09:00:00'
    assert itinerary.end_hour.strftime('%H:%M:%S') == '18:00:00'
    assert itinerary.photo_url == 'http://example.com/photo.jpg'

def test_itinerary_days_count(itinerary):
    assert itinerary.days_count == 10

def test_place_creation(place):
    assert place.name == 'Test Place'
    assert place.description == 'Test Description'
    assert place.address == '123 Test St'
    assert place.latitude == 0.0
    assert place.longitude == 0.0
    assert place.category == PlaceCategory.OTHER

def test_visit_creation(visit):
    assert visit.itinerary.title == 'Test Itinerary'
    assert visit.place.name == 'Test Place'
    assert visit.day == 1
    assert visit.duration == 60
    assert visit.start_time.strftime('%H:%M:%S') == '10:00:00'

def test_daily_route_creation(daily_route):
    assert daily_route.itinerary.title == 'Test Itinerary'
    assert daily_route.day == 1
    assert daily_route.geometry == 'Test Geometry'

from rest_framework.test import APIClient

@pytest.fixture
def api_client():
    return APIClient()

def test_itinerary_visits_view(api_client, itinerary, visit):
    response = api_client.get(f'/api/itineraries/{itinerary.id}/visits/')
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['place'] == visit.place.id
    assert data[0]['day'] == visit.day
    assert data[0]['duration'] == visit.duration
    assert data[0]['start_time'] == visit.start_time.strftime('%H:%M:%S')
