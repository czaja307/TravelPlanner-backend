from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_longitude(longitude):
    if longitude < -180 or longitude > 180:
        raise ValidationError(_('Longitude must be between -180 and 180'))


def validate_latitude(latitude):
    if latitude < -90 or latitude > 90:
        raise ValidationError(_('Latitude must be between -90 and 90'))


def validate_daterange(start_date, end_date):
    if start_date > end_date:
        raise ValidationError(_('Start date must be before end date'))


def validate_timerange(start_hour, end_hour):
    if start_hour > end_hour:
        raise ValidationError(_('Start hour must be before end hour'))
