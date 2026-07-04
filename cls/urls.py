from django.urls import path
from . import views
urlpatterns = [
    path('', views.save, name='Adding'),
    path('sections/', views.get_sections, name='get_sections'),
]
