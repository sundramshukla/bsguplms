from rest_framework import serializers
from .models import CourseLesson, CourseModel, ProfileDetails, UserRegisterModel


class RegisterSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserRegisterModel
        fields = "__all__"



class ProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProfileDetails
        fields = "__all__"


class CourseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model= CourseModel
        fields= "__all__"

class CourseLessonSerializer(serializers.ModelSerializer):

    class Meta:
        model = CourseLesson
        fields = "__all__"