# serializers.py

from rest_framework import serializers
from bsgupadmin.models import UserRegisterModel
from bsgupadmin.models import CourseModel


class CourseModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = CourseModel
        fields = "__all__"


class EnrollCourseSerializer(serializers.ModelSerializer):

    course = CourseModelSerializer(read_only=True)

    class Meta:
        model = UserRegisterModel
        fields = "__all__"