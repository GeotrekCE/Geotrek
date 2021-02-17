# Generated by Django 3.1.6 on 2021-02-16 14:13

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authent', '0006_auto_20210216_1413'),
        ('core', '0023_auto_20210216_1412'),
    ]

    operations = [
        migrations.AlterField(
            model_name='path',
            name='structure',
            field=models.ForeignKey(default=settings.DEFAULT_STRUCTURE_PK, on_delete=django.db.models.deletion.CASCADE, to='authent.structure', verbose_name='Related structure'),
        ),
        migrations.AlterField(
            model_name='trail',
            name='structure',
            field=models.ForeignKey(default=settings.DEFAULT_STRUCTURE_PK, on_delete=django.db.models.deletion.CASCADE, to='authent.structure', verbose_name='Related structure'),
        ),
    ]