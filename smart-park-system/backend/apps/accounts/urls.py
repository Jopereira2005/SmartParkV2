from django.urls import path
from .views import (
    # Authentication views
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    LogoutView,
    # User management views
    CreateAppUserView,
    CreateAppUserWithAddressView,
    UserProfileView,
    UpdateUserProfileView,
    UpdateUserAddressView,
    UpdateUserWithAddressView,
    ChangePasswordView,
    DeactivateUserView,
    # User search views
    UserSearchView,
    # Utility views
    check_username_availability,
    check_email_availability,
)

urlpatterns = [
    # ==================== AUTHENTICATION ENDPOINTS ====================
    path("auth/login/", CustomTokenObtainPairView.as_view(), name="auth_login"),
    path("auth/refresh/", CustomTokenRefreshView.as_view(), name="auth_refresh"),
    path("auth/logout/", LogoutView.as_view(), name="auth_logout"),
    # ==================== USER MANAGEMENT ENDPOINTS ====================
    path("user/register/", CreateAppUserView.as_view(), name="user_register"),
    path("user/register-with-address/", CreateAppUserWithAddressView.as_view(), name="user_register_with_address"),
    path("user/profile/", UserProfileView.as_view(), name="user_profile"),
    path(
        "user/profile/update/",
        UpdateUserProfileView.as_view(),
        name="user_profile_update",
    ),
    path(
        "user/user-address/",
        UpdateUserAddressView.as_view(),
        name="user_address_update",
    ),
    path(
        "user/profile/update-with-address/",
        UpdateUserWithAddressView.as_view(),
        name="user_profile_update_with_address",
    ),
    path(
        "user/profile/change-password/",
        ChangePasswordView.as_view(),
        name="user_change_password",
    ),
    path(
        "user/profile/deactivate/", DeactivateUserView.as_view(), name="user_deactivate"
    ),
    path("user/search/", UserSearchView.as_view(), name="user_search"),
    # ==================== UTILITY ENDPOINTS ====================
    path(
        "user/utils/check-username/",
        check_username_availability,
        name="user_check_username",
    ),
    path("user/utils/check-email/", check_email_availability, name="user_check_email"),
]
