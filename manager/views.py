"""
Manager (Admin) Views
=====================
- Login / Dashboard
- Student list + section change + update + result view
- Teacher list + add + update detail
- Auto-assign teachers (qualification + specialization match)
- Manual assign / update assign
- Teacher attendance (daily, no Sunday)
- Attendance history
- Teacher salary + deduction
- Class fee management
- Admin view: which teacher teaches which subject
"""

import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
import random
from cls.models import Grade, Section, Subject
from student.models import Students, Logins
from Teacher.models import Teachers, Entry
from Result.models import Marks, Attendance
from .models import Assigned, TeacherAttendance, TeacherSalary, ClassFee, FeePayment


# ─── Month List ──────────────────────────────────────────────
MONTHS = [
    (1,'January'),(2,'February'),(3,'March'),(4,'April'),
    (5,'May'),(6,'June'),(7,'July'),(8,'August'),
    (9,'September'),(10,'October'),(11,'November'),(12,'December'),
]


# ─── Subject Category Map ────────────────────────────────────
# Maps degree keywords to the subjects that teacher can teach
SUBJECT_CATEGORIES = {
    'mathematics' : ['mathematics', 'math', 'maths', 'statistics'],
    'math'        : ['mathematics', 'math', 'maths', 'statistics'],
    'physics'     : ['physics', 'science', 'general science'],
    'chemistry'   : ['chemistry', 'science', 'general science'],
    'biology'     : ['biology', 'science', 'general science'],
    'science'     : ['science', 'general science', 'physics', 'chemistry', 'biology'],
    'english'     : ['english', 'literature'],
    'literature'  : ['english', 'literature'],
    'urdu'        : ['urdu', 'sindhi', 'punjabi'],
    'islamiat'    : ['islamiat', 'islamic studies', 'quran', 'arabic',
                     'pakistan studies', 'social studies'],
    'islamic'     : ['islamiat', 'islamic studies', 'quran', 'arabic'],
    'arabic'      : ['arabic', 'islamiat', 'quran'],
    'pakistan studies': ['pakistan studies', 'social studies', 'history', 'civics'],
    'pak studies' : ['pakistan studies', 'social studies', 'history', 'civics'],
    'history'     : ['history', 'social studies', 'pakistan studies'],
    'geography'   : ['geography', 'social studies', 'pakistan studies'],
    'social'      : ['social studies', 'pakistan studies', 'history', 'geography'],
    'computer'    : ['computer', 'it', 'ict', 'information technology'],
    'it'          : ['computer', 'it', 'ict', 'information technology'],
    'economics'   : ['economics', 'commerce', 'business studies'],
    'commerce'    : ['commerce', 'economics', 'accounts'],
    'arts'        : ['arts', 'drawing', 'fine arts'],
    # B.Ed / M.Ed holders can teach general primary subjects
    'education'   : ['urdu', 'english', 'mathematics', 'general science', 'islamiat'],
    'b.ed'        : ['urdu', 'english', 'mathematics', 'general science', 'islamiat'],
    'bed'         : ['urdu', 'english', 'mathematics', 'general science', 'islamiat'],
    'm.ed'        : ['urdu', 'english', 'mathematics', 'general science', 'islamiat'],
    'med'         : ['urdu', 'english', 'mathematics', 'general science', 'islamiat'],
}

# Maximum subjects one teacher can be assigned
MAX_SUBJECTS_PER_TEACHER = 6


def _get_teachable_subjects(teacher):
    """
    Extract eligible subjects from teacher's qualification and specialization.
    Returns a set of lowercase subject names.
    """
    teachable = set()
    qual = teacher.Qualification.lower()
    spec = teacher.specialization.lower()

    for keyword, subjects in SUBJECT_CATEGORIES.items():
        if keyword in qual or keyword in spec:
            teachable.update(subjects)

    # If nothing matched, allow basic primary subjects by default
    if not teachable:
        teachable = {'urdu', 'english', 'mathematics', 'general science', 'islamiat'}

    return teachable


