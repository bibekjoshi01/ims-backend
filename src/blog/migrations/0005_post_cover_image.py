# Generated by Django 4.2 on 2024-11-28 16:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0004_alter_post_visibility"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="cover_image",
            field=models.ImageField(
                help_text="Cover image of blog post, Use a ratio of 4:3 for best results.",
                null=True,
                upload_to="",
            ),
        ),
    ]
