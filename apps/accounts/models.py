from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", self.model.Role.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)



class User(AbstractUser):
    class Role(models.TextChoices):
        LEARNER = "learner", "Learner"
        REVIEWER = "reviewer", "Content Reviewer"
        ADMIN = "admin", "Training Admin"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.LEARNER)
    designation = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"