def _grade_level(grade_name):
    """
    Convert grade name to numeric level (1-6).
    Used to match teacher qualification with appropriate grade level.
    Class I-III = low level, Class IV-VI = high level
    """
    name = grade_name.lower()
    for num in ['vi', '6']:
        if num in name: return 6
    for num in ['v', '5']:
        if num in name: return 5
    for num in ['iv', '4']:
        if num in name: return 4
    for num in ['iii', '3']:
        if num in name: return 3
    for num in ['ii', '2']:
        if num in name: return 2
    return 1  # Class I or default


# ─── Admin Login ─────────────────────────────────────────────
def login(request):
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password')
        )
        if user:
            auth_login(request, user)
            return redirect('Home')
        messages.error(request, "Invalid username or password!")
    return render(request, 'add/Auth.html')


# ─── Dashboard ───────────────────────────────────────────────
@login_required(login_url='/man/')
def home(request):
    today     = datetime.date.today()
    att_today = TeacherAttendance.objects.filter(date=today)
    return render(request, 'add/home.html', {
        'sections'      : Section.objects.select_related('grade').all(),
        'total_students': Students.objects.count(),
        'total_teachers': Teachers.objects.count(),
        'total_sections': Section.objects.count(),
        'today'         : today,
        'att_summary'   : {
            'present': att_today.filter(status='P').count(),
            'absent' : att_today.filter(status='A').count(),
            'leave'  : att_today.filter(status='L').count(),
        },
    })


# ─── Students List (per section) ─────────────────────────────
@login_required(login_url='/man/')
def stu(request, s_id):
    query   = request.GET.get('q', '')
    section = get_object_or_404(Section, id=s_id)

    if query:
        students = Students.objects.filter(
            Q(Roll__icontains=query) | Q(Name__icontains=query))
    else:
        students = Students.objects.filter(
            section=s_id).select_related('grade', 'section')

    return render(request, 'add/detail.html', {
        'students': students,
        'section' : section,
        'query'   : query,
    })


# ─── Student Update (Admin) ───────────────────────────────────
@login_required(login_url='/man/')
def student_update(request, stu_id):
    """Admin can update any student's details including class and section."""
    student = get_object_or_404(Students, id=stu_id)
    grades  = Grade.objects.all()

    if request.method == "POST":
        student.Name    = request.POST.get('Name',    student.Name)
        student.F_Name  = request.POST.get('F_Name',  student.F_Name)
        student.Contact = request.POST.get('Contact', student.Contact)
        student.Address = request.POST.get('Address', student.Address)

        if request.FILES.get('image'):
            student.Image = request.FILES['image']

        grade_id = request.POST.get('grade_id')
        sec_id   = request.POST.get('section_id')

        if grade_id:
            student.grade = get_object_or_404(Grade, id=grade_id)

        if sec_id:
            new_section = get_object_or_404(Section, id=sec_id)

            # ✅ Check if new section is different from current section
            if new_section != student.section:
                current_count = new_section.students_set.exclude(pk=student.pk).count()

                if current_count >= new_section.grade.section_limit:
                    messages.error(
                        request,
                        f" Section {new_section} is full! "
                        f"({current_count}/{new_section.grade.section_limit} students). "
                        f"Please increase the limit or pick another section."
                    )
                    return render(request, 'add/student_update.html', {
                        'student': student,
                        'grades' : grades,
                    })  # Stay on same page, don't save

            student.section = new_section

        student.save()
        messages.success(request, f"{student.Name}'s details updated successfully!")
        return redirect('Stu', s_id=student.section.id if student.section else 1)

    return render(request, 'add/student_update.html', {
        'student': student,
        'grades' : grades,
    })
