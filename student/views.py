from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
import datetime
import re

from cls.models import Grade, Section
from .models import Students, Logins
from manager.models import Assigned, ClassFee
from Teacher.models import Teachers
from Result.models import Marks, Attendance


# ─── Add Student (Admin) ─────────────────────────────────────
def Add(request):
    """
    Admin adds a new student.
    Section must be manually selected by the admin — no auto-assignment.
    """
    grades   = Grade.objects.all()
    sections = Section.objects.all()

    if request.method == "POST":
        name       = request.POST.get('Name')
        roll       = request.POST.get('Roll')
        father     = request.POST.get('F_Name')
        cnic       = request.POST.get('F_cnic')
        email      = request.POST.get('Email')
        contact    = request.POST.get('Contact')
        address    = request.POST.get('Address')
        image      = request.FILES.get('image')
        grade_id   = request.POST.get('grade_id')
        section_id = request.POST.get('section_id')
        login = request.POST.get('loginPassword')

        # Validate CNIC format: 36102-1313450-9
        if not re.match(r'^\d{5}-\d{7}-\d{1}$', cnic):
            messages.error(request, "CNIC must be in format: 36102-1313450-9")
            return redirect('Adds')

        # Validate selected grade
        try:
            grade = Grade.objects.get(id=grade_id)
        except Grade.DoesNotExist:
            messages.error(request, "Invalid grade selected.")
            return redirect('Adds')

        # Section is now mandatory — no auto-assignment
        if not section_id:
            messages.error(request, "Please select a section.")
            return redirect('Adds')

        try:
            section = Section.objects.get(id=section_id, grade=grade)
        except Section.DoesNotExist:
            messages.error(request, "Invalid section selected.")
            return redirect('Adds')

        # Save student to database
        student=Students.objects.create(
            Name    = name,
            Roll    = roll,
            F_Name  = father,
            F_CNIC  = cnic,
            E_mail  = email,
            grade   = grade,
            section = section,
            Contact = contact,
            Address = address,
            Image   = image,
        )
        Logins.objects.create(
            Roll=student,
            password=login
        )
        messages.success(request, f"{name} added to Section {section.section}!")
        return redirect('Adds')

    students = Students.objects.select_related('grade', 'section').all()
    return render(request, 'stu/Add.html', {
        'grades'  : grades,
        'sections': sections,
        'students': students,
    })

# ─── Change Student Section (Admin) ──────────────────────────
def change_section(request):
    """Admin moves a student from one section to another."""
    if request.method == "POST":
        student         = get_object_or_404(Students, id=request.POST.get('student_id'))
        student.section = get_object_or_404(Section,  id=request.POST.get('new_section_id'))
        student.save()
        messages.success(request, "Section changed successfully!")
    return redirect('Adds')


# ─── Student Login ────────────────────────────────────────────
def login(request):
    ''' Student login using roll number and password '''
    request.session['ID'] = ''
    if request.method == "POST":
        roll     = request.POST.get('ID', '').strip()
        password = request.POST.get('password', '')
        try:
            entry = Logins.objects.get(Roll__Roll=roll)
            if entry.Password == password:
                request.session['ID'] = roll
                return redirect('Menue', E_ID=roll)
            messages.error(request, "Incorrect password!")
        except Logins.DoesNotExist:
            messages.error(request, "Roll number not found!")
    return render(request, 'stu/Login.html')

# ------------meue---------------
def menue(request, E_ID):
    # this will not show nav bar in parent attendance
    is_parent = request.GET.get('parent') == '1'

    m = Students.objects.get(Roll=E_ID)
    details = Assigned.objects.filter(clas=m.section)
    emp_ids = details.values_list('Employee_ID', flat=True)
    teachers = Teachers.objects.filter(Employee_ID__in=emp_ids)
    teacher_dict = {t.Employee_ID: t.First_Name for t in teachers}
    for d in details:
        d.teacher_name = teacher_dict.get(d.Employee_ID, "N/A")
    return render(request, 'stu/menue.html', {'Details': details,
            'student':m,   'is_parent':is_parent})


# --------------Attendance--------------


