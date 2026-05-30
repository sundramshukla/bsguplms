from django.urls import path
from .views import *

urlpatterns = [
    path('registerthroughemail/', RegisterThroughEmailAPIView.as_view()),
    path('loginthroughemail/', LoginThroughEmailAPIView.as_view()),
    path('forgetpassword/', ForgotPasswordAPIView.as_view()),
    # path('register/', RegisterApi.as_view(), name='user-register'),
    # path('login/', LoginApi.as_view(), name='login-api'),
    path('profile/', CreateProfileApi.as_view(), name='profile'),
    path("createcourse/", CourseCreateApi.as_view()),
    path("create-lesson/", CourseLessonApi.as_view()),
    path('create-quiz/',CreateQuizAPIView.as_view()),
    path('create-question/',CreateQuestionAPIView.as_view()),
    path('get-quiz/',GetQuizAPIView.as_view()),
    path('start-quiz/',StartQuizAPIView.as_view()),
    path('submit-quiz/',SubmitQuizAPIView.as_view()),
    path('dashboard/', AdminDashboardAPIView.as_view()),
    path('enrollment-by-department/', EnrollmentByDepartmentAPIView.as_view()),
    path('recentenrollment/',RecentEnrollmentsAPIView.as_view()),
    path('student-status-cahnge/', ToggleStudentStatusAPIView.as_view())
]