# ─── Admin: View Single Student Result ───────────────────────
@login_required(login_url='/man/')
def admin_result(request, stu_id):
    """Admin can view the result of any student."""
    student    = get_object_or_404(Students, id=stu_id)
    marks      = Marks.objects.filter(Student=student).order_by('term', 'subject')
    has_result = marks.exists()

    # Group marks by term
    terms = {}
    for m in marks:
        terms.setdefault(m.term, []).append(m)

    total_obt    = sum(m.obt_marks   for m in marks)
    total_max    = sum(m.total_marks  for m in marks)
    percentage   = round((total_obt / total_max * 100), 1) if total_max else 0
    grade_letter = (
        'A+' if percentage >= 90 else
        'A'  if percentage >= 80 else
        'B'  if percentage >= 70 else
        'C'  if percentage >= 60 else 'Fail'
    )

    return render(request, 'add/admin_result.html', {
        'student'     : student,
        'terms'       : terms,
        'has_result'  : has_result,
        'total_obt'   : total_obt,
        'total_max'   : total_max,
        'percentage'  : percentage,
        'grade_letter': grade_letter,
    })


# ─── Admin: All Classes Results ──────────────────────────────
@login_required(login_url='/man/')
def all_results(request):
    """
    Admin can filter and view results for any class or section.
    Result only shown when marks for ALL assigned subjects are uploaded.
    """
    grades    = Grade.objects.prefetch_related('section_set').all()
    sel_grade = request.GET.get('grade_id')
    sel_sec   = request.GET.get('sec_id')
    students  = []

    if sel_sec:
        students = Students.objects.filter(
            section_id=sel_sec).select_related('grade', 'section')
    elif sel_grade:
        students = Students.objects.filter(
            grade_id=sel_grade).select_related('grade', 'section')


    student_results = []
    for s in students:
        m = Marks.objects.filter(Student=s)

        # Total subjects assigned to this student's section
        assigned_count = Assigned.objects.filter(clas=s.section).count()

        # Subjects with marks uploaded (distinct subject names)
        uploaded_count = m.values('subject').distinct().count()

        # Result only valid when all subjects have marks
        all_uploaded = (assigned_count > 0 and uploaded_count >= assigned_count)

        obt = sum(x.obt_marks  for x in m) if all_uploaded else 0
        tot = sum(x.total_marks for x in m) if all_uploaded else 0
        pct = round(obt / tot * 100, 1)    if tot          else None

        student_results.append({
            'student'       : s,
            'has_result'    : all_uploaded,
            'percentage'    : pct,
            'obt'           : obt,
            'tot'           : tot,
            'assigned_count': assigned_count,
            'uploaded_count': uploaded_count,
            'missing_count' : max(0, assigned_count - uploaded_count),
        })

    return render(request, 'add/all_results.html', {
        'grades'         : grades,
        'student_results': student_results,
        'sel_grade'      : sel_grade,
        'sel_sec'        : sel_sec,
    })
# ─── Teachers List ───────────────────────────────────────────
@login_required(login_url='/man/')
def teach(request):
    query = request.GET.get('q', '')
    if query:
        teachers = Teachers.objects.filter(
            Q(Employee_ID__icontains=query) | Q(First_Name__icontains=query))
    else:
        teachers = Teachers.objects.all()
    return render(request, 'add/T_detail.html', {
        'teachers': teachers,
        'query'   : query,
    })


# ─── Teacher Update (Admin) ───────────────────────────────────
@login_required(login_url='/man/')
def teacher_update(request, t_id):
    """Admin can update any teacher's profile and specialization."""
    teacher = get_object_or_404(Teachers, id=t_id)

    if request.method == "POST":
        teacher.First_Name     = request.POST.get('First_Name',     teacher.First_Name)
        teacher.Last_Name      = request.POST.get('Last_Name',      teacher.Last_Name)
        teacher.Email          = request.POST.get('Email',          teacher.Email)
        teacher.Contact        = request.POST.get('Contact',        teacher.Contact)
        teacher.Address        = request.POST.get('Address',        teacher.Address)
        teacher.Qualification  = request.POST.get('Qualification',  teacher.Qualification)
        teacher.specialization = request.POST.get('specialization', teacher.specialization)

        if request.FILES.get('image'):
            teacher.Image = request.FILES['image']

        teacher.save()
        messages.success(request, f"{teacher.First_Name}'s details updated!")
        return redirect('Teacher')

    return render(request, 'add/teacher_update.html', {'teacher': teacher})


