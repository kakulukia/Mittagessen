# Generated by Django 4.1.2 on 2022-11-08 13:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("meals", "0013_alter_day_options_alter_meal_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="meal",
            name="headline",
            field=models.BooleanField(default=False, verbose_name="Wahlessen"),
        ),
    ]
