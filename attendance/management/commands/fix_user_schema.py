from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Fix user schema by setting default values for date_joined and updated_at'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Set default values for date_joined
            cursor.execute("""
                ALTER TABLE auth_user 
                ALTER COLUMN date_joined SET DEFAULT CURRENT_TIMESTAMP;
                UPDATE auth_user 
                SET date_joined = CURRENT_TIMESTAMP 
                WHERE date_joined IS NULL;
            """)
            
            # Set default values for updated_at
            cursor.execute("""
                ALTER TABLE auth_user 
                ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
                UPDATE auth_user 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE updated_at IS NULL;
            """)
            
            self.stdout.write(self.style.SUCCESS('Successfully fixed user schema'))
