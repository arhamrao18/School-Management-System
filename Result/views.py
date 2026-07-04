from django.shortcuts import render, redirect
from student.models import Students
from .models import Marks, Attendance, AcademicRecord


def uploading(request, S_id, subject):
    """redirect to new marks upload"""
    return redirect('UploadMarks', s_id=S_id, subject=subject, term='first')