# ─── Assign Subject (Manual) ─────────────────────────────────
@login_required(login_url='/man/')
def Assign(request, E_id):
    teacher  = get_object_or_404(Teachers, Employee_ID=E_id)
    sections = Section.objects.select_related('grade').all()
    subjects = Subject.objects.all()

    if request.method == "POST":
        subject = request.POST.get('Subject')
        sec     = get_object_or_404(Section, id=request.POST.get('clas'))
        Assigned.objects.get_or_create(Employee_ID=E_id, Subject=subject, clas=sec)
        messages.success(request, f"{teacher.First_Name} assigned to {subject}!")
        return redirect('Show', E_id=E_id)

    return render(request, 'add/Assign.html', {
        'sections': sections,
        'teacher' : teacher,
        'subjects': subjects,
    })


# ─── View Teacher Assignments ────────────────────────────────
@login_required(login_url='/man/')
def show(request, E_id):
    teacher = get_object_or_404(Teachers, Employee_ID=E_id)
    assigns = Assigned.objects.filter(
        Employee_ID=E_id).select_related('clas', 'clas__grade')
    return render(request, 'add/view.html', {
        'teacher' : teacher,
        'subjects': assigns,
    })


# ─── Update / Delete Assignment ──────────────────────────────
@login_required(login_url='/man/')
def update(request, id):
    assign   = get_object_or_404(Assigned, id=id)
    sections = Section.objects.select_related('grade').all()
    subjects = Subject.objects.all()

    if request.method == "POST":
        action = request.POST.get('action')

        if action == "update":
            sub = request.POST.get('subject')
            sec = request.POST.get('clas')
            if sub: assign.Subject = sub
            if sec: assign.clas    = get_object_or_404(Section, id=sec)
            assign.save()
            messages.success(request, "Assignment updated successfully!")

        elif action == "delete":
            eid = assign.Employee_ID
            assign.delete()
            messages.success(request, "Assignment deleted!")
            return redirect('Show', E_id=eid)

    return render(request, 'add/update.html', {
        'sections': sections,
        'subject' : assign,
        'subjects': subjects,
    })


# ─── Teaching Overview ───────────────────────────────────────
@login_required(login_url='/man/')
def teaching_overview(request):
    """View all assignments grouped by teacher — who teaches what and where."""
    assigns  = Assigned.objects.select_related(
        'clas', 'clas__grade').order_by('clas__grade__id')
    teachers = Teachers.objects.all()

    overview = []
    for t in teachers:
        t_assigns = [a for a in assigns if a.Employee_ID == t.Employee_ID]
        overview.append({'teacher': t, 'assigns': t_assigns})

    return render(request, 'add/teaching_overview.html', {'overview': overview})


