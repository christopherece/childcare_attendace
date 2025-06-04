from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attendance',
            name='late',
        ),
        migrations.RemoveField(
            model_name='attendance',
            name='late_reason',
        ),
    ]
