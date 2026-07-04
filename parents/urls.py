from django.urls import path
from . import views

urlpatterns = [
    path('',views.Login,name='Log'),
    path('ch/<str:c>/',views.children,name='Children'),
    path('parent_prof/',views.parent_profile,name='ParentProfile')
    ]