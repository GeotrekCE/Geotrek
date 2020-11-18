# Generated by Django 3.1.3 on 2020-11-17 13:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('infrastructure', '0020_auto_20200831_1406'),
    ]

    operations = [
        migrations.AlterField(
            model_name='infrastructure',
            name='publication_date',
            field=models.DateField(blank=True, editable=False, null=True, verbose_name='Date de publication'),
        ),
        migrations.AlterField(
            model_name='infrastructure',
            name='published',
            field=models.BooleanField(default=False, help_text='Visible sur Geotrek-rando', verbose_name='Publié'),
        ),
        migrations.AlterField(
            model_name='infrastructuretype',
            name='pictogram',
            field=models.FileField(blank=True, max_length=512, null=True, upload_to='upload', verbose_name='Pictogramme'),
        ),
    ]
