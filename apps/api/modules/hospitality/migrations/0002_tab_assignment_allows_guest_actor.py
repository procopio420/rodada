# A guest can originate an occupancy assignment, but is not a StaffMember.
# Staff-created assignments continue to retain their actor in this field; guest
# provenance is recorded by GuestSession/audit instead of fabricating staff.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hospitality", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="taboccupancyassignment",
            name="assigned_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="tab_occupancy_assignments",
                to="access.staffmember",
            ),
        ),
    ]
