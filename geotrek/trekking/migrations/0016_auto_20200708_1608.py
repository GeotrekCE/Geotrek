# Generated by Django 2.2.14 on 2020-07-08 16:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0012_reservationsystem'),
        ('trekking', '0015_auto_20200406_1412'),
    ]

    operations = [
        migrations.AddField(
            model_name='trek',
            name='reservation_id',
            field=models.CharField(blank=True, max_length=1024, verbose_name='Reservation ID'),
        ),
        migrations.AddField(
            model_name='trek',
            name='reservation_system',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='common.ReservationSystem', verbose_name='Reservation system'),
        ),
    ]
