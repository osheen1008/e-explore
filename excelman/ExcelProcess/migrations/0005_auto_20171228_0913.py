# Generated by Django 2.0 on 2017-12-28 09:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ExcelProcess', '0004_auto_20171228_0910'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='docfile',
            field=models.FileField(upload_to='documents/%Y/%m/%d/'),
        ),
    ]