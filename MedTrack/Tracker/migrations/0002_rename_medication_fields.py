from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("Tracker", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="medication",
            old_name="dosage",
            new_name="dose",
        ),
        migrations.RenameField(
            model_name="medication",
            old_name="frequency",
            new_name="how_often",
        ),
    ]
