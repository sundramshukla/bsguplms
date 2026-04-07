from django.contrib import admin
from .models import CourseLesson, CourseModel, ProfileDetails, UserRegisterModel


admin.site.register(UserRegisterModel)
admin.site.register(ProfileDetails)
admin.site.register(CourseModel)
admin.site.register(CourseLesson)