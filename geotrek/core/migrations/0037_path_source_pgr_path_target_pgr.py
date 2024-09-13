# Generated by Django 4.2.13 on 2024-07-23 10:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0036_auto_20230503_0837'),
    ]

    operations = [
        migrations.AddField(
            model_name='path',
            name='source_pgr',
            field=models.IntegerField(blank=True, db_column='source', editable=False, help_text='Internal field used by pgRouting', null=True),
        ),
        migrations.AddField(
            model_name='path',
            name='target_pgr',
            field=models.IntegerField(blank=True, db_column='target', editable=False, help_text='Internal field used by pgRouting', null=True),
        ),
    ]
