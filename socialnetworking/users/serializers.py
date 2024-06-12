from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from .models import FriendRequest
from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta: 
        model = User
        fields = ['id', 'email', 'username']
    
class UserSignupSerializer(serializers.ModelSerializer):
    class Meta: 
        model = User
        fields = ['email', 'username', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username = validated_data['username'],
            password = validated_data['password']
        )

        return user
    
class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'), email=email, password=password)

            if not user:
                raise serializers.ValidationError('Invalid credentials')
        
        else: 
            raise serializers.ValidationError('Email and Password are mandatory')
        
        data['user'] = user
        return data
    
    def get_tokens(self, user):
        refresh = RefreshToken.for_user(user=user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class FriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendRequest
        fields = ['id', 'to_user', 'from_user', 'status', 'timestamp']
        extra_kwargs = {
            'from_user': {'read_only': True} 
        }

    def create(self, validated_data):
        from_user = self.context['request'].user
        to_user = validated_data['to_user']
        if FriendRequest.objects.filter(from_user=from_user, to_user=to_user, status='pending').exists():
            print("raised from here")
            raise serializers.ValidationError('Friend request already exists')
        return FriendRequest.objects.create(from_user=from_user, to_user=to_user)
    
class FriendRequestActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendRequest
        fields = ['status']
