from typing import ClassVar

from django.db import migrations


class Migration(migrations.Migration):
    dependencies: ClassVar = [("documents_printing", "0013_agent_delivery_guards")]
    operations: ClassVar = [
        migrations.RemoveConstraint(
            model_name="agentprinterroute", name="printing_single_active_route"
        ),
    ]
