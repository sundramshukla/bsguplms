import random
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from bsgupadmin.serializer import CourseCreateSerializer, CourseLessonSerializer, ProfileSerializer
from bsgupadmin.models import CourseLesson, CourseModel, ProfileDetails, UserRegisterModel
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import EnrollCourseSerializer

from .models import Enrollment

# Create your views here.
class UserCourseApi(APIView):

    def get(self, request):

        course_id = request.query_params.get("course_id")
        department = request.query_params.get("department")

        # both not allowed
        if course_id and department:
            return Response({
                "error": "Provide only one: course_id or department"
            }, status=400)

        # none not allowed
        if not course_id and not department:
            return Response({
                "error": "course_id or department is required"
            }, status=400)

        # ================= SINGLE COURSE =================
        if course_id:
            try:
                course = CourseModel.objects.get(id=course_id)

                serializer = CourseCreateSerializer(course)

                return Response({
                    "success": "Course fetched successfully",
                    "data": serializer.data
                })

            except CourseModel.DoesNotExist:
                return Response({
                    "error": "Course not found"
                }, status=404)

        # ================= DEPARTMENT =================
        if department:

            courses = CourseModel.objects.filter(
                department__iexact=department
            )

            if not courses.exists():
                return Response({
                    "error": "No courses found for this department"
                }, status=404)

            serializer = CourseCreateSerializer(courses, many=True)

            return Response({
                "success": "Courses fetched successfully",
                "count": len(serializer.data),
                "data": serializer.data
            })

class UserCourseLessonApi(APIView):

    def get(self, request):

        course_id = request.query_params.get("course_id")

        lessons = CourseLesson.objects.filter(
            course_id=course_id
        ).order_by("order")

        serializer = CourseLessonSerializer(lessons, many=True)

        return Response({
            "success": "Lessons fetched successfully",
            "data": serializer.data
        })
    


class RegisterAndEnroll(APIView):

    def post(self, request):

        mobile = request.data.get("mobile")
        course_id = request.data.get("course_id")
        otp = request.data.get("otp")

        # =========================
        # STEP 1 -> SEND OTP
        # =========================

        if not otp:

            generated_otp = str(random.randint(100000, 999999))

            request.session["otp"] = generated_otp
            request.session["mobile"] = mobile
            request.session["course_id"] = course_id
            request.session["data"] = request.data

            return Response({
                "success": "OTP sent",
                "otp": generated_otp
            })

        # =========================
        # STEP 2 -> VERIFY OTP
        # =========================

        if otp != request.session.get("otp"):

            return Response({
                "error": "Invalid OTP"
            }, status=400)

        data = request.session.get("data")

        # =========================
        # USER CHECK
        # =========================

        user = UserRegisterModel.objects.filter(
            mobile_number=mobile
        ).first()

        # =========================
        # EXISTING USER
        # =========================

        if user:

            course = CourseModel.objects.get(
                id=course_id
            )

            Enrollment.objects.get_or_create(
                user=user,
                course=course
            )

            return Response({
                "success": "Course enrolled successfully",
                "user_id": user.id,
                "existing_user": True
            })

        # =========================
        # NEW USER CREATE
        # =========================

        user = UserRegisterModel.objects.create(
            mobile_number=mobile
        )

        # =========================
        # PROFILE CREATE
        # =========================

        ProfileDetails.objects.create(

            user=user,

            full_name=data.get("full_name"),
            email=data.get("email"),
            date_of_birth=data.get("date_of_birth"),
            gender=data.get("gender"),
            address=data.get("address"),
            city=data.get("city"),
            state=data.get("state"),
            pincode=data.get("pincode"),
        )

        # =========================
        # ENROLLMENT
        # =========================

        course = CourseModel.objects.get(
            id=course_id
        )

        Enrollment.objects.get_or_create(
            user=user,
            course=course
        )

        return Response({
            "success": "Registered and enrolled successfully",
            "user_id": user.id,
            "existing_user": False
        })

