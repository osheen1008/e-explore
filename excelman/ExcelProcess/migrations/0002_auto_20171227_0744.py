# Generated by Django 2.0 on 2017-12-27 07:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ExcelProcess', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='docfile',
            field=models.FileField(upload_to='excel/'),
        ),
    ]
