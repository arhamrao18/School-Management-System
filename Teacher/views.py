"""
Teacher Portal Views
====================
- Login / Dashboard / Profile / Logout / Password Change
- Students list per section
- Student Attendance (daily, no Sunday, Present/Leave/Absent)
- Marks Upload (teacher selects term before uploading)
- Teacher Add (used by admin)
"""

import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q

from .models import Teachers, Entry
from manager.models import Assigned
from student.models import Students
from Result.models import Attendance, Marks, AcademicRecord
from cls.models import Section, Grade


# ─── Teacher Login ────────────────────────────────────────────
def login(request):
    """Teacher logs in using Employee ID and password."""
    request.session['ID'] = ''
    if request.method == "POST":
        E_ID     = request.POST.get('ID', '').strip()
        password = request.POST.get('password', '')
        try:
            entry = Entry.objects.get(Employer_ID__Employee_ID=E_ID)
            if entry.Password == password:
                request.session['ID'] = E_ID
                return redirect('Dash', myid=E_ID)
            messages.error(request, "Incorrect password!")
        except Entry.DoesNotExist:
            messages.error(request, "Employee ID not found!")
    return render(request, 'Teach/login.html')


# ─── Teacher Dashboard ────────────────────────────────────────
def dash(request, myid):
    """Show teacher's assigned sections and subjects."""
    assigns = Assigned.objects.filter(
        Employee_ID=myid).select_related('clas', 'clas__grade')
    return render(request, 'Teach/board.html', {
        'sections': assigns,
        'myid'    : myid,
    })


# ─── Teacher Profile ──────────────────────────────────────────
def prof(request):
    """Teacher can view and update their own profile."""
    eid     = request.session.get('ID', '')
    teacher = get_object_or_404(Teachers, Employee_ID=eid)

    if request.method == "POST":
        teacher.Contact = request.POST.get('Contact', teacher.Contact)
        teacher.Address = request.POST.get('Address', teacher.Address)
        teacher.Email   = request.POST.get('Email',   teacher.Email)
        if request.FILES.get('image'):
            teacher.Image = request.FILES['image']
        teacher.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('Profile')

    return render(request, 'Teach/profile.html', {'Miss': teacher})


# ─── Logout ───────────────────────────────────────────────────
def logout(request):
    """Clear session and redirect to login page."""
    request.session.flush()
    return redirect('Login')


# ─── Students List (per section) ─────────────────────────────
def stu(request, s_id):
    """Teacher views students in their assigned section."""
    query   = request.GET.get('q', '')
    section = get_object_or_404(Section, id=s_id)

    if query:
        students = Students.objects.filter(
            Q(Roll__icontains=query) | Q(Name__icontains=query))
    else:
        students = Students.objects.filter(section=section)

    return render(request, 'Teach/detail.html', {
        'students': students,
        'section' : section,
    })


# ─── Password Change ──────────────────────────────────────────
def password(request):
    """Teacher changes their own login password."""
    eid = request.session.get('ID', '')
    try:
        entry = Entry.objects.get(Employer_ID__Employee_ID=eid)
    except Entry.DoesNotExist:
        return redirect('Login')

    if request.method == "POST":
        old = request.POST.get('old_password', '')
        new = request.POST.get('new_password', '')
        cfm = request.POST.get('confirm_password', '')

        if old != entry.Password:
            messages.error(request, "Old password is incorrect.")
        elif new != cfm:
            messages.error(request, "New password and confirm password do not match.")
        elif new == old:
            messages.error(request, "New password must be different from old password.")
        else:
            entry.Password = new
            entry.save()
            messages.success(request, "Password changed successfully!")

    return redirect('Profile')


# ─── Student Attendance ───────────────────────────────────────
def attendance(request, s_id):
    """
    Teacher marks daily attendance for their section.
    - No attendance on Sundays
    - Only one attendance record allowed per day per section
    - Status options: Present (P), Leave (L), Absent (A)
    """
    section  = get_object_or_404(Section, id=s_id)
    students = Students.objects.filter(section=section)
    today    = datetime.date.today()

    # Block attendance on Sunday
    if today.weekday() == 6:
        messages.error(request, "Today is Sunday — attendance is not allowed!")
        return redirect('Dash', myid=request.session.get('ID', ''))

    # Check if attendance is already taken for today
    already = Attendance.objects.filter(section=section, date=today).exists()

    if request.method == "POST" and not already:
        for student in students:
            status = request.POST.get(f'status_{student.id}', 'P')
            Attendance.objects.create(
                student=student,
                section=section,
                date=today,
                status=status,
            )
        messages.success(request, f"Attendance for {today} saved successfully!")
        return redirect('Dash', myid=request.session.get('ID', ''))

    # Load existing attendance records for display
    existing = {
        a.student_id: a.status
        for a in Attendance.objects.filter(section=section, date=today)
    }

    return render(request, 'Teach/attendance.html', {
        'section' : section,
        'students': students,
        'today'   : today,
        'already' : already,
        'existing': existing,
    })


