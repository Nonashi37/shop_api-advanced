from django.urls import path

from users.views import (
    RegistrationAPIView,
    AuthorizationAPIView,
    ConfirmUserAPIView,
    CustomTokenObtainPairView,
)

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('registration/', RegistrationAPIView.as_view(), name='registration'),
    path('authorization/', AuthorizationAPIView.as_view(), name='authorization'),
    path('confirm/', ConfirmUserAPIView.as_view(), name='confirm'),
]