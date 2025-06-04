import os
import shutil
from pathlib import Path

# Define paths
base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
migrations_dir = base_dir / 'attendance' / 'migrations'

# Remove all migration files except __init__.py
for file in migrations_dir.glob('*.py'):
    if file.name != '__init__.py':
        file.unlink()

# Create a fresh initial migration
with open(migrations_dir / '0001_initial.py', 'w') as f:
    f.write("""
from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Center',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('address', models.TextField()),
                ('phone', models.CharField(max_length=20)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('capacity', models.IntegerField()),
                ('opening_time', models.TimeField(default='08:30:00')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Parent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('address', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Child',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('date_of_birth', models.DateField()),
                ('gender', models.CharField(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], max_length=10)),
                ('allergies', models.TextField(blank=True, null=True)),
                ('medical_conditions', models.TextField(blank=True, null=True)),
                ('emergency_contact', models.CharField(max_length=100)),
                ('emergency_phone', models.CharField(max_length=20)),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to='child_pix/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('parent', models.ForeignKey(on_delete=models.CASCADE, related_name='children', to='attendance.parent')),
                ('center', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='children', to='attendance.center')),
            ],
        ),
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sign_in', models.DateTimeField(blank=True, null=True)),
                ('sign_out', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('child', models.ForeignKey(on_delete=models.CASCADE, to='attendance.child')),
                ('parent', models.ForeignKey(on_delete=models.CASCADE, to='attendance.parent')),
                ('center', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to='attendance.center')),
            ],
            options={
                'ordering': ['-sign_in', '-sign_out'],
            },
        ),
    ]
""")

print("Migrations cleaned and recreated successfully!")
