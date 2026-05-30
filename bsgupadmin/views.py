import random
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from user.models import Enrollment

from .serializer import CourseCreateSerializer, CourseLessonSerializer, ProfileSerializer
from .models import CourseLesson, CourseModel, DynamicField, DynamicForm, FormAnswer, FormResponse, ProfileDetails, UserRegisterModel,Quiz,Question,QuizAttempt,QuizResult,Certificate
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils import timezone
from rest_framework.parsers import (MultiPartParser,FormParser)

from datetime import timedelta

from reportlab.pdfgen import canvas

import os




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
            user = UserRegisterModel.objects.get(
                mobile_number=mobile_number
            )

        except UserRegisterModel.DoesNotExist:

            return Response(
                {
                    "error": "Mobile number not registered"
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        if not user.is_active_student:

            return Response(
                {
                    "success": False,
                    "message": "Your account has been suspended by admin"
                },
                status=status.HTTP_403_FORBIDDEN
            )


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
        



class CreateQuizAPIView(APIView):

    def post(self, request):

        user_id = request.data.get("user_id")

        title = request.data.get("title")

        course_id = request.data.get("course_id")

        total_marks = request.data.get("total_marks")

        passing_marks = request.data.get("passing_marks")

        duration = request.data.get("duration")

        if not user_id:

            return Response({
                "success": False,
                "message": "user_id required"
            })

        try:
            user = UserRegisterModel.objects.get(id=user_id)

        except UserRegisterModel.DoesNotExist:

            return Response({
                "success": False,
                "message": "Invalid user"
            })

        # only admin/superadmin
        if user.role not in ["admin", "superadmin"]:

            return Response({
                "success": False,
                "message": "Only admin or superadmin can create quiz"
            })

        quiz = Quiz.objects.create(

            created_by=user,

            course_id=course_id,

            title=title,

            total_marks=total_marks,

            passing_marks=passing_marks,

            duration=duration
        )

        return Response({

            "success": True,
            "message": "Quiz created successfully",

            "data": {

                "quiz_id": quiz.id,

                "title": quiz.title,

                "total_marks": quiz.total_marks,

                "passing_marks": quiz.passing_marks,

                "duration": quiz.duration
            }

        }, status=status.HTTP_201_CREATED)
    






class CreateQuestionAPIView(APIView):

    def post(self, request):

        data = request.data

        user_id = data.get("user_id")
        quiz_id = data.get("quiz_id")

        # fast required check
        required_fields = [

            "question",

            "option1",
            "option2",
            "option3",
            "option4",

            "correct_answer"
        ]

        for field in required_fields:

            if not data.get(field):

                return Response({

                    "success": False,

                    "message": f"{field} is required"

                }, status=status.HTTP_400_BAD_REQUEST)

        # fast role check
        user = UserRegisterModel.objects.filter(
            id=user_id
        ).only(
            'id',
            'role'
        ).first()

        if not user:

            return Response({

                "success": False,

                "message": "Invalid user"

            }, status=status.HTTP_404_NOT_FOUND)

        # permission check
        if user.role not in ["admin", "superadmin"]:

            return Response({

                "success": False,

                "message": "Permission denied"

            }, status=status.HTTP_403_FORBIDDEN)

        # fast quiz check
        quiz = Quiz.objects.filter(
            id=quiz_id
        ).only('id').first()

        if not quiz:

            return Response({

                "success": False,

                "message": "Quiz not found"

            }, status=status.HTTP_404_NOT_FOUND)

        # fast correct answer validation
        options = {

            data.get("option1"),

            data.get("option2"),

            data.get("option3"),

            data.get("option4")
        }

        if data.get("correct_answer") not in options:

            return Response({

                "success": False,

                "message": "Correct answer must match options"

            }, status=status.HTTP_400_BAD_REQUEST)

        # create question
        question = Question.objects.create(

            quiz_id=quiz.id,

            question=data.get("question"),

            option1=data.get("option1"),

            option2=data.get("option2"),

            option3=data.get("option3"),

            option4=data.get("option4"),

            correct_answer=data.get("correct_answer")
        )

        # ultra fast response
        return Response({

            "success": True,

            "message": "Question added successfully",

            "question_id": question.id

        }, status=status.HTTP_201_CREATED)










# class CreateQuestionAPIView(APIView):

#     def post(self, request):

#         user_id = request.data.get("user_id")

#         if not user_id:

#             return Response({
#                 "success": False,
#                 "message": "user_id required"
#             })

#         try:
#             user = UserRegisterModel.objects.get(id=user_id)

#         except UserRegisterModel.DoesNotExist:

#             return Response({
#                 "success": False,
#                 "message": "Invalid user"
#             })

#         if user.role not in ["admin", "superadmin"]:

#             return Response({
#                 "success": False,
#                 "message": "Only admin/superadmin can add questions"
#             })

#         question = Question.objects.create(

#             quiz_id=request.data.get("quiz_id"),

#             question=request.data.get("question"),

#             option1=request.data.get("option1"),

#             option2=request.data.get("option2"),

#             option3=request.data.get("option3"),

#             option4=request.data.get("option4"),

#             correct_answer=request.data.get("correct_answer")
#         )

#         return Response({

#             "success": True,

#             "message": "Question added successfully",

#             "data": {
#                 "question_id": question.id
#             }

#         })
    
class GetQuizAPIView(APIView):

    def get(self, request):

        quiz_id = request.GET.get("quiz_id")

        try:
            quiz = Quiz.objects.get(id=quiz_id)

        except Quiz.DoesNotExist:

            return Response({
                "success": False,
                "message": "Quiz not found"
            })

        questions = Question.objects.filter(quiz=quiz)

        question_data = []

        for q in questions:

            question_data.append({

                "question_id": q.id,

                "question": q.question,

                "option1": q.option1,

                "option2": q.option2,

                "option3": q.option3,

                "option4": q.option4,
            })

        return Response({

            "success": True,

            "quiz": {

                "quiz_id": quiz.id,

                "title": quiz.title,

                "total_marks": quiz.total_marks,

                "passing_marks": quiz.passing_marks,

                "duration": quiz.duration
            },

            "questions": question_data
        })
    


class StartQuizAPIView(APIView):

    def post(self, request):

        user_id = request.data.get("user_id")

        quiz_id = request.data.get("quiz_id")

        if not user_id or not quiz_id:

            return Response({
                "success": False,
                "message": "user_id and quiz_id required"
            })

        try:
            quiz = Quiz.objects.get(id=quiz_id)

        except Quiz.DoesNotExist:

            return Response({
                "success": False,
                "message": "Quiz not found"
            })

        # already started
        existing_attempt = QuizAttempt.objects.filter(
            user_id=user_id,
            quiz=quiz
        ).first()

        if existing_attempt:

            return Response({
                "success": False,
                "message": "Quiz already started"
            })

        attempt = QuizAttempt.objects.create(

            user_id=user_id,

            quiz=quiz
        )

        end_time = (
            attempt.started_at +
            timedelta(minutes=quiz.duration)
        )

        return Response({

            "success": True,

            "message": "Quiz started",

            "data": {

                "quiz_id": quiz.id,

                "title": quiz.title,

                "duration_minutes": quiz.duration,

                "started_at": attempt.started_at,

                "end_time": end_time
            }

        })
    













    
from threading import Thread

from django.db.models import F, Count

class SubmitQuizAPIView(APIView):

    # background email sender
    def send_certificate_email(
        self,
        profile,
        student_name,
        pdf_path
    ):

        try:

            email = EmailMessage(

                subject="Course Completion Certificate",

                body=f"""
Congratulations {student_name}

You have successfully completed the course.

Certificate attached.
                """,

                from_email=settings.EMAIL_HOST_USER,

                to=[profile.email]
            )

            email.attach_file(pdf_path)

            email.send()

        except Exception as e:

            print("Email Error:", e)

    def post(self, request):

        user_id = request.data.get("user_id")

        quiz_id = request.data.get("quiz_id")

        answers = request.data.get("answers")

        # validation
        if not user_id or not quiz_id or not answers:

            return Response({

                "success": False,

                "message": "user_id, quiz_id and answers required"

            }, status=status.HTTP_400_BAD_REQUEST)

        # quiz fetch
        try:

            quiz = Quiz.objects.select_related(
                'course'
            ).get(id=quiz_id)

        except Quiz.DoesNotExist:

            return Response({

                "success": False,

                "message": "Quiz not found"

            }, status=status.HTTP_404_NOT_FOUND)

        # attempt check
        try:

            attempt = QuizAttempt.objects.get(

                user_id=user_id,

                quiz_id=quiz_id
            )

        except QuizAttempt.DoesNotExist:

            return Response({

                "success": False,

                "message": "Please start quiz first"

            }, status=status.HTTP_404_NOT_FOUND)

        # already submitted
        if attempt.submitted:

            return Response({

                "success": False,

                "message": "Quiz already submitted"

            }, status=status.HTTP_400_BAD_REQUEST)

        # timing check
        quiz_end_time = (

            attempt.started_at +

            timedelta(minutes=quiz.duration)
        )

        if timezone.now() > quiz_end_time:

            attempt.submitted = True

            attempt.save(update_fields=['submitted'])

            return Response({

                "success": False,

                "message": "Quiz time is over"

            }, status=status.HTTP_400_BAD_REQUEST)

        # fetch questions
        questions = Question.objects.filter(
            quiz_id=quiz_id
        )

        total_questions = questions.count()

        if total_questions == 0:

            return Response({

                "success": False,

                "message": "No questions found"

            }, status=status.HTTP_404_NOT_FOUND)

        # fast lookup dictionary
        question_map = {

            q.id: q.correct_answer
            for q in questions
        }

        correct_answers = 0

        # answer checking
        for ans in answers:

            question_id = ans.get("question_id")

            selected_answer = ans.get("answer")

            correct_answer = question_map.get(
                question_id
            )

            if correct_answer == selected_answer:

                correct_answers += 1

        # marks calculation
        marks_per_question = (

            quiz.total_marks / total_questions
        )

        obtained_marks = (

            correct_answers *
            marks_per_question
        )

        percentage = (

            obtained_marks / quiz.total_marks
        ) * 100

        passed = (

            percentage >= quiz.passing_marks
        )

        # save result
        QuizResult.objects.create(

            user_id=user_id,

            quiz_id=quiz_id,

            total_questions=total_questions,

            correct_answers=correct_answers,

            obtained_marks=obtained_marks,

            percentage=percentage,

            passed=passed
        )

        # update attempt
        attempt.submitted = True

        attempt.save(update_fields=['submitted'])

        # default response
        response_data = {

            "success": True,

            "message": "Quiz submitted successfully",

            "data": {

                "total_questions": total_questions,

                "correct_answers": correct_answers,

                "obtained_marks": obtained_marks,

                "total_marks": quiz.total_marks,

                "percentage": percentage,

                "passed": passed,

                "certificate": None
            }
        }

        # certificate generation
        if passed:

            try:

                profile = ProfileDetails.objects.only(

                    'full_name',
                    'email'

                ).filter(
                    user_id=user_id
                ).first()

                student_name = (

                    profile.full_name
                    if profile else "Student"
                )

                course = quiz.course

                # create certificate folder
                certificate_dir = os.path.join(

                    settings.MEDIA_ROOT,

                    "certificates"
                )

                os.makedirs(

                    certificate_dir,

                    exist_ok=True
                )

                # pdf name
                pdf_name = (

                    f"certificate_{user_id}_{course.id}.pdf"
                )

                pdf_path = os.path.join(

                    certificate_dir,

                    pdf_name
                )

                # generate pdf
                c = canvas.Canvas(pdf_path)

                c.setFont(
                    "Helvetica-Bold",
                    30
                )

                c.drawString(
                    180,
                    750,
                    "CERTIFICATE"
                )

                c.setFont(
                    "Helvetica",
                    18
                )

                c.drawString(
                    80,
                    680,
                    "This certificate is awarded to"
                )

                c.setFont(
                    "Helvetica-Bold",
                    24
                )

                c.drawString(
                    80,
                    640,
                    student_name
                )

                c.setFont(
                    "Helvetica",
                    18
                )

                c.drawString(
                    80,
                    580,
                    "For successfully completing"
                )

                c.drawString(
                    80,
                    540,
                    course.title
                )

                c.drawString(
                    80,
                    480,
                    f"Score : {percentage}%"
                )

                c.save()

                # save certificate
                certificate = Certificate.objects.create(

                    user_id=user_id,

                    course_id=course.id,

                    certificate_file=f"certificates/{pdf_name}"
                )

                # certificate url
                certificate_url = request.build_absolute_uri(
                    certificate.certificate_file.url
                )

                # add certificate url in response
                response_data["data"]["certificate"] = (
                    certificate_url
                )

                # send email in background
                if profile and profile.email:

                    Thread(

                        target=self.send_certificate_email,

                        args=(
                            profile,
                            student_name,
                            pdf_path
                        )

                    ).start()

            except Exception as e:

                print("Certificate Error:", e)

        return Response(

            response_data,

            status=status.HTTP_200_OK
        )



# ================================
# DASHBOARD SUMMARY API
# ================================

class AdminDashboardAPIView(APIView):

    def get(self, request):

        user_id = request.GET.get("user_id")

        if not user_id:
            return Response(
                {
                    "success": False,
                    "message": "user_id is required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            admin_user = UserRegisterModel.objects.get(id=user_id)

        except UserRegisterModel.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Admin not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if admin_user.role not in ["admin", "superadmin"]:
            return Response(
                {
                    "success": False,
                    "message": "Unauthorized access"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        total_students = UserRegisterModel.objects.filter(
            role="student"
        ).count()

        enrolled_students = Enrollment.objects.values(
            "user"
        ).distinct().count()

        total_courses = CourseModel.objects.count()

        total_lessons = CourseLesson.objects.count()

        completion_rate = (
            round((enrolled_students / total_students) * 100, 2)
            if total_students > 0 else 0
        )

        total_revenue = 0

        return Response(
            {
                "success": True,
                "data": {
                    "registered_students": total_students,
                    "enrolled_students": enrolled_students,
                    "total_courses": total_courses,
                    "total_lessons": total_lessons,
                    "completion_rate": completion_rate,
                    "total_revenue": total_revenue
                }
            },
            status=status.HTTP_200_OK
        )


# ================================
# ENROLLMENT BY DEPARTMENT API
# ================================

class EnrollmentByDepartmentAPIView(APIView):

    def get(self, request):

        user_id = request.GET.get("user_id")

        if not user_id:
            return Response(
                {
                    "success": False,
                    "message": "user_id is required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            admin_user = UserRegisterModel.objects.get(id=user_id)

        except UserRegisterModel.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Admin not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if admin_user.role not in ["admin", "superadmin"]:
            return Response(
                {
                    "success": False,
                    "message": "Unauthorized access"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        department_data = (
            Enrollment.objects
            .values("course__department")
            .annotate(total_students=Count("id"))
        )

        data = []

        for item in department_data:

            data.append({
                "department": item["course__department"],
                "total_students": item["total_students"]
            })

        return Response(
            {
                "success": True,
                "data": data
            },
            status=status.HTTP_200_OK
        )


# ================================
# RECENT ENROLLMENTS API
# ================================
class RecentEnrollmentsAPIView(APIView):

    def get(self, request):

        user_id = request.GET.get("user_id")

        if not user_id:
            return Response(
                {
                    "success": False,
                    "message": "user_id is required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        admin_exists = UserRegisterModel.objects.filter(
            id=user_id,
            role__in=["admin", "superadmin"]
        ).exists()

        if not admin_exists:
            return Response(
                {
                    "success": False,
                    "message": "Unauthorized access"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        recent_enrollments = (
            Enrollment.objects
            .select_related("user", "course")
            .prefetch_related("user__profile")
            .order_by("-enrolled_at")[:10]
        )

        data = [
            {
                "student_id": enrollment.user.id,
                "student_name": (
                    enrollment.user.profile.first().full_name
                    if enrollment.user.profile.exists()
                    else None
                ),
                "mobile_number": enrollment.user.mobile_number,
                "course_name": enrollment.course.title,
                "enrollment_date": enrollment.enrolled_at.date(),
                "status": "Active"
            }
            for enrollment in recent_enrollments
        ]

        return Response(
            {
                "success": True,
                "data": data
            },
            status=status.HTTP_200_OK
        )



from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

@method_decorator(csrf_exempt, name='dispatch')
class ToggleStudentStatusAPIView(APIView):

    def post(self, request):

        user_id = request.data.get("user_id")
        student_id = request.data.get("student_id")

        admin_exists = UserRegisterModel.objects.filter(
            id=user_id,
            role__in=["admin", "superadmin"]
        ).exists()

        if not admin_exists:
            return Response(
                {
                    "success": False,
                    "message": "Unauthorized"
                },
                status=403
            )

        try:
            student = UserRegisterModel.objects.get(
                id=student_id,
                role="student"
            )

        except UserRegisterModel.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Student not found"
                },
                status=404
            )

        student.is_active_student = not student.is_active_student
        student.save()

        return Response(
            {
                "success": True,
                "is_active_student": student.is_active_student
            }
        )
    

class CreateDynamicFormAPIView(APIView):

    def post(self, request):

        admin_id = request.data.get("admin_id")

        title = request.data.get("title")

        description = request.data.get("description")

        fields = request.data.get("fields", [])

        admin_exists = UserRegisterModel.objects.filter(
            id=admin_id,
            role__in=["admin", "superadmin"]
        ).exists()

        if not admin_exists:

            return Response(
                {
                    "success": False,
                    "message": "Unauthorized"
                },
                status=403
            )

        form = DynamicForm.objects.create(
            title=title,
            description=description,
            created_by_id=admin_id
        )

        for index, field in enumerate(fields):

            DynamicField.objects.create(
                form=form,
                label=field.get("label"),
                field_type=field.get("field_type"),
                required=field.get("required", False),
                options=",".join(
                    field.get("options", [])
                ),
                order=index
            )

        return Response(
            {
                "success": True,
                "form_id": form.id
            }
        )
    



class GetDynamicFormAPIView(APIView):

    def get(self, request, form_id):

        try:
            form = DynamicForm.objects.get(
                id=form_id,
                is_active=True
            )

        except DynamicForm.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Form not found"
                },
                status=404
            )

        fields = DynamicField.objects.filter(
            form=form
        ).order_by("order")

        data = []

        for field in fields:

            data.append({
                "id": field.id,
                "label": field.label,
                "field_type": field.field_type,
                "required": field.required,
                "options": (
                    field.options.split(",")
                    if field.options else []
                )
            })

        return Response(
            {
                "success": True,
                "form": {
                    "id": form.id,
                    "title": form.title,
                    "description": form.description,
                    "fields": data
                }
            }
        )
    


class SubmitDynamicFormAPIView(APIView):

    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):

        form_id = request.data.get("form_id")

        user_id = request.data.get("user_id")

        answers = json.loads(
            request.data.get("answers", "[]")
        )

        response = FormResponse.objects.create(
            form_id=form_id,
            submitted_by_id=user_id
        )

        for item in answers:

            field_id = item.get("field_id")

            answer = item.get("answer")

            FormAnswer.objects.create(
                response=response,
                field_id=field_id,
                answer_text=answer
            )

        return Response(
            {
                "success": True,
                "message": "Form submitted successfully"
            }
        )
    


class GetFormResponsesAPIView(APIView):

    def get(self, request):

        form_id = request.query_params.get("form_id")

        if not form_id:

            return Response(
                {
                    "success": False,
                    "message": "form_id is required"
                },
                status=400
            )

        responses = (
            FormResponse.objects
            .filter(form_id=form_id)
            .prefetch_related(
                "answers__field"
            )
        )

        data = []

        for response in responses:

            answers = []

            for ans in response.answers.all():

                answers.append({
                    "question": ans.field.label,
                    "answer": ans.answer_text,
                    "file": (
                        ans.uploaded_file.url
                        if ans.uploaded_file
                        else None
                    )
                })

            data.append({
                "student_id": response.submitted_by.id,
                "submitted_at": response.submitted_at,
                "answers": answers
            })

        return Response(
            {
                "success": True,
                "data": data
            }
        )