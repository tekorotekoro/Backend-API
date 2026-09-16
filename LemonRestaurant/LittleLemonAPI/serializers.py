from rest_framework import serializers
from .models import Category, MenuItem, Cart, Order, OrderItem
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator
from django.contrib.auth.models import User, Group
import datetime
from django.db import transaction
from decimal import Decimal

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "title", "slug"]

class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ["id", "title", "price", "category", "featured"]

        validators = [
            UniqueTogetherValidator(
                queryset=MenuItem.objects.all(),
                fields=['title', 'price'],
                message='The title and price must be unique'
            )
        ]

        extra_kwargs = {
            'price':{'min_value':2}
        }

class ManagerMenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = '__all__'

        #prevent Managers from updating thees fields
        read_only_fields = ['title', 'price', 'category']

class CartSerializer(serializers.ModelSerializer):
    unit_price = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    price = serializers.SerializerMethodField(read_only=True)
    menuitem = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all())
    quantity = serializers.IntegerField(min_value=1)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "user", "menuitem", "quantity", "unit_price", "price"]

    def get_price(self, cart_item):
        return cart_item.quantity * cart_item.unit_price

    def create(self, validated_data):
        user = self.context["request"].user
        menuitem = validated_data["menuitem"]
        quantity = validated_data["quantity"]

        # Check if this user already has menuitem in his cart, if not create a new menuitem
        cart_item, created = Cart.objects.get_or_create(
            user=user,
            menuitem=menuitem,
            defaults={
                "quantity": quantity,
                "unit_price": menuitem.price,
                "price": Decimal(quantity) * menuitem.price,
            }
        )

        # If menuitem already exists(if not created) for this user, increment the existing quantity
        if not created:
            cart_item.quantity += quantity
            cart_item.unit_price = menuitem.price
            cart_item.price = Decimal(cart_item.quantity) * cart_item.unit_price
            cart_item.save()

        return cart_item

class OrderItemSerializers(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "order", "menuitem", "quantity", "unit_price", "price"]

class OrderSerializer(serializers.ModelSerializer):
    total = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    date = serializers.DateField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    status = serializers.ChoiceField(choices=Order.Status.choices, required=False)
    # Restrict the delivery_crew field to only show users in the "Delivery crew" group:
    delivery_crew = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(groups__name='Delivery crew'),
        allow_null=True,
        required=False
    )
    order_items = OrderItemSerializers(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "user", "delivery_crew", "status", "total", "date", "order_items"]

    def create(self, validated_data):
        #1.Get user from the request context
        user = self.context['request'].user

        #2.Fetch user's cart items
        cart_items = Cart.objects.filter(user=user)
        if not cart_items.exists():
            raise serializers.ValidationError({'message':'Cart is empty. Cannot create an order'})
        
        #3.Calculate the total price of the order
        total = sum([item.price for item in cart_items])

        ##Use a transaction to remove all db operation succeed together 
        with transaction.atomic():
            #4.Create the order
            order = Order.objects.create(
                user=user, 
                total=total,
                date=datetime.date.today(),
                **validated_data
            )

            ##5.Move item from cart to OrderItem
            order_items_to_create = [
                OrderItem(
                    order=order,
                    menuitem=item.menuitem,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    price=item.price,
                ) for item in cart_items
            ]
            OrderItem.objects.bulk_create(order_items_to_create)

            #6.Clear the user's cart
            cart_items.delete()

        return order

class DeliveryCrewOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"

        read_only_fields = ['user', 'delivery_crew', 'total', 'date', 'order_items']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

