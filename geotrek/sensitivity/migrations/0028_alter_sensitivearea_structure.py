# Generated by Django 3.2.18 on 2023-04-07 08:15

from django.db import migrations, models
import django.db.models.deletion
import geotrek.authent.models


class Migration(migrations.Migration):

    dependencies = [
        ('authent', '0011_alter_userprofile_structure'),
        ('sensitivity', '0027_auto_20230202_2202'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sensitivearea',
            name='structure',
            field=models.ForeignKey(default=geotrek.authent.models.default_structure_pk, on_delete=django.db.models.deletion.PROTECT, to='authent.structure', verbose_name='Related structure'),
        ),
    ]
