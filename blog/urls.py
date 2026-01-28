from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BlogPostViewSet

# The router automatically maps our ViewSet actions to URL patterns
router = DefaultRouter()
router.register(r'posts', BlogPostViewSet, basename='blogpost')

urlpatterns = [
    # This includes the list, detail, categories, and featured endpoints
    path('', include(router.urls)),
]