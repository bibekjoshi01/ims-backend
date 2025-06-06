# Generated by Django 5.1.4 on 2024-12-23 14:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="organizationsetup",
            name="about_us_en",
        ),
        migrations.RemoveField(
            model_name="organizationsetup",
            name="about_us_fr",
        ),
        migrations.RemoveField(
            model_name="organizationsetup",
            name="cookie_policy_en",
        ),
        migrations.RemoveField(
            model_name="organizationsetup",
            name="cookie_policy_fr",
        ),
        migrations.RemoveField(
            model_name="organizationsetup",
            name="policies_en",
        ),
        migrations.RemoveField(
            model_name="organizationsetup",
            name="policies_fr",
        ),
        migrations.RemoveField(
            model_name="organizationsetup",
            name="privacy_policy_en",
        ),
        migrations.RemoveField(
            model_name="organizationsetup",
            name="privacy_policy_fr",
        ),
        migrations.RemoveField(
            model_name="organizationsetup",
            name="terms_of_use_en",
        ),
        migrations.RemoveField(
            model_name="organizationsetup",
            name="terms_of_use_fr",
        ),
        migrations.AddField(
            model_name="organizationsetup",
            name="cookie_policy",
            field=models.TextField(
                default=1,
                help_text="Cookie Policy of the organization (french)",
                verbose_name="Cookie Policy",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="organizationsetup",
            name="privacy_policy",
            field=models.TextField(
                default=1,
                help_text="Privacy Policy of the organization (english)",
                verbose_name="Privacy Policy",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="organizationsetup",
            name="terms_of_use",
            field=models.TextField(blank=True, verbose_name="Terms of Use"),
        ),
        migrations.AlterField(
            model_name="thirdpartycredential",
            name="gateway",
            field=models.CharField(
                choices=[("GOOGLE", "Google")],
                help_text="Select the payment gateway from the list (e.g., Google, Paypal).",
                max_length=20,
                unique=True,
            ),
        ),
        migrations.DeleteModel(
            name="OrganizationDonationLinks",
        ),
    ]
