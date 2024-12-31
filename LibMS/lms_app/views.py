from django.conf import settings
from rest_framework import viewsets, generics, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CustomUser, Book, BookTransaction, BorrowRequest
from .serializers import CustomUserSerializer, BookSerializer, BookTransactionSerializer, BorrowRequestSerializer
from django_filters.rest_framework import DjangoFilterBackend
from .filters import BookFilter
from django.shortcuts import render, redirect
from .forms import *
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_protect
from rest_framework.parsers import MultiPartParser, FormParser
import openpyxl
from rest_framework import status
from django.shortcuts import render, redirect, get_object_or_404
from .forms import BookTransactionForm
from .models import BookTransaction
from django.http import JsonResponse, HttpResponseForbidden
from datetime import timedelta
from django.utils.timezone import now 

from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import uuid

from django.templatetags.static import static
import os
import requests

from django.core.mail import send_mail
from django.contrib import messages
from decouple import config


# Home page
def home_view(request):
    """
    Renders the home page with navigation buttons for all routes.
    """
    return render(request, 'index.html')

# Fetch form to create mutltiple books
def upload_excel_form(request):
    return render(request, 'create_multiple_books.html')

# View to update a book
def update_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == "POST":
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            # return redirect('book_list')  # Adjust this to the name of your book listing page
    else:
        form = BookForm(instance=book)
    return render(request, 'update_book.html', {'form': form, 'book': book})

@login_required
def book_transaction_create_view(request):
    if request.method == 'POST':
        form = BookTransactionForm(request.POST)
        if form.is_valid():
            book_transaction = form.save(commit=False)
            book_transaction.user = request.user
            book_transaction.save()
            return redirect('home')  # Redirect after creation
    else:
        form = BookTransaction()
    return render(request, 'book_transaction_form.html', {'form': form})

@login_required
def book_transaction_update_view(request, pk):
    book_transaction = get_object_or_404(BookTransaction, pk=pk)
    if request.method == 'POST':
        form = BookTransactionForm(request.POST, instance=book_transaction)
        if form.is_valid():
            form.save()
            return redirect('home')  # Redirect after update
    else:
        form = BookTransaction(instance=book_transaction)
    return render(request, 'book_transaction_form.html', {'form': form})

@login_required
def book_transaction_list_view(request, pk):
    book_transactions = BookTransaction.objects.all()  # Fetch all book_transactions from the database
    return render(request, 'book_transaction_list.html', {'book_transactions': book_transactions})


@csrf_protect
def register_view(request):
    if request.method == 'POST':
        # Extract the reCAPTCHA token from the POST data
        recaptcha_token = request.POST.get('g-recaptcha-response')
        
        if not recaptcha_token:
            return JsonResponse({'error': 'ReCAPTCHA token is missing.'}, status=400)
        
        # Verify the reCAPTCHA token with Google's siteverify API
        recaptcha_secret_key = config("RECAPTCHA_SECRET_KEY")  # Make sure this is defined in settings.py
        recaptcha_url = "https://www.google.com/recaptcha/api/siteverify"
        recaptcha_data = {
            'secret': recaptcha_secret_key,
            'response': recaptcha_token
        }
        recaptcha_response = requests.post(recaptcha_url, data=recaptcha_data)
        recaptcha_result = recaptcha_response.json()
        
        # Check if the verification was successful
        if not recaptcha_result.get('success') or recaptcha_result.get('score', 0) < 0.5:
            return JsonResponse({'error': 'ReCAPTCHA verification failed.'}, status=400)
        
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form, 'user': request.user})

