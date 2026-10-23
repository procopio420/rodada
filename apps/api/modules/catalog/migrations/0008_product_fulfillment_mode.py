# Generated for Spec 035: preserve existing products' preparation flow.

from typing import ClassVar

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies: ClassVar[list] = [
        ("catalog", "0007_availabilitycommand"),
    ]

    operations: ClassVar[list] = [
        migrations.AddField(
            model_name="product",
            name="fulfillment_mode",
            field=models.CharField(choices=[("PREPARE", "Requires preparation"), ("PICKUP", "Immediate pickup")],
                                   default="PREPARE", max_length=16),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.CheckConstraint(
                condition=models.Q(fulfillment_mode="PREPARE") | models.Q(fulfillment_station="BAR"),
                name="catalog_pickup_only_bar",
            ),
        ),
    ]
