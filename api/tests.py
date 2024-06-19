import pytest
from django.contrib.auth.models import User
from api.models import Itinerary
from datetime import date, time

@pytest.fixture
@pytest.mark.django_db
def user():
    return User.objects.create_user(username='testuser', password='12345')

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
        photo_url='http://example.com/photo.jpg'
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
    assert itinerary.days_count == 10  # Update this if `days_count` is calculated differently

@pytest.mark.django_db
def test_itinerary_str_representation(itinerary):
    assert str(itinerary) == 'Test Itinerary'  # Adjust based on your model's __str__ method


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
    # Add appropriate assertions to the test
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
    # Add appropriate assertions to the test
    assert itinerary.start_date == date(2023, 1, 1)
    assert itinerary.end_date == date(2023, 1, 20)
    assert itinerary.start_hour == time(9, 0)
    assert itinerary.end_hour == time(18, 0)