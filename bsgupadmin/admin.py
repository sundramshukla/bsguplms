from django.contrib import admin
from .models import *


admin.site.register(UserRegisterModel)
admin.site.register(ProfileDetails)
admin.site.register(CourseModel)
admin.site.register(CourseLesson)

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'title',
        'course',
        'created_by',
        'total_marks',
        'passing_marks',
        'duration',
        'created_at'
    )

    search_fields = (
        'title',
        'course__title',
        'created_by__mobile_number'
    )

    list_filter = (
        'created_at',
        'course'
    )


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'quiz',
        'question',
        'correct_answer'
    )

    search_fields = (
        'question',
        'quiz__title'
    )

    list_filter = (
        'quiz',
    )


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'user',
        'quiz',
        'started_at',
        'submitted'
    )

    search_fields = (
        'user__mobile_number',
        'quiz__title'
    )

    list_filter = (
        'submitted',
        'quiz'
    )


@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'user',
        'quiz',
        'correct_answers',
        'obtained_marks',
        'percentage',
        'passed',
        'created_at'
    )

    search_fields = (
        'user__mobile_number',
        'quiz__title'
    )

    list_filter = (
        'passed',
        'quiz'
    )


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'user',
        'course',
        'certificate_file',
        'created_at'
    )

    search_fields = (
        'user__mobile_number',
        'course__title'
    )

    list_filter = (
        'course',
    )