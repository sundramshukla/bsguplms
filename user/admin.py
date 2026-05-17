from django.contrib import admin
from .models import Enrollment


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_id_display', 'user_name', 'course', 'enrolled_at']

    def user_id_display(self, obj):
        return obj.user.id
    user_id_display.short_description = 'User ID'

    def user_name(self, obj):
        return obj.user.mobile_number  # agar name field nahi hai to username use karo
