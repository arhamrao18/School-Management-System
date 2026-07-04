from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('',               views.login,            name='Auth'),
    path('home/',          views.home,             name='Home'),

    # Students
    path('detail/<int:s_id>/',     views.stu,            name='Stu'),
    path('student/update/<int:stu_id>/', views.student_update, name='StudentUpdate'),
    path('result/<int:stu_id>/',   views.admin_result,   name='AdminResult'),
    path('all-results/',           views.all_results,    name='AllResults'),

    # Teachers
    path('teach/',                 views.teach,          name='Teacher'),
    path('teacher/update/<int:t_id>/', views.teacher_update, name='TeacherUpdate'),
    path('assign/<str:E_id>/',     views.Assign,         name='Assign'),
    path('show/<str:E_id>/',       views.show,           name='Show'),
    path('update/<int:id>/',       views.update,         name='Update'),
    path('teaching-overview/',     views.teaching_overview, name='TeachingOverview'),
    path('auto-assign/',           views.auto_assign,    name='AutoAssign'),

    # Teacher Attendance
    path('teacher-attendance/',    views.teacher_attendance, name='TeacherAttendance'),
    path('attendance-history/',    views.attendance_history, name='AttendanceHistory'),

    # Salary
    path('salary/',                views.teacher_salary, name='TeacherSalary'),
    path('salary/paid/<int:sal_id>/', views.mark_paid,  name='MarkPaid'),

    # Fee
    path('fee/',                   views.class_fee,      name='ClassFee'),
    path('timetable/',             views.timetable,      name='Timetable'),
    path('fee-status/', views.fee_status, name='FeeStatus'),
path('fee-voucher/<str:id>', views.fee_voucher, name='FeeVoucher'),
]
