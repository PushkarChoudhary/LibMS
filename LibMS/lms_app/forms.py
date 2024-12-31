from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, Book, BookTransaction, BorrowRequest
from django.contrib.auth.forms import AuthenticationForm

from django.contrib.auth import authenticate

from datetime import date, time
import uuid
import random
import string




# Registration Form
class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    phone = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={'placeholder': 'Phone'}))
    gender = forms.ChoiceField(choices=CustomUser.GENDER_CHOICES, required=True, widget=forms.Select())
    pid = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'placeholder': 'Personal ID'}))
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}),
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone', 'gender', 'pid', 'password1', 'password2']

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            # Check if username is email or phone
            if '@' in username:  # Assume it's an email
                user_cache = CustomUser.objects.filter(email=username).first()
            else:  # Assume it's a phone number
                user_cache = CustomUser.objects.filter(phone=username).first()

            # Authenticate using the correct identifier
            if user_cache:
                self.user_cache = authenticate(self.request, username=user_cache.email, password=password)
            else:
                self.user_cache = None

            if self.user_cache is None:
                raise forms.ValidationError("Invalid email/phone or password.")
            elif not self.user_cache.is_active:
                raise forms.ValidationError("This account is inactive.")

        return self.cleaned_data

    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.set_password(self.cleaned_data["password1"])  # Hash the password
        user.is_staff = False  # Not mark the user as staff
        user.is_superuser = False  # Ensure the user is not a superuser
        if commit:
            user.save()
        return user


# Login Form
class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Email or Phone", widget=forms.TextInput(attrs={'placeholder': 'Email or Phone'}))
    password = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError("Invalid email/phone or password.")
            elif not self.user_cache.is_active:
                raise forms.ValidationError("This account is inactive.")

        return self.cleaned_data



# Book Form
class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'quantity', 'fee_per_day']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Book Title'}),
            'author': forms.TextInput(attrs={'placeholder': 'Author'}),
            'quantity': forms.NumberInput(attrs={'placeholder': 'Quantity'}),
            'fee_per_day': forms.NumberInput(attrs={'placeholder': 'Fee per Day'}),
        }


# BookTransaction Form
class BookTransactionForm(forms.ModelForm):
    class Meta:
        model = BookTransaction
        fields = ['address']
        widgets = {
            'address': forms.Textarea(attrs={'placeholder': 'Address', 'rows': 3}),
        }


# Book Search Form
class BookSearchForm(forms.Form):
    title = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Search by Title'}))
    author = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Search by Author'}))

# Borrow Request Form
class BorrowRequestForm(forms.ModelForm):
    borrow_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date', 
            'min': date.today().isoformat()
        }),
        initial=date.today,
        required=True
    )
    return_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True
    )
    receipt_id = forms.CharField(
        max_length=12,
        required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    class Meta:
        model = BorrowRequest
        fields = ['user', 'book', 'borrow_date', 'return_date', 'fine', 'receipt_id']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure receipt_id is set during form initialization
        if not self.instance.receipt_id:
            self.instance.receipt_id = self.generate_unique_receipt_id()
        self.fields['receipt_id'].initial = self.instance.receipt_id

    def clean_receipt_id(self):
        receipt_id = self.cleaned_data.get('receipt_id')

        # If the receipt ID is not provided, use the instance's receipt ID
        if not receipt_id:
            receipt_id = self.instance.receipt_id
        return receipt_id

    def clean(self):
        cleaned_data = super().clean()
        borrow_date = cleaned_data.get('borrow_date')
        return_date = cleaned_data.get('return_date')

        # Ensure borrow_date is not in the past
        if borrow_date and borrow_date < date.today():
            raise forms.ValidationError("Borrow date cannot be in the past.")

        # Validate return_date is after borrow_date
        if borrow_date and return_date and borrow_date > return_date:
            raise forms.ValidationError("Return date cannot be earlier than borrow date.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Set the receipt ID
        instance.receipt_id = self.cleaned_data.get('receipt_id', self.instance.receipt_id)

        if commit:
            instance.save()
        return instance

    def generate_unique_receipt_id(self):
        # Generate a random 6-character string
        while True:
            receipt_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            # Ensure the ID is unique in the database
            if not BorrowRequest.objects.filter(receipt_id=receipt_id).exists():
                return receipt_id



# class CustomLoginForm(forms.Form):
#     identifier = forms.CharField(
#         max_length=150,
#         widget=forms.TextInput(attrs={'placeholder': 'Email or Phone'}),
#         help_text="Enter your email or phone number."
#     )
#     password = forms.CharField(
#         widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
#         help_text="Enter your password."
#     )

#     def __init__(self, *args, **kwargs):
#         self.user = None  # To store the authenticated user
#         super().__init__(*args, **kwargs)

#     def clean(self):
#         cleaned_data = super().clean()
#         identifier = cleaned_data.get('identifier')
#         password = cleaned_data.get('password')

#         if identifier and password:
#             # Try to authenticate the user
#             self.user = authenticate(identifier=identifier, password=password)
#             if not self.user:
#                 raise forms.ValidationError("Invalid email/phone or password.")
#         return cleaned_data

#     def get_user(self):
#         """Return the authenticated user."""
#         return self.user