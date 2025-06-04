from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0014_alter_attendance_options_and_more'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        # Fix user fields
        migrations.RunSQL(
            sql="""
            -- Update date_joined if it exists and is NULL
            UPDATE auth_user 
            SET date_joined = CURRENT_TIMESTAMP 
            WHERE date_joined IS NULL;
            """,
        ),
    ]
