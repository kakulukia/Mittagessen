# Generated by Django 4.0.3 on 2022-04-06 19:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('meals', '0002_week_alter_meal_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='week',
            name='footer',
            field=models.CharField(default='', max_length=300, verbose_name='footer'),
        ),
        migrations.AlterField(
            model_name='week',
            name='headline',
            field=models.CharField(max_length=300, verbose_name='Überschrift'),
        ),
    ]
