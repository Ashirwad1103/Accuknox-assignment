from django.urls import path
from .views import UserSearchView, UserSignupView, SendFriendRequestView, ListPendingFriendRequestsView, UserLoginView, AcceptRejectFriendRequestView, ListFriendsView


urlpatterns = [
    path('signup/', UserSignupView.as_view(), name = 'signup'),
    path('search/', UserSearchView.as_view(), name= 'user-search'),
    path('friend-request/send/', SendFriendRequestView.as_view(), name = "send-friend-request"),
    path('friend-requests/pending/', ListPendingFriendRequestsView.as_view(), name = "list-pending-requests"),
    path('login/', UserLoginView.as_view(), name = 'login'),
    path('friend-request/<int:pk>/<str:action>/', AcceptRejectFriendRequestView.as_view(), name='accept-reject-friend-request'),
    path('friends-list/', ListFriendsView.as_view(), name="friends-list")
]
