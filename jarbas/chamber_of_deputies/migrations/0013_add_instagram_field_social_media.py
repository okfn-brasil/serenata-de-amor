# Generated by Django 2.0.8 on 2019-07-11 08:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chamber_of_deputies', '0012_make_party_field_longer'),
    ]

    operations = [
        migrations.AddField(
            model_name="SocialMedia",
            name="instagram_profile",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
