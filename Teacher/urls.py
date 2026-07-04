from django.urls import path
from . import views

urlpatterns = [
    path('',                        views.login,        name='Login'),
    path('add/',                    views.Add,          name='Save'),
    path('board/<str:myid>/',       views.dash,         name='Dash'),
    path('prof/',                   views.prof,         name='Profile'),
    path('out/',                    views.logout,       name='Logout'),
    path('pass/',                   views.password,     name='Password'),
    path('studs/<int:s_id>/',       views.stu,          name='Students'),
    path('attendance/<int:s_id>/',  views.attendance,   name='Attendance'),
    path('marks/<int:s_id>/',       views.upload_marks, name='UploadMarks'),
]
