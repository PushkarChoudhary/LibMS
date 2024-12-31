from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from .models import CustomUser, Book, BookTransaction, BorrowRequest
from .forms import RegisterForm

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = RegisterForm
    model = CustomUser
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone', 'gender', 'pid')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'quantity', 'fee_per_day')
    search_fields = ('title', 'author')

@admin.register(BookTransaction)
class BookTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'address')

@admin.register(BorrowRequest)
class BorrowRequestAdmin(admin.ModelAdmin):
    list_display = ('borrower_name', 'book', 'borrow_date', 'return_date', 'fine', 'created_at', 'updated_at')
    list_filter = ('borrow_date', 'return_date', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'book__title')
    readonly_fields = ('fine', 'created_at', 'updated_at')

    def get_queryset(self, request):
        # To prefetch related fields for optimization
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'book')

    def borrower_name(self, obj):
        return obj.user.get_full_name()

    borrower_name.admin_order_field = 'user__first_name'  # Allows ordering by user's first name in the admin interface
    borrower_name.short_description = 'Borrower'