# ─── Auto-Assign Teachers ────────────────────────────────────
@login_required(login_url='/man/')
def auto_assign(request):
    """
    Automatically assign teachers to sections based on:
    1. Subject eligibility (degree must match the subject)
    2. One teacher per section (no repeat assignment to same section)
    3. Max subjects per teacher based on Title:
       - Lecturer = max 6 subjects
       - Others   = max 3 subjects
    4. High grade (IV-VI): MSc/MA+ preferred
       Low grade (I-III):  BA/BSc preferred
    """
    if request.method == "POST":
        Assigned.objects.all().delete()

        teachers = list(Teachers.objects.all())
        sections = list(Section.objects.select_related('grade').all())
        subjects = Subject.objects.prefetch_related('grade').all()
        assigned_count = 0

        teacher_section_map = {t.Employee_ID: set() for t in teachers}
        teacher_subj_count  = {t.Employee_ID: 0     for t in teachers}

        def get_max_subjects(teacher):
            """Title ke basis par max subjects limit"""
            title = (teacher.Title or '').lower().strip()
            if 'lecturer' in title:
                return 6   # Lecturer = max 6
            return 3       # Baaki sab = max 3

        for section in sections:
            grade          = section.grade
            g_level        = _grade_level(grade.grade)
            grade_subjects = list(subjects.filter(grade=grade))

            for subj in grade_subjects:
                s_name_lower = subj.S.lower()
                best_teacher = None
                best_score   = -1

                for t in teachers:
                    # Rule 1: Same section mein dobara nahi
                    if section.id in teacher_section_map[t.Employee_ID]:
                        continue

                    # Rule 2: Title ke basis par max subjects check
                    if teacher_subj_count[t.Employee_ID] >= get_max_subjects(t):
                        continue

                    # Rule 3: Subject eligibility check
                    teachable = _get_teachable_subjects(t)
                    if not any(s_name_lower in ts or ts in s_name_lower
                               for ts in teachable):
                        continue

                    # Score calculate karo
                    score   = 0
                    spec    = t.specialization.lower()
                    qual    = t.Qualification.lower()
                    q_level = t.qual_level()

                    if s_name_lower in spec or any(
                            w in spec for w in s_name_lower.split()):
                        score += 15

                    if s_name_lower in qual:
                        score += 8

                    if g_level >= 4:
                        if q_level >= 3:    score += 10
                        elif q_level == 2:  score += 3
                    else:
                        if q_level >= 3:    score += 6
                        elif q_level == 2:  score += 10
                        else:               score += 4

                    if score > best_score:
                        best_score   = score
                        best_teacher = t

                # Best match mila — assign karo
                if best_teacher:
                    Assigned.objects.get_or_create(
                        Employee_ID=best_teacher.Employee_ID,
                        Subject=subj.S,
                        clas=section
                    )
                    teacher_section_map[best_teacher.Employee_ID].add(section.id)
                    teacher_subj_count[best_teacher.Employee_ID] += 1
                    assigned_count += 1

                # Koi match nahi — available teachers mein se assign karo
                else:
                    available = [
                        t for t in teachers
                        if section.id not in teacher_section_map[t.Employee_ID]
                        and teacher_subj_count[t.Employee_ID] < get_max_subjects(t)
                    ]
                    if available:
                        available.sort(
                            key=lambda t: get_max_subjects(t) - teacher_subj_count[t.Employee_ID],
                            reverse=True
                        )
                        fallback = available[0]
                        Assigned.objects.get_or_create(
                            Employee_ID=fallback.Employee_ID,
                            Subject=subj.S,
                            clas=section
                        )
                        teacher_section_map[fallback.Employee_ID].add(section.id)
                        teacher_subj_count[fallback.Employee_ID] += 1
                        assigned_count += 1

        covered = sum(1 for v in teacher_section_map.values() if v)
        messages.success(request,
            f"Auto-assign complete! {assigned_count} assignments — "
            f"{covered} teachers assigned.")
        return redirect('TeachingOverview')

    # GET — confirm page
    teachers_info = []
    for t in Teachers.objects.all():
        title = (t.Title or '').lower()
        max_s = 6 if 'lecturer' in title else 3
        teachers_info.append({
            'name'    : f"{t.First_Name} {t.Last_Name}",
            'title'   : t.Title or 'Teacher',
            'max_subj': max_s,
            'qual'    : t.Qualification,
        })

    return render(request, 'add/auto_assign_confirm.html', {
        'teachers_count': Teachers.objects.count(),
        'sections_count': Section.objects.count(),
        'subjects_count': Subject.objects.count(),
        'teachers_info' : teachers_info,
    })
