from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter(trailing_slash=True)
router.register('books', views.BookView, basename='books')
urlpatterns = router.urls