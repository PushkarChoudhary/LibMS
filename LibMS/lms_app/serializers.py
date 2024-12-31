from rest_framework import serializers
from .models import CustomUser, Book, BookTransaction, BorrowRequest

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'gender', 'pid', 'is_staff']

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'quantity', 'fee_per_day', 'created_at', 'updated_at']

class BookTransactionSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()

    class Meta:
        model = BookTransaction
        fields = ['id', 'user', 'address', 'created_at', 'updated_at']

# class BorrowRequestSerializer(serializers.ModelSerializer):
#     user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
#     book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())

#     class Meta:
#         model = BorrowRequest
#         fields = ['id', 'user', 'book', 'borrow_date', 'return_date', 'fine', 'created_at', 'updated_at']

class BorrowRequestSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
    # print(user)
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())

    class Meta:
        model = BorrowRequest
        fields = ['id', 'user', 'book', 'borrow_date', 'return_date', 'fine', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Extract user and book data
        user = validated_data.get('user')
        book = validated_data.get('book')

        # Check book availability
        if book.quantity <= 0:
            raise serializers.ValidationError("Book is not available.")

        # Reduce book quantity
        book.quantity -= 1
        book.save()

        # Create a borrow request
        borrow_request = BorrowRequest.objects.create(
            user=user,
            book=book,
            borrow_date=validated_data.get('borrow_date'),
            return_date=validated_data.get('return_date'),
        )

        return borrow_request