# ─── Teacher Attendance ──────────────────────────────────────
@login_required(login_url='/man/')
def teacher_attendance(request):
    """
    Admin marks daily teacher attendance.
    Sunday is a holiday — no attendance on Sundays.
    Each teacher can only have one record per day.
    """
    today    = datetime.date.today()
    teachers = Teachers.objects.all()

    # No attendance on Sunday
    if today.weekday() == 6:
        messages.warning(request, "Today is Sunday — no attendance!")
        return redirect('Home')

    already = TeacherAttendance.objects.filter(date=today).exists()

    if request.method == "POST" and not already:
        for t in teachers:
            status = request.POST.get(f'status_{t.id}', 'P')
            TeacherAttendance.objects.create(teacher=t, date=today, status=status)
        messages.success(request, f"Attendance for {today} saved!")
        return redirect('TeacherAttendance')

    # Load today's existing attendance for display
    existing = {
        a.teacher_id: a.status
        for a in TeacherAttendance.objects.filter(date=today)
    }

    return render(request, 'add/teacher_attendance.html', {
        'teachers': teachers,
        'today'   : today,
        'already' : already,
        'existing': existing,
    })


# ─── Attendance History ──────────────────────────────────────
@login_required(login_url='/man/')
def attendance_history(request):
    """View monthly attendance history for any teacher."""
    teachers    = Teachers.objects.all()
    sel_teacher = request.GET.get('teacher_id')
    sel_month   = int(request.GET.get('month', datetime.date.today().month))
    sel_year    = int(request.GET.get('year',  datetime.date.today().year))
    records     = []
    summary     = {}

    if sel_teacher:
        t       = get_object_or_404(Teachers, id=sel_teacher)
        records = TeacherAttendance.objects.filter(
            teacher=t,
            date__month=sel_month,
            date__year=sel_year
        ).order_by('date')

        summary = {
            'present': records.filter(status='P').count(),
            'absent' : records.filter(status='A').count(),
            'leave'  : records.filter(status='L').count(),
        }

    return render(request, 'add/attendance_history.html', {
        'teachers'   : teachers,
        'records'    : records,
        'summary'    : summary,
        'sel_teacher': sel_teacher,
        'sel_month'  : sel_month,
        'sel_year'   : sel_year,
        'months'     : MONTHS,
        'years'      : range(2024, datetime.date.today().year + 1),
    })


# ─── Teacher Salary ──────────────────────────────────────────
@login_required(login_url='/man/')
def teacher_salary(request):
    """
    Admin sets and views monthly salary for each teacher.
    Deduction formula:
      - Up to 4 absents: no deduction
      - Each extra absent (5th onwards): base_salary / 26 per day deducted
      - Leave days are NOT counted as absent
    """
    teachers  = Teachers.objects.all()
    sel_month = int(request.GET.get('month', datetime.date.today().month))
    sel_year  = int(request.GET.get('year',  datetime.date.today().year))
    salary_data = []

    for t in teachers:
        # Count only Absent days (Leave is excluded)
        absent_days = TeacherAttendance.objects.filter(
            teacher=t,
            date__month=sel_month,
            date__year=sel_year,
            status='A'
        ).count()

        sal, _ = TeacherSalary.objects.get_or_create(
            teacher=t,
            month=sel_month,
            year=sel_year,
            defaults={'base_salary': 0, 'absent_days': absent_days}
        )
        sal.absent_days = absent_days

        if sal.base_salary > 0:
            sal.calculate_and_save()
        else:
            sal.save()

        salary_data.append(sal)

    if request.method == "POST":
        for t in teachers:
            base = request.POST.get(f'base_{t.id}', '').strip()
            if base:
                sal = TeacherSalary.objects.get(
                    teacher=t, month=sel_month, year=sel_year)
                sal.base_salary = float(base)
                sal.calculate_and_save()
        messages.success(request, "Salaries saved successfully!")
        return redirect(f'/man/salary/?month={sel_month}&year={sel_year}')

    return render(request, 'add/teacher_salary.html', {
        'salary_data': salary_data,
        'sel_month'  : sel_month,
        'sel_year'   : sel_year,
        'months'     : MONTHS,
        'years'      : range(2024, datetime.date.today().year + 1),
    })


