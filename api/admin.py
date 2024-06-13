from django.contrib import admin

from api.models import Itinerary, Place, Visit


# Register your models here.
@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'start_date', 'end_date')
    search_fields = ('title', 'user__username')
    list_filter = ('start_date', 'end_date')


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'category')
    search_fields = ('name', 'address')
    list_filter = ('category',)


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ('itinerary', 'place', 'day', 'duration')
    search_fields = ('itinerary__title', 'place__name')
    list_filter = ('itinerary', 'day')
