from django.db import models

TERM_CHOICES = [
    ('first', 'First Term'),
    ('mid',   'Mid Term'),
    ('final', 'Final Term'),
]

STATUS_CHOICES = [
    ('P', 'Present'),
    ('A', 'Absent'),
    ('L', 'Leave'),
]


class Marks(models.Model):
    """Teacher will select term and then upload marks"""
    Student     = models.ForeignKey('student.Students', on_delete=models.CASCADE)
    section     = models.ForeignKey('cls.Section',      on_delete=models.CASCADE)
    subject     = models.CharField(max_length=100)
    term        = models.CharField(max_length=10, choices=TERM_CHOICES, default='first')
    obt_marks   = models.IntegerField()
    total_marks = models.IntegerField(default=100)
    year        = models.IntegerField(default=2025)

    class Meta:
        unique_together = ('Student', 'subject', 'term', 'year')

    def percentage(self):
        if self.total_marks:
            return round((self.obt_marks / self.total_marks) * 100, 1)
        return 0

    def __str__(self):
        return f"{self.Student} | {self.subject} | {self.term}"


class Attendance(models.Model):
    """Teacher will take attendance of student every day"""
    student = models.ForeignKey('student.Students', on_delete=models.CASCADE)
    section = models.ForeignKey('cls.Section',      on_delete=models.CASCADE)
    date    = models.DateField()
    status  = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')

    class Meta:
        unique_together = ('student', 'date')

    def __str__(self):
        return f"{self.student} | {self.date} | {self.status}"


class AcademicRecord(models.Model):
    """Record will save after promotion"""
    student_roll = models.CharField(max_length=50)
    student_name = models.CharField(max_length=100)
    grade        = models.CharField(max_length=50)
    section      = models.CharField(max_length=5)
    year         = models.IntegerField()
    promoted     = models.BooleanField(default=False)
    graduated    = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student_roll} | {self.grade} | {self.year}"
