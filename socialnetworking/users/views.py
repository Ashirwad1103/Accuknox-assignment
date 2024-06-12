from django.shortcuts import render
from rest_framework import generics, permissions, status
from django.contrib.auth import get_user_model
from .serializers import UserSignupSerializer, UserSerializer, FriendRequestSerializer, UserLoginSerializer, FriendRequestActionSerializer
from rest_framework.pagination import PageNumberPagination
from .models import FriendRequest
from rest_framework.response import Response
from rest_framework import serializers
from django.db.models import Q


User = get_user_model()



class UserSignupView(generics.CreateAPIView):
    queryset =  User.objects.all()
    serializer_class = UserSignupSerializer
    permission_classes = [permissions.AllowAny]


class UserLoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        tokens = serializer.get_tokens(user=user)
        return Response(tokens, status=status.HTTP_200_OK)
    

class UserSearchView(generics.ListAPIView):
    serializer_class = UserSerializer
    pagination_class = PageNumberPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        keyword = self.request.query_params.get('q', '')
        if '@' in keyword:
            return User.objects.filter(email__iexact=keyword)
        return User.objects.filter(username__icontains=keyword)
    

from django.core.cache import cache
import time

class SendFriendRequestView(generics.CreateAPIView):
    serializer_class = FriendRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    method = 'POST'

    def post(self, request):
        user_id = request.user.id
        cache_key = f'rate_limit_{user_id}'       
        request_timestamps = cache.get(cache_key, [])
        current_time = time.time()
        request_timestamps = [timestamp for timestamp in request_timestamps if current_time - timestamp < 60]
        if len(request_timestamps) >= 3:
            return Response({"error": "Rate limit exceeded"}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        request_timestamps.append(current_time)
        cache.set(cache_key, request_timestamps, timeout=60)


        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.error_messages, status=status.HTTP_400_BAD_REQUEST)


class ListPendingFriendRequestsView(generics.ListAPIView):
    serializer_class = FriendRequestSerializer
    pagination_class = PageNumberPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        to_user = self.request.user
        return FriendRequest.objects.filter(to_user=to_user, status='pending')
    
class AcceptRejectFriendRequestView(generics.UpdateAPIView):
    serializer_class = FriendRequestActionSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = FriendRequest.objects.all()

    def get_object(self):
        try:
            friend_request = FriendRequest.objects.get(
                id=self.kwargs['pk'],
                to_user=self.request.user,
                status='pending'
            )
            return friend_request
        except FriendRequest.DoesNotExist:
            raise serializers.ValidationError('Friend request not found')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        action = kwargs.get('action')


        if action == 'accept':
            instance.status = 'accepted'
        elif action == 'reject':
            instance.status = 'rejected'
        else:
            return Response({'detail': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    

class ListFriendsView(generics.ListAPIView):
    serializer_class = UserSerializer
    pagination_class = PageNumberPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        friends = User.objects.filter(
            Q(sent_request__from_user=user, sent_request__status='accepted') |
            Q(received_request__to_user=user, received_request__status='accepted')
        ).distinct()
        return friends
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)