from django.db import models

from .validators import validate_longitude, validate_latitude, validate_daterange, validate_timerange


class Itinerary(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    description = models.TextField()
    start_place_latitude = models.FloatField(validators=[validate_latitude])
    start_place_longitude = models.FloatField(validators=[validate_longitude])
    start_date = models.DateField()
    end_date = models.DateField()
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
        return (self.end_date - self.start_date).days + 1


class Place(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    address = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    category = models.TextField()

    class Meta:
        unique_together = ('name', 'latitude', 'longitude')

    def __str__(self):
        return self.name

    def get_estimated_duration(self):
        default_duration = 90

        # Duration in minutes for each category
        category_durations = {
            'cafe': 30,
            'park': 60,
            'zoo': 180,
            'place of worship': 45,
            'historic': 90,
            'fast food': 30,
            'mall': 120,
            'shop': 60,
            'museum': 120,
            'stadium': 90,
            'nature reserve': 120,
        }

        for key, duration in category_durations.items():
            if key in self.category.lower():
                return duration

        return default_duration


class Visit(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='visits')
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='visits')
    day = models.PositiveIntegerField()
    duration = models.PositiveIntegerField()
    start_time = models.TimeField()

    class Meta:
        unique_together = ('itinerary', 'day', 'place')
        ordering = ['itinerary', 'day']

    def __str__(self):
        return f"Day {self.day} - {self.place.name}"


class DailyRoute(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='daily_routes')
    day = models.PositiveIntegerField()
    geometry = models.TextField()

    class Meta:
        unique_together = ('itinerary', 'day')
        ordering = ['itinerary', 'day']

    def __str__(self):
        return f"Day {self.day} - {self.itinerary.title}"
