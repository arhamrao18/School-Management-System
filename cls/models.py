from django.db import models



class Grade(models.Model):
    """Represents a class/grade in the school (e.g. Class I, Class II)"""
    id            = models.AutoField(primary_key=True)
    grade         = models.CharField(max_length=50)


    def __str__(self):
        return self.grade



class Section(models.Model):
    """A section within a grade (e.g. Class I - A, Class I - B)"""
    grade         = models.ForeignKey(Grade, on_delete=models.CASCADE)
    section       = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.grade.grade} - {self.section}"

    @property
    def student_count(self):
        return self.students_set.count()


class Subject(models.Model):
    """A subject that can be assigned to one or more grades"""
    S     = models.CharField(max_length=50)
    grade = models.ManyToManyField(Grade, related_name="subjects")

    def __str__(self):
        return self.S
