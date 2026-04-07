from django.db import models


class UserRegisterModel(models.Model):
    mobile_number = models.CharField(max_length=15, unique=True)
    password = models.CharField(max_length=100)
    ROLE_CHOICES = (
        ("student", "student"),
        ("admin", "Admin"),
        ("superadmin", "Super Admin")
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="student")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.mobile_number
    

class ProfileDetails(models.Model):
    user = models.ForeignKey(
        UserRegisterModel,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    full_name = models.CharField(max_length=200)
    email = models.EmailField(max_length=50)
    date_of_birth = models.CharField(max_length=15)
    gender = models.CharField(
        max_length=10,
        choices=(
            ("male", "Male"),
            ("female", "Female"),
            ("other", "Other")
        )
    )
    address = models.TextField(max_length=200)
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=200)
    pincode = models.CharField(max_length=200)
    profile_image = models.ImageField(upload_to="profiles/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.full_name


from django.db import models


class CourseModel(models.Model):
    user = models.ForeignKey(
        UserRegisterModel,
        on_delete=models.CASCADE,
    )
    DEPARTMENT_CHOICES = (
        ("organisation", "Organization"),
        ("training", "Training"),
        ("it", "IT"),
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.CharField(max_length=100)
    department = models.CharField(
        max_length=20,
        choices=DEPARTMENT_CHOICES,
        default="training"
    )
    course_profile_pic = models.ImageField(
        upload_to='course_pic/',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    

class CourseLesson(models.Model):

    course = models.ForeignKey(
        CourseModel,
        on_delete=models.CASCADE,
        related_name="lessons"
    )

    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    youtube_url = models.URLField()
    order = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