# ─── Marks Upload ─────────────────────────────────────────────
def upload_marks(request, s_id):
    section  = get_object_or_404(Section, id=s_id)
    students = Students.objects.filter(section=section)
    eid      = request.session.get('ID', '')
    year     = datetime.date.today().year

    assign  = Assigned.objects.filter(Employee_ID=eid, clas=section).first()
    subject = assign.Subject if assign else ''

    preselect_term = request.GET.get('term', '')

    # ✅ Check if marks already uploaded for this term
    already_uploaded = Marks.objects.filter(
        section=section,
        subject=subject,
        term=preselect_term
    ).exists()

    if already_uploaded:
        messages.error(request, f"{preselect_term.capitalize()} term marks have already been uploaded!")
        return redirect('Dash', myid=eid)  # stop here, don't show the form

    if request.method == "POST":
        term  = request.POST.get('term', '').strip()
        total = int(request.POST.get('total_marks', 100))

        if not term:
            messages.error(request, "Please select a term before saving marks!")
            return redirect('UploadMarks', s_id=s_id)

        saved = 0
        for student in students:
            val = request.POST.get(f'marks_{student.id}', '').strip()
            if val:
                Marks.objects.update_or_create(
                    Student=student,
                    subject=subject,
                    term=term,
                    year=year,
                    defaults={
                        'section'    : section,
                        'obt_marks'  : int(val),
                        'total_marks': total,
                    }
                )
                saved += 1

        #  Success message
        if term == 'final':
            _promote_students(section, year)
            messages.success(request,
                f"✅ Final term marks saved for {saved} students. "
                f"Students have been promoted to next class!")
        else:
            messages.success(request,
                f"✅ {term.capitalize()} term marks saved successfully for {saved} students.")

        return redirect('Dash', myid=eid)

    return render(request, 'Teach/marks.html', {
        'students'      : students,
        'section'       : section,
        'subject'       : subject,
        'year'          : year,
        'preselect_term': preselect_term,
    })
# ─── Student Promotion (Internal) ────────────────────────────
def _promote_students(section, year):
    """
    Promote all students in a section to the next grade after Final Term.
    - Saves an academic record before moving the student
    - If student is in the last grade, they are marked as graduated and removed
    """
    students      = Students.objects.filter(section=section)
    current_grade = section.grade
    all_grades    = list(Grade.objects.order_by('id'))
    grade_ids     = [g.id for g in all_grades]

    try:
        current_index = grade_ids.index(current_grade.id)
    except ValueError:
        return

    for student in students:
        # Save historical academic record before promotion
        AcademicRecord.objects.get_or_create(
            student_roll=student.Roll,
            year=year,
            defaults={
                'student_name': student.Name,
                'grade'       : current_grade.grade,
                'section'     : section.section,
                'promoted'    : True,
                'graduated'   : False,
            }
        )

        if current_index + 1 < len(all_grades):
            # Move student to next grade and auto-assign section
            next_grade      = all_grades[current_index + 1]
            next_section    = next_grade.get_or_create_section()
            student.grade   = next_grade
            student.section = next_section
            student.save()
        else:
            # Student has completed the last grade — mark as graduated
            AcademicRecord.objects.filter(
                student_roll=student.Roll,
                year=year,
            ).update(graduated=True, promoted=False)
            student.delete()


# ─── Add Teacher (Admin) ──────────────────────────────────────
def Add(request):
    """
    Admin adds a new teacher.
    A login entry is also created with the provided password.
    """
    if request.method == "POST":
        teacher = Teachers.objects.create(
            Employee_ID    = request.POST.get('Employee_ID'),
            First_Name     = request.POST.get('First_Name'),
            Last_Name      = request.POST.get('Last_Name'),
            Email          = request.POST.get('Email'),
            Contact        = request.POST.get('Contact'),
            Address        = request.POST.get('Address', ''),
            Qualification  = request.POST.get('Qualification'),
            specialization = request.POST.get('specialization', ''),
            Image          = request.FILES.get('image', ''),
            Title         =request.FILES.get('tittle', ''),
        )
        # Create login credentials for the teacher
        Entry.objects.create(
            Employer_ID=teacher,
            Password=request.POST.get(
                'password', f"T{teacher.Employee_ID[-3:]}123")
        )
        messages.success(request,
            f"{teacher.First_Name} added successfully! "
            f"Login ID: {teacher.Employee_ID}")
        return redirect('Save')

    return render(request, 'Teach/Add_T.html')