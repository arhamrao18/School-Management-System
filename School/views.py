from django.shortcuts import render
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings
def show(request):
    return render(request,'start.html')
def contact(request):
    if request.method == 'POST':
        name=request.POST.get('name')
        email=request.POST.get('email')
        number=request.POST.get('phone')
        subj=request.POST.get('subject')
        msg=request.POST.get('message')
        if send_mail(
            subject=f"Message from School Portal about {subj}",
            message=f"From {name}\n Message: {msg}\n Contact: {number}\n email: {email}\n",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email]
        ):
            messages.success(request,'Sent Successfully')
    return render(request,'contact.html')
def about(request):
    return render(request,'about.html')
