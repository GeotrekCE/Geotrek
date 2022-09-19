# Generated by Django 3.2.15 on 2022-09-13 13:42

import django.contrib.gis.db.models.fields
import django.contrib.postgres.indexes
from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zoning', '0100_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='city',
            name='geom',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(spatial_index=False, srid=settings.SRID),
        ),
        migrations.AlterField(
            model_name='district',
            name='geom',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(spatial_index=False, srid=settings.SRID),
        ),
        migrations.AlterField(
            model_name='restrictedarea',
            name='geom',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(spatial_index=False, srid=settings.SRID),
        ),
        migrations.AddIndex(
            model_name='city',
            index=django.contrib.postgres.indexes.GistIndex(fields=['geom'], name='city_geom_gist_idx'),
        ),
        migrations.AddIndex(
            model_name='district',
            index=django.contrib.postgres.indexes.GistIndex(fields=['geom'], name='district_geom_gist_idx'),
        ),
        migrations.AddIndex(
            model_name='restrictedarea',
            index=django.contrib.postgres.indexes.GistIndex(fields=['geom'], name='restrictedarea_geom_gist_idx'),
        ),
    ]