@csrf_protect
def login_view(request):
    if request.method == 'POST':
        # Extract the reCAPTCHA token from the POST data
        recaptcha_token = request.POST.get('g-recaptcha-response')
        
        if not recaptcha_token:
            return JsonResponse({'error': 'ReCAPTCHA token is missing.'}, status=400)
        
        # Verify the reCAPTCHA token with Google's siteverify API
        recaptcha_secret_key = config("RECAPTCHA_SECRET_KEY")  # Make sure this is defined in settings.py
        recaptcha_url = "https://www.google.com/recaptcha/api/siteverify"
        recaptcha_data = {
            'secret': recaptcha_secret_key,
            'response': recaptcha_token
        }
        recaptcha_response = requests.post(recaptcha_url, data=recaptcha_data)
        recaptcha_result = recaptcha_response.json()
        
        # Check if the verification was successful
        if not recaptcha_result.get('success') or recaptcha_result.get('score', 0) < 0.5:
            return JsonResponse({'error': 'ReCAPTCHA verification failed.'}, status=400)
        
        # Proceed with authentication
        form = AuthenticationForm(data=request.POST)
        print(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return render(request, 'index.html', {'user': request.user})  # Redirect to homepage after login
        else:
            print(form.errors)
            return JsonResponse({'error': 'Invalid login credentials.'}, status=400)
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required
def logout_confirmation(request):
    return render(request, 'logout_confirm.html')

@login_required
def book_search_view(request):
    books = Book.objects.all()
    already_requested_books_id = BorrowRequest.objects.filter(user=request.user.id, returned=False).values_list('book_id', flat=True)

    form = BookSearchForm(request.GET)
    if form.is_valid():
        title = form.cleaned_data.get('title')
        author = form.cleaned_data.get('author')
        if title:
            books = books.filter(title__icontains=title)
        if author:
            books = books.filter(author__icontains=author)
    return render(request, 'book_search.html', {'form': form, 'books': books, 'already_requested_books_id':already_requested_books_id})

# Book ViewSet
class BookViewSet(LoginRequiredMixin, viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = BookFilter
    login_url = '/login/'
    lookup_value_regex = r'\d+'
    parser_classes = [MultiPartParser, FormParser]  # To handle file uploads

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def bulk_create(self, request):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def upload_excel(self, request):
        """
        Handle file upload and create books from Excel file.
        """
        file = request.FILES.get('file', None)
        if not file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            workbook = openpyxl.load_workbook(file)
            sheet = workbook.active

            books = []
            for row in sheet.iter_rows(min_row=2, values_only=True):  # Assuming the first row contains headers
                title, author, isbn, quantity, fee_per_day = row
                if not title or not author or not quantity or not fee_per_day:
                    continue
                books.append(
                    Book(
                        title=title,
                        author=author,
                        quantity=int(quantity),
                        fee_per_day=float(fee_per_day),
                        isbn=isbn,
                    )
                )

            Book.objects.bulk_create(books)
            return Response({"message": f"{len(books)} books created successfully"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
# Select book and checkout to issue
# Give user editable final checkout page with all details
@login_required
def checkout_view(request):
    if request.method == "POST":
        user = request.user
        book_ids = request.POST.getlist('book_ids')

        receipt_id = uuid.uuid4().hex[:6].upper()

        # Check for receipt already created or not
        if BorrowRequest.objects.filter(receipt_id = receipt_id).exists():
            return JsonResponse({'error': f"Issue request for receipt '{receipt_id}' already exists."}, status=400)

        # Check for book issue request is already submitted by user or not
        already_request_books = []
        for book_id in book_ids:
            book = Book.objects.get(id=book_id)
            borrow_request = BorrowRequest.objects.filter(user=user.id, book=book.id, returned=False)
            if borrow_request.exists():
                already_request_books.append(book_id)

        for book_id in book_ids:
            # Skip if active book request for the book already exist
            if book_id in already_request_books:
                continue

            try:
                book = Book.objects.get(id=book_id)
                if book.quantity > 1:
                    # Create BorrowRequest
                    BorrowRequest.objects.create(
                        user=user,
                        book=book,
                        borrow_date=now(),
                        return_date=now() + timedelta(days=14),  # Example: 14-day return period
                        receipt_id=receipt_id
                    )
                    # Decrement book quantity
                    book.quantity -= 1
                    book.save()
                else:
                    return JsonResponse({'error': f"Book '{book.title}' is out of stock."}, status=400)
            except Book.DoesNotExist:
                return JsonResponse({'error': 'Book not found.'}, status=404)

        return redirect('checkout_receipt', receipt_id)  # Replace with your success URL
    else:
        books = Book.objects.filter(quantity__gt=0)
        return render(request, 'checkout.html', {'books': books})
    
# Give user downloadable checkout receipt
@login_required
def checkout_receipt_view(request, receipt_id):
    try:
        borrow_request = BorrowRequest.objects.filter(user=request.user, receipt_id=receipt_id)[0]
        book_ids = BorrowRequest.objects.filter(user=request.user, receipt_id=receipt_id).values_list('book_id', flat=True)
        books = Book.objects.filter(id__in=book_ids)
    except:
        return JsonResponse({'error': f"No receipt exist with id '{receipt_id}'."}, status=400) 
       
    return render(request, 'checkout_receipt.html', {'receipt_id':receipt_id, 'issued_date':borrow_request.borrow_date, 'return_date':borrow_request.return_date, 'books':books})

# Borrow Request View
class BorrowRequestViewSet(LoginRequiredMixin, viewsets.ModelViewSet):
    queryset = BorrowRequest.objects.all()
    serializer_class = BorrowRequestSerializer
    login_url = '/login/'

    def perform_create(self, serializer):
        # The logic of checking book quantity and saving is now handled in the serializer
        serializer.save()

# views to download a successful checkout receipt
@login_required
def download_receipt_pdf(request, receipt_id):
    # Fetch the BorrowRequest and associated details
    borrow_requests = BorrowRequest.objects.filter(user_id=request.user.id, receipt_id=receipt_id)
    if not borrow_requests:
        return HttpResponse("No such receipt found.", status=404)

    # Prepare the PDF response
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle("Checkout Receipt")

    # Organization Logo
    logo_path = os.path.join(settings.BASE_DIR, 'lms_app/static/images/logo.jpeg')

    # Draw the image on the PDF
    pdf.drawImage(logo_path, 230, 750, width=100, height=50)

    # User Information
    user = request.user
    pdf.drawString(50, 700, f"Name: {user.get_full_name()}")
    pdf.drawString(50, 680, f"Email: {user.email}")
    pdf.drawString(50, 660, f"Issued Date: {borrow_requests.first().borrow_date}")
    pdf.drawString(50, 640, f"Return Date: {borrow_requests.first().return_date}")

    # Book Details Table Header
    y = 600
    pdf.drawString(50, y, "Book Name")
    pdf.drawString(300, y, "ISBN")
    y -= 20
    pdf.line(50, y, 500, y)

    # Add Book Details
    for borrow_request in borrow_requests:
        pdf.drawString(50, y, borrow_request.book.title)
        pdf.drawString(300, y, borrow_request.book.isbn)
        y -= 20

    # Finalize the PDF
    pdf.save()
    buffer.seek(0)

    # Return the PDF as a response
    response = HttpResponse(buffer, content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename="Checkout_Receipt_{receipt_id}.pdf"'
    return response



def is_librarian(user):
    return user.groups.filter(name='librarians').exists() or user.is_staff

def manage_borrow_request(request):
    receipt_id = request.GET.get('receipt_id', '').strip()
    status = request.GET.get('status', '').strip()
    operation = request.GET.get('submit', '').strip()

    borrow_requests = BorrowRequest.objects.all()

    if receipt_id:
        borrow_requests = borrow_requests.filter(receipt_id=receipt_id)

    if status:
        if operation=='search':
            if status=='issued':
                borrow_requests = borrow_requests.filter(issued=True)
            elif status=='returned':
                borrow_requests = borrow_requests.filter(returned=True)
            elif status=='requested':
                borrow_requests = borrow_requests.filter(issued=False, returned=False)
            else:
                borrow_requests = []
        elif operation=='update':
            if status=='issued':
                borrow_requests.update(issued=True)
                borrow_requests = BorrowRequest.objects.all()
            elif status=='returned':
                borrow_requests.update(returned=True)
                for borrow_request in borrow_requests:
                    borrow_request.calculate_fine()
                borrow_requests = BorrowRequest.objects.all()
            else:
                borrow_requests = []

    return render(request, 'manage_borrow_request.html', {'borrow_requests': borrow_requests})

@login_required
@user_passes_test(is_librarian)
def update_single_borrow_request_status(request, id):
    if request.method == 'POST':
        new_status = request.POST.get('status')
         # Get all borrow requests associated with the receipt_id
        borrow_request = BorrowRequest.objects.filter(id=id)
        
        if not borrow_request.exists():
            return JsonResponse({'error': f'No book borrow requests found with id {id}.'}, status=404)
        
        # Update the status of all borrow requests
        if new_status=='issued':
            borrow_request.update(issued=True)
        elif new_status=='returned':
            borrow_request.update(returned=True)
            borrow_request[0].calculate_fine()
        elif new_status=='requested':
            borrow_request.update(returned=False, issued=False)

        return redirect('manage_borrow_request')
    return HttpResponseForbidden("Invalid request method.")


@login_required
@user_passes_test(is_librarian)
def create_borrow_request(request):
    if request.method == 'POST':
        form = BorrowRequestForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            book = form.cleaned_data['book']
            existing_borrow_request = BorrowRequest.objects.filter(user=user.id, book=book.id, returned=False)
            if existing_borrow_request.exists():
                return JsonResponse({'error': f'Book request already exist for this user with receipt id {existing_borrow_request[0].receipt_id}.'}, status=404)
            borrow_request = form.save(commit=False)
            borrow_request.user = user  # Set the user to the currently logged-in user
            borrow_request.save()
            return JsonResponse({'message': 'Borrow request created successfully!'}, status=201)
        else:
            return JsonResponse({'errors': form.errors}, status=400)
    
    # Render the form on a GET request
    form = BorrowRequestForm()
    return render(request, 'create_borrow_request.html', {'form': form})

# Views to fetch extra resources
def about_view(request):
    return render(request, "about.html")

def terms_of_usage(request):
    return render(request, "terms_of_usage.html")

def privacy(request):
    return render(request, "privacy.html")

def contact_us_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        # Combine the message with additional details
        full_message = f"From: {name}\nEmail: {email}\n\nMessage:\n{message}"

        # Send an email (configure your email settings in settings.py)
        try:
            recipient_email = config("EMAIL_RECEPIENT_USER")
            send_mail(
                subject=subject,
                message=full_message,
                from_email=config("EMAIL_HOST_USER"),
                recipient_list=[recipient_email],
                fail_silently=False,
            )
            messages.success(request, "Your message has been sent successfully!")
        except Exception as e:
            messages.error(request, "There was an error sending your message. Please try again later.")

        return redirect("success")

    return render(request, "contact_us.html")

# Success views
def success_view(request):
    """
    Render the success page after a contact request has been sent.
    """
    return render(request, 'success.html')