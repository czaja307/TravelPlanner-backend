# Generated by Django 5.0.6 on 2024-06-17 10:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_visit_geometry'),
    ]

    operations = [
        migrations.AddField(
            model_name='itinerary',
            name='destination',
            field=models.CharField(default='Kaczka', max_length=100),
            preserve_default=False,
        ),
    ]
