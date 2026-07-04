from django.urls import path
from . import views
urlpatterns = [
    path('Save/', views.Add, name='Adds'),
    path('', views.login, name="Log"),
    path('menue/<str:E_ID>/', views.menue, name="Menue"),
    path('res/<str:id>', views.result, name="ResultID"),
    path('res/', views.result, name="Result"),
    path('me/', views.profile, name="Self"),
    path('pas/', views.password, name='password'),
    path('out/', views.out, name='Out'),
    path('change-section/', views.change_section, name='ChangeSection'),
    path('attendance/', views.attendance_view, name='StuAttendance'),
path('attendance/<str:id>', views.attendance_view, name='StuAttendanceid'),
    path('fee-voucher/', views.fee_voucher, name='FeeVoucher')
]
