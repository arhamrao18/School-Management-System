from django.db import models
from django.core.validators import RegexValidator
class Students(models.Model):
    id = models.AutoField(primary_key=True)
    Roll = models.CharField(max_length=50)
    grade = models.ForeignKey('cls.Grade', on_delete=models.CASCADE, null=True, blank=True)
    section = models.ForeignKey('cls.Section', on_delete=models.SET_NULL, null=True, blank=True, related_name='students_set')
    Name = models.CharField(max_length=50)
    F_Name = models.CharField(max_length=50)
    F_CNIC = models.CharField(
        max_length=15,
        validators=[RegexValidator(
            regex=r'^\d{5}-\d{7}-\d{1}$',
            message="CNIC must be 36102-1313450-9 format"
        )],
        null=False,
        blank=False
    )
    E_mail=models.EmailField(max_length=100,default="test@example.com",null=False)
    Contact = models.CharField(max_length=20)
    Address = models.CharField(max_length=1000, default='')
    Image = models.ImageField(upload_to='image', default='')

    def __str__(self):
        return self.Roll

class Logins(models.Model):
    Roll = models.ForeignKey('Students', on_delete=models.CASCADE)
    Password = models.CharField(max_length=10)
