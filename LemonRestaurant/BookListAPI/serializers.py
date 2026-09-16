from rest_framework import serializers
from .models import Book
from rest_framework.validators import UniqueTogetherValidator
import bleach
from django.contrib.auth.models import User

class BookSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        # queryset=User.objects.all(),
        default = serializers.CurrentUserDefault(),
        read_only=True
    )


    def validate(self, attrs):
        attrs['title'] = bleach.clean(attrs['title'])
        attrs['author'] = bleach.clean(attrs['author'])

        # if(attrs['price']<3):
        #     raise serializers.ValidationError("The price shouldn't be less than 3.0")
        # if(attrs['inventory']<0):
        #     raise serializers.ValidationError("Inventory can't be negative")
        
        return super().validate(attrs)

    class Meta:
        model = Book
        fields = ["user", "id", "title", "author", "price", "inventory", "rating"]

        validators = [
            UniqueTogetherValidator(
                queryset=Book.objects.all(),
                fields=['user', 'title', 'author'],
                message='The title, author, and price must not be the same'
            )
        ]

        extra_kwargs = {
            'rating':{
                'max_value':5,
                'min_value':0
            },
            'price':{'min_value':3},
            'inventory':{'min_value':0}
        }

        def create(self, validated_data):
            user = self.context["request"].user
            validated_data["user"] = user
            return super().create(validated_data)
        