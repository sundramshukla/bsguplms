import random
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from .serializer import CourseCreateSerializer, CourseLessonSerializer, ProfileSerializer
from .models import CourseLesson, CourseModel, ProfileDetails, UserRegisterModel
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken



# Create your views here.
class RegisterApi(APIView):
    def get(self, request):
        mobile_number = request.query_params.get('mobile_number')
        role=request.query_params.get('role')

        if not mobile_number or not role:
            return Response({"error": "Mobile number and role are required"}, status=status.HTTP_400_BAD_REQUEST)

        if UserRegisterModel.objects.filter(mobile_number=mobile_number).exists():
            return Response({"error": "Mobile number already exists"}, status=status.HTTP_400_BAD_REQUEST)
        otp = random.randint(100000, 999999)
        cache.set(f"otp_{mobile_number}", otp, timeout=300)  # OTP valid for 5 minutes
        return Response({"message": "OTP sent successfully", "otp": otp}, status=status.HTTP_200_OK)

    def post(self, request):
        mobile_number = request.data.get('mobile_number')
        role=request.data.get('role')
        otp = request.data.get('otp')

        if not mobile_number or not otp or not role:
            return Response({"error": "Mobile number and OTP and role are required"}, status=status.HTTP_400_BAD_REQUEST)

        cached_otp = cache.get(f"otp_{mobile_number}")
        if not cached_otp or str(cached_otp) != str(otp):
            return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)

        if UserRegisterModel.objects.filter(mobile_number=mobile_number).exists():
            return Response({"error": "Mobile number already registered"}, status=status.HTTP_400_BAD_REQUEST)


        UserRegisterModel.objects.create(
            mobile_number=mobile_number,
            role=role
        )

        # Clear cache after successful registration
        cache.delete(f"otp_{mobile_number}")

        return Response({"message": "User Registered Successfully"}, status=status.HTTP_201_CREATED)



class LoginApi(APIView):
    def get(self, request):
        mobile_number = request.query_params.get('mobile_number')

        if not mobile_number:
            return Response({"error": "Mobile number is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = UserRegisterModel.objects.get(mobile_number=mobile_number)
        except UserRegisterModel.DoesNotExist:
            return Response({"error": "Mobile number not registered"}, status=status.HTTP_400_BAD_REQUEST)

        # Generate OTP (6-digit)
        otp = random.randint(100000, 999999)

        # Store OTP in cache (valid for 5 minutes)
        cache.set(f"otp_{mobile_number}", otp, timeout=300)

        return Response({"message": "OTP sent successfully", "otp": otp}, status=status.HTTP_200_OK)

    def post(self, request):
        mobile_number = request.data.get('mobile_number')
        otp = request.data.get('otp')

        if not mobile_number:
            return Response({"error": "Mobile number is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            super_admin = UserRegisterModel.objects.get(mobile_number=mobile_number)
        except UserRegisterModel.DoesNotExist:
            return Response({"error": "Invalid mobile number"}, status=status.HTTP_400_BAD_REQUEST)

        def generate_tokens(user):
            refresh = RefreshToken()
            refresh['mobile_number'] = user.mobile_number
            refresh['user_type'] = user.role
            refresh['user_id'] = user.id

            access = refresh.access_token
            return {
                'refresh': str(refresh),
                'access': str(access)
            }


        # ✅ OTP Login
        if otp:
            otp_stored = cache.get(f"otp_{mobile_number}")
            if otp_stored and int(otp) == otp_stored:
                cache.delete(f"otp_{mobile_number}")
                tokens = generate_tokens(super_admin)
                return Response({
                    "message": "Login successful via OTP",
                    "tokens": tokens
                }, status=status.HTTP_200_OK)
            return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error": "Either OTP or password is required"}, status=status.HTTP_400_BAD_REQUEST) 


    


class CreateProfileApi(APIView):

    def get(self, request):
        user_id = request.query_params.get("user_id")

        if not user_id:
            return Response({"error": "user_id is required"}, status=400)

        try:
            profile = ProfileDetails.objects.get(user_id=user_id)
            serializer = ProfileSerializer(profile)

            return Response({
                "Success": "Profile fetched successfully",
                "data": serializer.data
            })

        except ProfileDetails.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)


    def post(self, request):
        user_id = request.data.get("user")

        if not user_id:
            return Response({"error": "user id is required"}, status=400)

        if ProfileDetails.objects.filter(user_id=user_id).exists():
            return Response(
                {"error": "Profile already exists for this user"},
                status=400
            )

        serializer = ProfileSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "Success": "Profile created successfully",
                "data": serializer.data
            })

        return Response(serializer.errors, status=400)


    # ✅ PUT (Update Profile)
    def put(self, request):
        user_id = request.data.get("user")

        if not user_id:
            return Response({"error": "user id is required"}, status=400)

        try:
            profile = ProfileDetails.objects.get(user_id=user_id)
        except ProfileDetails.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)

        serializer = ProfileSerializer(profile, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "Success": "Profile updated successfully",
                "data": serializer.data
            })

        return Response(serializer.errors, status=400)


    # ✅ DELETE Profile
    def delete(self, request):
        user_id = request.query_params.get("user")

        if not user_id:
            return Response({"error": "user_id is required"}, status=400)

        try:
            profile = ProfileDetails.objects.get(user_id=user_id)
            profile.delete()

            return Response({
                "Success": "Profile deleted successfully"
            })

        except ProfileDetails.DoesNotExist:
            return Response({"error": "Profile not found"}, status=404)
    




