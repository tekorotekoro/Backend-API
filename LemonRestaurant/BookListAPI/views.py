from django.http import request
from django.shortcuts import render
from rest_framework import viewsets
from .models import Book
from .serializers import BookSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

class BookView(viewsets.ModelViewSet):
    # throttle_classes = [AnonRateThrottle, UserRateThrottle]
    # permission_classes = [IsAuthenticated]
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def get_permissions(self):
        """Return no permission for superusers, permission for authenticated users on create, and no permission for anonymous users on other actions."""
        if self.request.user.is_superuser:
            permission_classes = [IsAdminUser]

        if self.action == 'list':
            permission_classes = []

        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_throttles(self):
        """Return no throttling for superusers, throttling for authenticated users on create, and throttling for anonymous users on other actions."""
        if self.request.user.is_superuser:
            throttle_classes = []

        if not self.request.user.is_superuser:

            if self.action == 'create':
                throttle_classes = [UserRateThrottle]
            else:
                throttle_classes = [AnonRateThrottle]

        return [throttle() for throttle in throttle_classes]

    ordering_fields = ['title', 'author', 'price', 'inventory']
    filterset_fields = ['user', 'title', 'author']
    search_fields = ['title', 'author']
