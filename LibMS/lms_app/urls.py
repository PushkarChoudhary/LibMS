from django.urls import path, include
from django.contrib.auth.views import LogoutView
from rest_framework.routers import DefaultRouter
from .views import (
    BookViewSet,
    BorrowRequestViewSet,
    register_view,
    login_view,
    book_transaction_create_view,
    book_transaction_update_view,
    book_transaction_list_view,
    book_search_view,
    home_view,
    logout_confirmation,
    update_book,
    upload_excel_form,
    checkout_view,
    checkout_receipt_view,
    download_receipt_pdf,
    manage_borrow_request,
    create_borrow_request,
    update_single_borrow_request_status,

    about_view,
    terms_of_usage,
    privacy,
    contact_us_view,
    success_view,
)

# REST Framework Router for ViewSets
router = DefaultRouter()
router.register(r'books', BookViewSet, basename='book')
router.register(r'borrow-requests', BorrowRequestViewSet, basename='borrow-request')

urlpatterns = [
    # Home page 
    path('', home_view, name='home'),  

    # API Endpoints
    path('api/', include(router.urls)),

    # User Authentication
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('logout_confirmation/', logout_confirmation, name='logout_confirmation'),

    # BookTransaction Management
    path('book_transaction/create/', book_transaction_create_view, name='book_transaction-create'),
    path('book_transaction/update/<int:pk>/', book_transaction_update_view, name='book_transaction-update'),
    path('book_transaction/list/', book_transaction_list_view, name='book_transaction_list'),

    # Book URLs
    path('books/search/', book_search_view, name='book-search'),
    path('books/<int:pk>/update/', update_book, name='update_book'),  # Url to update view
    path('books/bulk_create/', upload_excel_form, name='create-multiple-books'),
    path('api/books/upload_excel/', BookViewSet.as_view({'post': 'upload_excel'}), name='book-upload-excel'),
    path("checkout/", checkout_view, name="checkout"),
    path('books/checkout_receipt/<str:receipt_id>/', checkout_receipt_view, name='checkout_receipt'),
    path('download_receipt/<str:receipt_id>/', download_receipt_pdf, name='download_receipt_pdf'),

    path('manage-borrow-request/', manage_borrow_request, name='manage_borrow_request'),
    path('update-single-borrow-request-status/<int:id>/', update_single_borrow_request_status, name='update_single_borrow_request_status'),

    path('create-borrow-request/', create_borrow_request, name='create_borrow_request'),

    # Extra URLs
    path("about/", about_view, name="about"),
    path("terms_of_usage/", terms_of_usage, name="terms_of_usage"),
    path("privacy/", privacy, name="privacy"),
    path("contact-us/", contact_us_view, name="contact_us"),

    path('success/', success_view, name='success'),
]