class CourseCreateApi(APIView):

    def post(self, request):

        # =========================
        # USER ID CHECK
        # =========================

        user_id = request.data.get("user")

        if not user_id:
            return Response({
                "error": "User ID is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        # =========================
        # USER FIND
        # =========================

        user = UserRegisterModel.objects.filter(
            id=user_id
        ).first()

        if not user:
            return Response({
                "error": "User not found"
            }, status=status.HTTP_404_NOT_FOUND)

        # =========================
        # ROLE CHECK
        # =========================

        if user.role not in ["admin", "superadmin"]:

            return Response({
                "error": "Permission denied. Only admin can create course"
            }, status=status.HTTP_403_FORBIDDEN)

        # =========================
        # GET DATA
        # =========================

        title = request.data.get("title", "").strip()
        description = request.data.get("description", "").strip()
        duration = request.data.get("duration", "").strip()

        # =========================
        # REQUIRED FIELD CHECK
        # =========================

        if not title:
            return Response({
                "error": "Course title is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        if not description:
            return Response({
                "error": "Description is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        if not duration:
            return Response({
                "error": "Duration is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        # =========================
        # DUPLICATE CHECK
        # =========================

        existing_course = CourseModel.objects.filter(
            title__iexact=title,
            description__iexact=description,
            duration__iexact=duration
        ).exists()

        if existing_course:

            return Response({
                "error": "Same course already exists"
            }, status=status.HTTP_400_BAD_REQUEST)

        # =========================
        # SERIALIZER
        # =========================

        serializer = CourseCreateSerializer(
            data=request.data
        )

        # =========================
        # VALIDATION
        # =========================

        if serializer.is_valid():

            serializer.save(user=user)

            return Response({
                "success": "Course created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        # =========================
        # VALIDATION ERROR
        # =========================

        return Response({
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)



# class CourseCreateApi(APIView):

#     # CREATE COURSE
# # CREATE COURSE# CREATE COURSE and 
#     def post(self, request):

#         title = request.data.get("title", "").strip()
#         description = request.data.get("description", "").strip()
#         duration = request.data.get("duration", "").strip()

#         # duplicate check
#         existing = CourseModel.objects.filter(
#             title__iexact=title,
#             description__iexact=description,
#             duration__iexact=duration
#         )

#         if existing.exists():
#             return Response({
#                 "error": "Same course already exists"
#             }, status=400)

#         serializer = CourseCreateSerializer(data=request.data)

#         if serializer.is_valid():
#             serializer.save()

#             return Response({
#                 "success": "Course created successfully",
#                 "data": serializer.data
#             }, status=201)

#         return Response({
#             "error": serializer.errors
#         }, status=400)


    # LIST ALL COURSES
    def get(self, request):

        courses = CourseModel.objects.all().order_by("-id")

        serializer = CourseCreateSerializer(courses, many=True)

        return Response({
            "success": "Courses fetched successfully",
            "count": len(serializer.data),
            "data": serializer.data
        }, status=200)


    # UPDATE COURSE
    def put(self, request):

        course_id = request.data.get("course_id")

        if not course_id:
            return Response({
                "error": "Course ID is required"
            }, status=400)

        try:
            course = CourseModel.objects.get(id=course_id)
        except CourseModel.DoesNotExist:
            return Response({
                "error": "Course not found"
            }, status=404)

        serializer = CourseCreateSerializer(course, data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response({
                "success": "Course updated successfully",
                "data": serializer.data
            })

        return Response({
            "error": serializer.errors
        }, status=400)


    # DELETE COURSE
    def delete(self, request):

        course_id = request.query_params.get("course_id")

        if not course_id:
            return Response({
                "error": "Course ID is required"
            }, status=400)

        try:
            course = CourseModel.objects.get(id=course_id)
            course.delete()

            return Response({
                "success": "Course deleted successfully"
            })

        except CourseModel.DoesNotExist:
            return Response({
                "error": "Course not found"
            }, status=404)
        


class CourseLessonApi(APIView):

    # CREATE LESSON
    def post(self, request):

        serializer = CourseLessonSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response({
                "success": "Lesson created successfully",
                "data": serializer.data
            })

        return Response({
            "error": serializer.errors
        }, status=400)


    # GET LESSONS
    def get(self, request):

        course_id = request.query_params.get("course_id")

        if not course_id:
            return Response({
                "error": "course_id required"
            }, status=400)

        lessons = CourseLesson.objects.filter(
            course_id=course_id
        ).order_by("order")

        serializer = CourseLessonSerializer(lessons, many=True)

        return Response({
            "success": "Lessons fetched successfully",
            "data": serializer.data
        })


    # UPDATE
    def put(self, request):

        lesson_id = request.data.get("id")

        try:
            lesson = CourseLesson.objects.get(id=lesson_id)
        except CourseLesson.DoesNotExist:
            return Response({
                "error": "Lesson not found"
            }, status=404)

        serializer = CourseLessonSerializer(
            lesson,
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()

            return Response({
                "success": "Lesson updated successfully",
                "data": serializer.data
            })

        return Response({"error": serializer.errors})


    # DELETE
    def delete(self, request):

        lesson_id = request.query_params.get("lesson_id")

        try:
            lesson = CourseLesson.objects.get(id=lesson_id)
            lesson.delete()

            return Response({
                "success": "Lesson deleted successfully"
            })

        except CourseLesson.DoesNotExist:
            return Response({
                "error": "Lesson not found"
            }, status=404)