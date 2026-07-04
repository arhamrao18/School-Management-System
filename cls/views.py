from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Grade, Section, Subject


def save(request):
    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == "grade":
            g_name = request.POST.get('grade')
            Grade.objects.create(grade=g_name)

        elif form_type == "subject":
            subject_name = request.POST.get('subject')
            classess = request.POST.getlist('classess')
            s1, _ = Subject.objects.get_or_create(S=subject_name)
            grades = Grade.objects.filter(id__in=classess)
            s1.grade.set(grades)
            s1.save()

        elif form_type == "section":
            grade_id = request.POST.get('grade_id')
            section_name = request.POST.get('section_name')
            if grade_id and section_name:
                grade = Grade.objects.filter(id=grade_id).first()
                if grade:
                    Section.objects.create(grade=grade, section=section_name)

    grades = Grade.objects.all()
    subjects = Subject.objects.prefetch_related('grade').all()
    return render(request, 'clas/Add.html', {'Grades': grades, 'Subjects': subjects})


def get_sections(request):
    grade_id = request.GET.get('grade_id')
    sections = Section.objects.filter(grade_id=grade_id)
    data = {
        'sections': [
            {'id': s.id, 'name': s.section, 'count': s.student_count}
            for s in sections
        ]
    }
    return JsonResponse(data)
