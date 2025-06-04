from django.contrib import admin
from django.utils.translation import gettext_lazy as _

# Customize the admin site title
admin.site.site_header = 'Childcare Attendance System'
admin.site.site_title = 'Childcare Attendance System'
admin.site.index_title = 'Welcome to Childcare Attendance System'

# Remove Django Administration text
admin.site.site_url = None

# Set empty site URL to remove "Django administration" link
admin.site.site_url = ''
