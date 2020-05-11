from rest_framework import serializers
from user.models import AppUser as User


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True, allow_blank=False)
    password = serializers.CharField(required=True, allow_blank=False)
    id = serializers.CharField(required=False, allow_blank=False)

    class Meta:
        model = User
        fields = ['username', 'password', 'id']
