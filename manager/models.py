from django.db import models
from cls.models import Section


# ─── Teacher ko section + subject assign karna ───────────────
class Assigned(models.Model):
    """Who teaches what"""
    Employee_ID = models.CharField(max_length=100)
    Subject     = models.CharField(max_length=100)
    clas        = models.ForeignKey(Section, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('Employee_ID', 'Subject', 'clas')

    def __str__(self):
        return f"{self.Employee_ID} → {self.Subject} → {self.clas}"


# ─── Teacher daily attendance ─────────────────────────────────
TEACHER_STATUS = [('P', 'Present'), ('A', 'Absent'), ('L', 'Leave')]

class TeacherAttendance(models.Model):
    """Admin will take attendance every day except sunday"""
    teacher = models.ForeignKey('Teacher.Teachers', on_delete=models.CASCADE)
    date    = models.DateField()
    status  = models.CharField(max_length=1, choices=TEACHER_STATUS, default='P')

    class Meta:
        unique_together = ('teacher', 'date')

    def __str__(self):
        return f"{self.teacher} | {self.date} | {self.get_status_display()}"


# ─── Teacher monthly salary ───────────────────────────────────
class TeacherSalary(models.Model):
    """
    Monthly salary record.
    Deduction formula:
      - 4  absent = No deduction
      - After 4th absent  = base_salary / 26 per day will deduct
      - Leave will not count as absent
    """
    teacher     = models.ForeignKey('Teacher.Teachers', on_delete=models.CASCADE)
    month       = models.IntegerField()
    year        = models.IntegerField()
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    absent_days = models.IntegerField(default=0)
    deduction   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_salary  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_paid     = models.BooleanField(default=False)

    class Meta:
        unique_together = ('teacher', 'month', 'year')

    def calculate_and_save(self):
        extra = max(0, self.absent_days - 4)
        per_day = float(self.base_salary) / 26
        self.deduction  = round(per_day * extra, 2)
        self.net_salary = round(float(self.base_salary) - self.deduction, 2)
        self.save()

    def __str__(self):
        return f"{self.teacher} | {self.month}/{self.year}"


# ─── Class Fee ───────────────────────────────────────────────
class ClassFee(models.Model):
    """Admin will set fee every month"""
    grade       = models.ForeignKey('cls.Grade', on_delete=models.CASCADE)
    month       = models.IntegerField(default=0)   # 1-12
    year        = models.IntegerField(default=0)
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2)
    due_date    = models.IntegerField(default=10)
    late_fine   = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    class Meta:
        unique_together = ('grade', 'month', 'year')  # Ek grade ek mahine mein sirf ek record

    def __str__(self):
        return f"{self.grade} — {self.month}/{self.year} — Rs.{self.monthly_fee}"

class FeePayment(models.Model):
    """
    Admin tracks each student's monthly fee payment.
    Status: Paid or Pending
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid',    'Paid'),
    ]

    student     = models.ForeignKey('student.Students', on_delete=models.CASCADE)
    month       = models.IntegerField()    # 1-12
    year        = models.IntegerField()
    amount      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    paid_date   = models.DateField(null=True, blank=True)
    remarks     = models.CharField(max_length=200, blank=True, default='')

    class Meta:
        unique_together = ('student', 'month', 'year')

    def __str__(self):
        return f"{self.student} | {self.month}/{self.year} | {self.status}"
