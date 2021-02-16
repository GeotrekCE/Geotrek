# Generated by Django 3.1.6 on 2021-02-16 14:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authent', '0006_auto_20210216_1413'),
        ('maintenance', '0016_auto_20210121_0943'),
    ]

    operations = [
        migrations.AlterField(
            model_name='intervention',
            name='structure',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='authent.structure', verbose_name='Related structure'),
        ),
        migrations.AlterField(
            model_name='project',
            name='structure',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='authent.structure', verbose_name='Related structure'),
        ),
    ]
