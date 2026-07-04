from django.shortcuts import render,redirect, get_object_or_404
from .models import Parent
from student.models import Students
from manager.models import FeePayment
import datetime
from django.contrib import messages
# Create your views here.
def Login(request):
    request.session['ID'] = ''
    if request.method == "POST":
        cnic     = request.POST.get('ID', '').strip()
        password = request.POST.get('password', '')
        request.session['ID']=cnic
        try:
            entry = Parent.objects.get(Cnic=cnic)
            if entry.pas == password:
                request.session['ID'] = cnic
                return redirect('Children', c=cnic)
            messages.error(request, "Incorrect password!")
        except Parent.DoesNotExist:
            messages.error(request, "CNIC number not found!")
    return render(request, 'par/Log.html')
def children(request, c):
    """
    Display all children linked to parent's CNIC.
    Also fetch current month fee status for each child.
    """
    today    = datetime.date.today()
    children = Students.objects.filter(F_CNIC=c)

    # Attach current month fee status to each student
    for student in children:
        try:
            student.fee = FeePayment.objects.get(
                student=student,
                month=today.month,
                year=today.year,
            )
        except FeePayment.DoesNotExist:
            student.fee = None  # fee record not added yet

    return render(request, 'par/child.html', {
        'childs': children,
    })

# ----------Profile----------

def parent_profile(request):
    """
    Display parent profile using CNIC stored in session.
    Password change is also handled here.
    """
    parent_cnic = request.session.get('ID', '')
    if not parent_cnic:
        return redirect('Log')

    # Get parent object
    parent = get_object_or_404(Parent, Cnic=parent_cnic)

    # Get one child to show parent details (F_Name, Contact etc)
    child = Students.objects.filter(F_CNIC=parent_cnic).first()

    # Handle password change
    if request.method == 'POST':
        current_pass = request.POST.get('current_password', '')
        new_pass     = request.POST.get('new_password', '')
        confirm_pass = request.POST.get('confirm_password', '')

        if parent.pas != current_pass:
            messages.error(request, 'Current password is incorrect.')
        elif new_pass != confirm_pass:
            messages.error(request, 'New passwords do not match.')
        elif len(new_pass) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
        else:
            parent.pas = new_pass
            parent.save()
            messages.success(request, 'Password changed successfully.')

    return render(request, 'par/profile.html', {
        'parent': parent,
        'child' : child,
    })