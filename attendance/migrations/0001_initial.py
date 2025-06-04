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
                ('email', models.EmailField(unique=True)),
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
                ('email', models.EmailField(unique=True)),
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
                ('emergency_contact', models.CharField(default='Emergency Contact', max_length=100)),
                ('emergency_phone', models.CharField(default='', max_length=15)),
                ('allergies', models.TextField(blank=True, null=True)),
                ('medical_conditions', models.TextField(blank=True, null=True)),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to='static/images/children/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('center', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='children', to='attendance.center')),
                ('parent', models.ForeignKey(on_delete=models.CASCADE, related_name='children', to='attendance.parent')),
            ],
        ),
        migrations.CreateModel(
            name='Teacher',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.CharField(default='Teacher', max_length=100)),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to='static/images/teachers/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=models.CASCADE, related_name='teacher_profile', to='auth.user')),
                ('center', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='teachers', to='attendance.center')),
            ],
        ),
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sign_in', models.DateTimeField(null=True)),
                ('sign_out', models.DateTimeField(null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('late', models.BooleanField(default=False)),
                ('late_reason', models.CharField(blank=True, max_length=200, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('child', models.ForeignKey(on_delete=models.CASCADE, to='attendance.child')),
                ('parent', models.ForeignKey(on_delete=models.CASCADE, to='attendance.parent')),
                ('center', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, to='attendance.center')),
            ],
        ),
    ]
