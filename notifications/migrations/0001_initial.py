from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('attendance', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('child', models.ForeignKey(on_delete=models.CASCADE, to='attendance.child', related_name='notifications')),
                ('parent', models.ForeignKey(on_delete=models.CASCADE, to='attendance.parent', related_name='notifications')),
                ('teacher', models.ForeignKey(on_delete=models.CASCADE, to='attendance.teacher', related_name='notifications')),
                ('center', models.ForeignKey(on_delete=models.CASCADE, to='attendance.center', related_name='notifications')),
            ],
        ),
    ]
