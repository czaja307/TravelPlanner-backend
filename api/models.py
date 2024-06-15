from django.db import models
from django.utils.translation import gettext_lazy as _

from .validators import validate_longitude, validate_latitude, validate_daterange, validate_timerange


class Itinerary(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    start_place_longitude = models.FloatField(validators=[validate_longitude])
    start_place_latitude = models.FloatField(validators=[validate_latitude])
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    start_hour = models.TimeField()
    end_hour = models.TimeField()
    photo_url = models.URLField(max_length=200, blank=True, null=True)

    def clean(self):
        validate_daterange(self.start_date, self.end_date)
        validate_timerange(self.start_hour, self.end_hour)

    def __str__(self):
        return self.title

    @property
    def days_count(self):
        return (self.end_date.date() - self.start_date.date()).days + 1


# TODO: adjust to the actual categories
class PlaceCategory(models.TextChoices):
    HISTORICAL = 'historical', _('Historical')
    MUSEUM = 'museum', _('Museum')
    PARK = 'park', _('Park')
    RESTAURANT = 'restaurant', _('Restaurant')
    HOTEL = 'hotel', _('Hotel')
    SHOPPING = 'shopping', _('Shopping')
    OTHER = 'other', _('Other')


class Place(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    address = models.CharField(max_length=255)
    longitude = models.FloatField()
    latitude = models.FloatField()
    category = models.CharField(
        max_length=50,
        choices=PlaceCategory.choices,
        default=PlaceCategory.OTHER,
    )

    def __str__(self):
        return self.name


class Visit(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='visits')
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='visits')
    day = models.PositiveIntegerField()
    duration = models.PositiveIntegerField()

    class Meta:
        unique_together = ('itinerary', 'day', 'place')
        ordering = ['itinerary', 'day']

    def __str__(self):
        return f"Day {self.day} - {self.place.name}"