# class RegisterAndEnroll(APIView):

#     def post(self, request):

#         mobile = request.data.get("mobile")
#         course_id = request.data.get("course_id")
#         otp = request.data.get("otp")

#         # step 1 send otp
#         if not otp:
#             generated_otp = "123456"

#             request.session["otp"] = generated_otp
#             request.session["mobile"] = mobile
#             request.session["course_id"] = course_id
#             request.session["data"] = request.data

#             return Response({
#                 "message": "OTP sent"
#             })

#         # step 2 verify otp
#         if otp != request.session.get("otp"):
#             return Response({"error": "Invalid OTP"}, status=400)

#         data = request.session.get("data")

#         # create user
#         user, created = UserRegisterModel.objects.get_or_create(
#             mobile=mobile
#         )

#         # create profile
#         ProfileDetails.objects.update_or_create(
#             user=user,
#             defaults={
#                 "full_name": data.get("full_name"),
#                 "email": data.get("email"),
#                 "date_of_birth": data.get("date_of_birth"),
#                 "gender": data.get("gender"),
#                 "address": data.get("address"),
#                 "city": data.get("city"),
#                 "state": data.get("state"),
#                 "pincode": data.get("pincode"),
#             }
#         )

#         # enroll
#         course = CourseModel.objects.get(id=course_id)

#         Enrollment.objects.get_or_create(
#             user=user,
#             course=course
#         )

#         return Response({
#             "success": "Registered and Enrolled successfully",
#             "user_id": user.id
#         })
    


class DirectEnrollApi(APIView):

    def post(self, request):

        profile_id = request.data.get("profile_id")
        course_id = request.data.get("course_id")

        if not profile_id:
            return Response(
                {"error": "profile_id required"},
                status=400
            )

        if not course_id:
            return Response(
                {"error": "course_id required"},
                status=400
            )

        # ✅ profile check
        try:
            profile = ProfileDetails.objects.get(id=profile_id)
        except ProfileDetails.DoesNotExist:
            return Response({
                "error": "Please complete your profile first"
            }, status=400)

        # user from profile
        user = profile.user

        # course check
        try:
            course = CourseModel.objects.get(id=course_id)
        except CourseModel.DoesNotExist:
            return Response(
                {"error": "Course not found"},
                status=404
            )

        # already enrolled
        if Enrollment.objects.filter(user=user, course=course).exists():
            return Response({
                "message": "Already enrolled"
            })

        # enroll
        Enrollment.objects.create(
            user=user,
            course=course
        )

        return Response({
            "success": "Enrolled successfully"
        })
    





class GetEnrollCourses(APIView):

 def get(self, request):
        user_id = request.GET.get('user_id')

        if not user_id:
            return Response({
                "status": False,
                "message": "user_id is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        enrollments = Enrollment.objects.filter(user_id=user_id)

        if not enrollments.exists():
            return Response({
  
                "success": "No enrolled courses found"
            }, status=status.HTTP_404_NOT_FOUND)

        data = []

        for enroll in enrollments:
            course = enroll.course
            user = enroll.user

            data.append({
                "enrollment_id": enroll.id,
                "enrolled_at": enroll.enrolled_at,

                "user": {
                    "id": user.id,
                    "name": getattr(user, 'name', ''),
                    "email": getattr(user, 'email', ''),
                    "phone": getattr(user, 'phone', ''),
                },

                "course": {
                    "id": course.id,
                    "title": getattr(course, 'title', ''),
                    "description": getattr(course, 'description', ''),
                    "price": getattr(course, 'price', ''),
                    "image": request.build_absolute_uri(course.image.url) if getattr(course, 'image', None) else None,
                }
            })

        return Response({
            "success": "Enrolled courses fetched successfully",
            "data": data
        }, status=status.HTTP_200_OK)