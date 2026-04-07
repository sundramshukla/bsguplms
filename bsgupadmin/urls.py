from django.urls import path
from .views import *

urlpatterns = [
    path('register/', RegisterApi.as_view(), name='user-register'),
    path('login/', LoginApi.as_view(), name='login-api'),
    path('profile/', CreateProfileApi.as_view(), name='profile'),
    path("createcourse/", CourseCreateApi.as_view()),
    path("create-lesson/", CourseLessonApi.as_view())
]