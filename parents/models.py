from django.db import models

# Create your models here.
class Parent(models.Model):
    Cnic=models.CharField(max_length=30)
    pas=models.CharField(max_length=20)
    def __str__(self):
        return self.Cnic

