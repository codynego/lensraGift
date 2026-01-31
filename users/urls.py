from django.urls import path
from .views import UserRegistrationView, UserLoginView, UserProfileView, UserLogoutView
from .views import AddressListCreateView, AddressDetailView, SetDefaultAddressView

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('logout/', UserLogoutView.as_view(), name='logout'),


    # Base list and create
    path('addresses/', AddressListCreateView.as_view(), name='address-list-create'),

    # Detail, Update, Delete
    path('addresses/<int:pk>/', AddressDetailView.as_view(), name='address-detail'),
    path('subscribe/', EmailSubscribeView.as_view(), name='email-subscribe'),
    
    # Specific action to set default
    path('addresses/<int:pk>/set-default/', SetDefaultAddressView.as_view(), name='address-set-default'),
]