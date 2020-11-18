# Generated by Django 3.1.3 on 2020-11-17 13:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0013_targetportal_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recordsource',
            name='pictogram',
            field=models.FileField(blank=True, max_length=512, null=True, upload_to='upload', verbose_name='Pictogramme'),
        ),
        migrations.AlterField(
            model_name='targetportal',
            name='facebook_image_url',
            field=models.CharField(default='/images/logo-geotrek.png', help_text='Url of the facebook image', max_length=256, verbose_name='Facebook image url'),
        ),
        migrations.AlterField(
            model_name='theme',
            name='pictogram',
            field=models.FileField(max_length=512, null=True, upload_to='upload', verbose_name='Pictogramme'),
        ),
    ]
