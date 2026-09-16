from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter(trailing_slash=True)
router.register(r"menuitems", views.MenuItemView, basename="menuitems")
router.register(r"category", views.CategoryView, basename="category")
router.register(r"cart/menuitems", views.CartView, basename="cart")
router.register(r"orders", views.OrderView, basename="order")
router.register(r"groups/manager/users", views.ManagerView, basename="manager_view")
router.register(r"groups/delivery-crew/users", views.DeliveryCrewView, basename="delivery_crew")
# urlpatterns = router.urls

urlpatterns = [
    path('', include(router.urls))
]