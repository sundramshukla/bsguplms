from django.urls import path
from .views import *

urlpatterns = [
    path('getcoursedetails/', UserCourseApi.as_view()),
    path('enrollwithoutlogin/', RegisterAndEnroll.as_view()),
    path('enrollment/', DirectEnrollApi.as_view()),
    path('getenrollcourses/', GetEnrollCourses.as_view() )
]