def attendance_view(request, id=None):
    """
    Monthly attendance record.
    - Normal student : roll taken from session.
    - Parent view    : roll taken from URL param (id).
    """
    is_parent = request.GET.get('parent') == '1'
    # If id provided in URL, use it (parent flow), otherwise use session (student flow)
    if id is not None:
        roll = id
    else:
        roll = request.session.get('ID', '')

    # Fetch student record using roll number
    student = get_object_or_404(Students, Roll=roll)

    # Get selected month and year from query params, default to current
    today = datetime.date.today()
    month = int(request.GET.get('month', today.month))
    year  = int(request.GET.get('year',  today.year))

    # Fetch attendance records for selected month and year
    records = Attendance.objects.filter(
        student=student,
        date__month=month,
        date__year=year
    ).order_by('date')

    # Count attendance summary
    summary = {
        'present': records.filter(status='P').count(),
        'absent' : records.filter(status='A').count(),
        'leave'  : records.filter(status='L').count(),
        'total'  : records.count(),
    }

    # Generate list of all months for dropdown
    months = [(i, datetime.date(2000, i, 1).strftime('%B')) for i in range(1, 13)]

    return render(request, 'stu/attendance.html', {
        'student'  : student,
        'records'  : records,
        'summary'  : summary,
        'sel_month': month,
        'sel_year' : year,
        'months'   : months,
        'years'    : range(2024, today.year + 1),
        'is_parent':is_parent
    })


# -------------Result----------


def result(request, id=None):
    """
    Display student result card.
    - Shows result ONLY when marks for ALL assigned subjects are uploaded.
    - Normal student : roll taken from session.
    - Parent view    : roll taken from URL param (id).
    """
    is_parent = request.GET.get('parent') == '1'
    roll = id if id is not None else request.session['ID']

    s = Students.objects.get(Roll=roll)
    n = Marks.objects.filter(Student=s)

    # Count how many subjects are assigned to this student's section
    assigned_subjects = Assigned.objects.filter(clas=s.section).count()

    # Count how many subjects have marks uploaded
    uploaded_subjects = n.values('subject').distinct().count()

    # Block result if marks are not uploaded for all subjects
    if assigned_subjects == 0 or uploaded_subjects < assigned_subjects:
        return render(request, 'stu/Card.html', {
            'S'              : s,
            'result_locked'  : True,
            'assigned_count' : assigned_subjects,
            'uploaded_count' : uploaded_subjects,
            'missing_count'  : assigned_subjects - uploaded_subjects,
            'is_parent'      : is_parent,
        })

    # All subjects have marks — show result
    total_sum  = sum(i.total_marks for i in n)
    obtained   = sum(i.obt_marks   for i in n)
    percentage = (obtained / total_sum * 100) if total_sum else 0
    grade = (
        'A+' if percentage >= 90 else
        'A'  if percentage >= 80 else
        'B'  if percentage >= 70 else
        'C'  if percentage >= 60 else 'Fail'
    )

    return render(request, 'stu/Card.html', {
        'subjects'   : n,
        'Sum'        : total_sum,
        'Total'      : obtained,
        'Percentage' : percentage,
        'Grade'      : grade,
        'S'          : s,
        'is_parent'  : is_parent,
        'result_locked': False,
    })
# ─── Student Profile ──────────────────────────────────────────
def profile(request):
    """Display logged-in student's profile."""
    roll    = request.session.get('ID', '')
    student = get_object_or_404(Students, Roll=roll)
    return render(request, 'stu/profile.html', {'Student': student})


# ─── Password Change ──────────────────────────────────────────
def password(request):
    """Student changes their own login password."""
    roll  = request.session.get('ID', '')
    entry = get_object_or_404(Logins, Roll__Roll=roll)

    if request.method == "POST":
        old     = request.POST.get('old_password', '')
        new     = request.POST.get('new_password', '')
        confirm = request.POST.get('confirm_password', '')

        if old != entry.Password:
            messages.error(request, "Old password is incorrect.")
        elif confirm != new:
            messages.error(request, "New password and confirm password do not match.")
        elif new == old:
            messages.error(request, "New password must be different from old password.")
        else:
            entry.Password = new
            entry.save()
            messages.success(request, "Password changed successfully!")

    return redirect('Self')


# ─── Logout ───────────────────────────────────────────────────
def out(request):
    """Clear session and log student out."""
    request.session.flush()
    return redirect('Log')



# ─── Fee Voucher ─────────────────────────────────────────────
def fee_voucher(request):
    """
    Student views and downloads their monthly fee voucher.
    Fee is fetched based on the student's grade, current month and year.
    If admin has not set the fee yet, a message is shown instead.
    """
    roll    = request.session.get('ID', '')
    student = get_object_or_404(Students, Roll=roll)
    today   = datetime.date.today()

    # Fetch fee for student's grade and current month/year
    try:
        fee_obj = ClassFee.objects.get(
            grade=student.grade,
            month=today.month,
            year=today.year,
        )
    except ClassFee.DoesNotExist:
        fee_obj = None

    voucher_no = f"VCH-{student.Roll}-{today.month:02d}{today.year}"

    return render(request, 'stu/fee_voucher.html', {
        'student'   : student,
        'fee_obj'   : fee_obj,
        'today'     : today,
        'voucher_no': voucher_no,
        'month_name': today.strftime('%B'),
    })