# ─── Mark Salary as Paid ─────────────────────────────────────
@login_required(login_url='/man/')
def mark_paid(request, sal_id):
    sal         = get_object_or_404(TeacherSalary, id=sal_id)
    sal.is_paid = True
    sal.save()
    messages.success(request, "Salary marked as paid!")
    return redirect(request.META.get('HTTP_REFERER', '/man/salary/'))


# ─── Class Fee Management ────────────────────────────────────
@login_required(login_url='/man/')
def class_fee(request):
    """
    Admin sets monthly fee for each grade.
    Each grade can have a different fee for each month and year.
    Students can view and download their fee voucher from the student portal.
    """
    today     = datetime.date.today()
    grades    = Grade.objects.all()
    sel_month = int(request.GET.get('month', today.month))
    sel_year  = int(request.GET.get('year',  today.year))

    if request.method == "POST":
        sel_month = int(request.POST.get('sel_month', today.month))
        sel_year  = int(request.POST.get('sel_year',  today.year))

        for grade in grades:
            amount = request.POST.get(f'fee_{grade.id}', '').strip()
            due    = request.POST.get(f'due_{grade.id}', 10)
            fine   = request.POST.get(f'fine_{grade.id}', 0)

            if amount:
                ClassFee.objects.update_or_create(
                    grade=grade,
                    month=sel_month,
                    year=sel_year,
                    defaults={
                        'monthly_fee': float(amount),
                        'due_date'   : int(due),
                        'late_fine'  : float(fine or 0),
                    }
                )

        messages.success(request,
            f"Fees for {dict(MONTHS)[sel_month]} {sel_year} saved!")
        return redirect(f'/man/fee/?month={sel_month}&year={sel_year}')

    # Load existing fees for the selected month and year
    fees = {
        f.grade_id: f
        for f in ClassFee.objects.filter(month=sel_month, year=sel_year)
    }
    grade_fees = [{'grade': g, 'fee': fees.get(g.id)} for g in grades]

    return render(request, 'add/class_fee.html', {
        'grade_fees': grade_fees,
        'sel_month' : sel_month,
        'sel_year'  : sel_year,
        'months'    : MONTHS,
        'years'     : range(2024, today.year + 2),
    })


# ─── Timetable Generator ─────────────────────────────────────
@login_required(login_url='/man/')
def timetable(request):
    sections = Section.objects.select_related('grade').all().order_by(
        'grade__grade', 'section'
    )

    assigns_raw   = Assigned.objects.select_related('clas', 'clas__grade').all()
    teacher_cache = {}
    assignments   = []

    for a in assigns_raw:
        if a.Employee_ID not in teacher_cache:
            teacher = Teachers.objects.filter(Employee_ID=a.Employee_ID).first()
            if teacher:
                teacher_cache[a.Employee_ID] = f"{teacher.First_Name} {teacher.Last_Name}".strip()
            else:
                teacher_cache[a.Employee_ID] = str(a.Employee_ID)

        a.teacher_name = teacher_cache[a.Employee_ID]
        assignments.append(a)

    return render(request, 'add/timetable.html', {
        'sections'   : sections,
        'assignments': assignments,
    })


