from django.urls import path
from . import views
urlpatterns = [
    path('up/<int:S_id>/<str:subject>/', views.uploading, name="Upload"),
]
