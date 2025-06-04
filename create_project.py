import django
from django.core import management

if __name__ == '__main__':
    management.call_command('startproject', 'temp_project', '.')