@login_required(login_url='/man/')
def fee_status(request):
    """
    Admin views and manages student fee payment status.
    - Filter by grade, section, month, year
    - Search by student name or roll number
    - Mark fee as Paid or Pending
    - Auto-creates pending records for all students when filter is applied
    """
    today     = datetime.date.today()
    grades    = Grade.objects.all()
    sel_month = int(request.GET.get('month', today.month))
    sel_year  = int(request.GET.get('year',  today.year))
    sel_grade = request.GET.get('grade_id', '')
    sel_sec   = request.GET.get('sec_id', '')
    search    = request.GET.get('q', '').strip()

    students = Students.objects.select_related('grade', 'section').none()

    if sel_sec:
        students = Students.objects.filter(
            section_id=sel_sec).select_related('grade', 'section')
    elif sel_grade:
        students = Students.objects.filter(
            grade_id=sel_grade).select_related('grade', 'section')

    if search:
        students = Students.objects.filter(
            Q(Roll__icontains=search) | Q(Name__icontains=search)
        ).select_related('grade', 'section')

    # Auto-create pending records for filtered students
    fee_records = []
    for s in students:
        # Get class fee amount
        try:
            class_fee = ClassFee.objects.get(
                grade=s.grade, month=sel_month, year=sel_year)
            amount = class_fee.monthly_fee
        except ClassFee.DoesNotExist:
            amount = 0

        # Get or create payment record
        payment, _ = FeePayment.objects.get_or_create(
            student=s, month=sel_month, year=sel_year,
            defaults={'amount': amount, 'status': 'pending'}
        )
        # Update amount if class fee changed
        if payment.amount != amount and amount > 0:
            payment.amount = amount
            payment.save()

        fee_records.append({'student': s, 'payment': payment})

    # Mark as paid / pending
    if request.method == "POST":
        action     = request.POST.get('action')
        student_id = request.POST.get('student_id')
        payment_id = request.POST.get('payment_id')

        if action == 'mark_paid' and payment_id:
            p = get_object_or_404(FeePayment, id=payment_id)
            p.status    = 'paid'
            p.paid_date = today
            p.remarks   = request.POST.get('remarks', '')
            p.save()
            messages.success(request,
                f"{p.student.Name}'s fee marked as Paid!")

        elif action == 'mark_pending' and payment_id:
            p = get_object_or_404(FeePayment, id=payment_id)
            p.status    = 'pending'
            p.paid_date = None
            p.remarks   = request.POST.get('remarks', '')
            p.save()
            messages.success(request,
                f"{p.student.Name}'s fee marked as Pending!")

        # Redirect preserving filters
        params = f"?month={sel_month}&year={sel_year}"
        if sel_grade: params += f"&grade_id={sel_grade}"
        if sel_sec:   params += f"&sec_id={sel_sec}"
        if search:    params += f"&q={search}"
        return redirect(f'/man/fee-status/{params}')

    # Summary counts
    paid_count    = sum(1 for r in fee_records if r['payment'].status == 'paid')
    pending_count = sum(1 for r in fee_records if r['payment'].status == 'pending')
    total_amount  = sum(r['payment'].amount for r in fee_records
                        if r['payment'].status == 'paid')

    return render(request, 'add/fee_status.html', {
        'fee_records'  : fee_records,
        'grades'       : grades,
        'sel_month'    : sel_month,
        'sel_year'     : sel_year,
        'sel_grade'    : sel_grade,
        'sel_sec'      : sel_sec,
        'search'       : search,
        'months'       : MONTHS,
        'years'        : range(2024, today.year + 2),
        'paid_count'   : paid_count,
        'pending_count': pending_count,
        'total_amount' : total_amount,
    })


# ─── Fee Voucher ─────────────────────────────────────────────
def fee_voucher(request,id):
    """
    Student views and downloads their monthly fee voucher.
    Fee is fetched based on the student's grade, current month and year.
    If admin has not set the fee yet, a message is shown instead.
    """
    student = get_object_or_404(Students, Roll=id)
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

    return render(request, 'add/fee_voucher.html', {
        'student'   : student,
        'fee_obj'   : fee_obj,
        'today'     : today,
        'voucher_no': voucher_no,
        'month_name': today.strftime('%B'),
    })