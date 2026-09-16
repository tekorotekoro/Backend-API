from django.shortcuts import render
from .models import Category, MenuItem, Cart, Order
from .serializers import CategorySerializer, MenuItemSerializer, CartSerializer, OrderSerializer, UserSerializer, ManagerMenuItemSerializer, DeliveryCrewOrderSerializer
from rest_framework import viewsets, views, status
from rest_framework.permissions import IsAuthenticated
from .permissions import IsManager, IsDeliveryCrew, IsAdmin
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from django.contrib.auth.models import User, Group
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class CategoryView(viewsets.ModelViewSet):
    throttle_classes = [UserRateThrottle, AnonRateThrottle]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdmin]
        else:
            permission_classes = []
     
        return [permission() for permission in permission_classes]

class MenuItemView(viewsets.ModelViewSet):
    throttle_classes = [UserRateThrottle, AnonRateThrottle]
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    # In order to assign a specific field to the Manager group, override the serializer_class and use the restricted serializer for manager edits
    def get_serializer_class(self):
        # Use the manager-only serializer for update/partial_update when the user is a manager
        if self.action in ['update', 'partial_update'] and self.request.user.groups.filter(name='Manager').exists():
            return ManagerMenuItemSerializer
        # Otherwise fall back to the default serializer_class
        return self.serializer_class

    def get_permissions(self):
        # Create and destroy should be limited to admins
        if self.action in ['create', 'destroy']:
            permission_classes = [IsAdmin]
        # Update/partial_update should be allowed to Managers or Admins. Return the appropriate permission
        elif self.action in ['update', 'partial_update']:
            if self.request.user.groups.filter(name='Manager').exists():
                permission_classes = [IsManager]
            else:
                permission_classes = [IsAdmin]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    search_fields = ['title', 'category__title']
    filterset_fields = ['price', 'category']

class CartView(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    throttle_classes = [UserRateThrottle]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class OrderView(viewsets.ModelViewSet):
    serializer_class = OrderSerializer

    throttle_classes = [UserRateThrottle]
    #1.Require permission for users to be authenticated
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update'] and self.request.user.groups.filter(name='Delivery crew').exists():
            return DeliveryCrewOrderSerializer
        return self.serializer_class

    def get_permissions(self):
        if self.action in ['destroy']:
            permission_classes = [IsManager]
        elif self.action in ['update', 'partial_update']:
            user = self.request.user
            if user.groups.filter(name='Manager').exists():
                permission_classes = [IsManager]
            elif user.groups.filter(name='Delivery crew').exists():
                permission_classes = [IsDeliveryCrew]
            else:
                permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        m_user = self.request.user
        is_delivery_crew = self.request.user.groups.filter(name='Delivery crew').exists()

        if m_user.groups.filter(name='Manager').exists():
            queryset = Order.objects.all()

        # Filter the queryset to a delivery_crew member assigned to the order
        elif is_delivery_crew:
            queryset = Order.objects.filter(delivery_crew=m_user)

        # Filter the queryset so user only see their own orders
        else:
            queryset = Order.objects.filter(user=m_user)
        return queryset

    def get_object(self):
        obj = super().get_object()
        user = self.request.user

        if user.groups.filter(name='Manager').exists():
            return obj

        if not user.groups.filter(name='Delivery crew').exists():
            self.permission_denied(
                self.request,
                message='You are not allowed to update orders.'
            )

        if obj.delivery_crew_id != user.id:
            self.permission_denied(
                self.request,
                message='You can only update orders assigned to you.'
            )

        return obj


class ManagerView(viewsets.ModelViewSet):
    throttle_classes = [UserRateThrottle]
    serializer_class = UserSerializer
    # Force the router to use 'id' instead of 'pk' in the router regex
    lookup_field = 'id'
    #Restric the router from generating PUT or PATCH routes
    http_method_names = ['get', 'post', 'delete']
    permission_classes = [IsAdmin]

    def get_queryset(self):
        """Handles GET request to list all managers"""
        manager_group = Group.objects.get(name='Manager')
        user = User.objects.filter(groups=manager_group)
        return user

    def create(self, request, *args, **kwargs):
        """Handles the POST request to add a user to the manager group"""
        username = request.data.get('username')
        user = get_object_or_404(User, username=username)

        # Check for existing user in the manager group
        if user.groups.filter(name='Manager').exists():
            return Response({'message': f'{user.username} is already in the manager group.'}, status=status.HTTP_409_CONFLICT)
        # If the aren't any existing user then add user to the group
        manager_group = Group.objects.get(name='Manager')
        manager_group.user_set.add(user)
        return Response({'message':f'{user.username} added to manager group'}, status.HTTP_201_CREATED) 

    def destroy(self, request, *args, **kwargs):
        """Handle the DELETE request to remove a user from the manager group"""
        manager_group = Group.objects.get(name='Manager')

        # Here we must override the get_object() blc we are not deleting the user object itself,
        # we are just removing it from the group
        id = self.kwargs.get('id')
        user = get_object_or_404(User, pk=id)
        manager_group.user_set.remove(user)
        return Response({'message':f'{user.username} removed from manager group'}, status.HTTP_200_OK)
    
class DeliveryCrewView(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    throttle_classes = [UserRateThrottle]

    # Force the router to use 'id' instead of 'pk' in the router regex
    lookup_field = 'id'

    #Restric the router from generating PUT or PATCH routes
    http_method_names = ['get', 'post', 'delete']
    permission_classes = [IsManager]

    def get_queryset(self):
        """Handles GET request to list all delivery crew"""
        delivery_group = Group.objects.get(name='Delivery crew')
        user = User.objects.filter(groups=delivery_group)
        return user

    def create(self, request, *args, **kwargs):
        """Handles the POST request to add a user to the delivery crew group"""
        username = request.data.get('username')
        user = get_object_or_404(User, username=username)

        # Check for existing user in the manager group
        if user.groups.filter(name='Delivery crew').exists():
            return Response({'message': f'{user.username} is already in the delivery crew group.'}, status=status.HTTP_409_CONFLICT)

        # Assign user to the delivery crew group
        delivery_group = Group.objects.get(name='Delivery crew')
        delivery_group.user_set.add(user)
        return Response({'message':f'{user.username} added to delivery crew group'}, status.HTTP_201_CREATED) 

    def destroy(self, request, *args, **kwargs):
        """Handle the DELETE request to remove a user from the delivery crew group"""
        delivery_group = Group.objects.get(name='Delivery crew')

        # Here we must override the get_object() blc we are not deleting the user object itself,
        # we are just removing it from the group
        id = self.kwargs.get('id')
        user = get_object_or_404(User, pk=id)
        delivery_group.user_set.remove(user)
        return Response({'message':f'{user.username} removed from delivery crew group'}, status.HTTP_200_OK)




