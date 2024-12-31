from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now
from django.core.validators import MinValueValidator
from datetime import timedelta
from django.contrib.auth.models import BaseUserManager
import uuid

class CustomUserManager(BaseUserManager):
    """
    Custom manager for CustomUser model.
    """

    def create_user(self, email=None, phone=None, password=None, **extra_fields):
        """
        Create and return a regular user with an email, phone, and password.
        """
        if not email and not phone:
            raise ValueError('The user must have either an email or a phone number.')

        if email:
            email = self.normalize_email(email)
            extra_fields['email'] = email


        if phone:
            extra_fields['phone'] = phone

        # Ensure required fields are provided
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        user = self.model(**extra_fields)
        user.username = email
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, phone=None, password=None, **extra_fields):
        """
        Create and return a superuser with an email, phone, and password.
        """
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email=email, phone=phone, pid= uuid.uuid4().hex[:6].upper(), password=password, **extra_fields)


# Custom User Model
class CustomUser(AbstractUser):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, blank=True, null=True)
    phone = models.CharField(max_length=15, unique=True, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    pid = models.CharField(max_length=20, unique=True)  # Personal ID
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'  # Authentication will use email by default
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone']

    objects = CustomUserManager()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Automatically set the username to the email
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email or self.phone})"

# Book Model
class Book(models.Model):
    title = models.CharField(max_length=255, unique=True)
    isbn = models.CharField(max_length=13)
    author = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    fee_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


# BookTransaction Model
class BookTransaction(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='book_transaction')
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.get_full_name()


# BorrowRequest Model
DEFAULT_GRACE_DAYS = 7  # Grace period in days

class BorrowRequest(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_borrow_requests')  # Changed to ForeignKey
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='book_borrow_requests')
    borrow_date = models.DateField(default=now)
    return_date = models.DateField()    
    fine = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    receipt_id = models.CharField(max_length=12)
    returned = models.BooleanField(default=False)
    issued = models.BooleanField(default=False)

    def calculate_fine(self):
        grace_date = self.borrow_date + timedelta(days=DEFAULT_GRACE_DAYS)
        if self.return_date > grace_date:
            days_overdue = (self.return_date - grace_date).days
            self.fine = days_overdue * self.book.fee_per_day
        else:
            self.fine = 0.0
        self.save()

    def __str__(self):
        return f"{self.user.get_full_name()} borrowed {self.book.title}"

