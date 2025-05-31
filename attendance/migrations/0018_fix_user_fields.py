from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            -- Remove any custom created_at field if it exists
            ALTER TABLE auth_user DROP COLUMN IF EXISTS created_at;
            
            -- Add default values for date_joined if it exists
            ALTER TABLE auth_user 
            ALTER COLUMN date_joined SET DEFAULT CURRENT_TIMESTAMP;
            
            -- Update existing records with current timestamp for date_joined
            UPDATE auth_user 
            SET date_joined = CURRENT_TIMESTAMP 
            WHERE date_joined IS NULL;
            
            -- Add default values for updated_at if it exists
            ALTER TABLE auth_user 
            ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
            
            -- Update existing records with current timestamp for updated_at
            UPDATE auth_user 
            SET updated_at = CURRENT_TIMESTAMP 
            WHERE updated_at IS NULL;
            
            -- Ensure all users have a username
            UPDATE auth_user 
            SET username = email 
            WHERE username IS NULL;
            
            -- Ensure all users have an email
            UPDATE auth_user 
            SET email = username || '@example.com' 
            WHERE email IS NULL;
            """,
            reverse_sql="""
            -- Revert changes if needed
            ALTER TABLE auth_user 
            ALTER COLUMN date_joined DROP DEFAULT;
            ALTER TABLE auth_user 
            ALTER COLUMN updated_at DROP DEFAULT;
            """
        ),
    ]
