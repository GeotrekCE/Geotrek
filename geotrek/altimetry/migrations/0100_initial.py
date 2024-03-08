# Generated by Django 3.2.24 on 2024-03-08 11:23

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    replaces = [
        ('altimetry', '0001_initial'),
        ('altimetry', '0002_import_mnt_data'),
    ]
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Dem",
            fields=[
                (
                    "id",
                    models.AutoField(
                        db_column="rid", primary_key=True, serialize=False
                    ),
                ),
                ("rast", django.contrib.gis.db.models.fields.RasterField(srid=2154)),
            ],
        ),
    ]
