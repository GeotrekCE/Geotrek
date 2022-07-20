# Generated by Django 3.1.14 on 2022-07-20 16:14

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('authent', '0010_auto_20220720_1613'),
        ('outdoor', '0039_auto_20220304_1442'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='structure',
            field=models.ForeignKey(default=settings.DEFAULT_STRUCTURE_PK, on_delete=django.db.models.deletion.CASCADE, to='authent.structure', verbose_name='Related structure'),
        ),
        migrations.AlterField(
            model_name='site',
            name='structure',
            field=models.ForeignKey(default=settings.DEFAULT_STRUCTURE_PK, on_delete=django.db.models.deletion.CASCADE, to='authent.structure', verbose_name='Related structure'),
        ),
    ]