# Generated by Django 2.0.4 on 2018-04-06 13:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("users", "0001_initial")]

    operations = [
        migrations.AlterModelOptions(
            name="user",
            options={
                "base_manager_name": "data",
                "default_manager_name": "data",
                "get_latest_by": "created",
                "ordering": ["-created"],
                "verbose_name": "user",
                "verbose_name_plural": "users",
            },
        )
    ]
