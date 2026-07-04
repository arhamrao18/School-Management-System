from django.db import models

# Qualification  levels — for auto-assign
QUAL_LEVEL = {
    'phd'  : 5,
    'mphil': 4,
    'msc'  : 3,
    'ma'   : 3,
    'mba'  : 3,
    'bed'  : 2,
    'bsc'  : 2,
    'ba'   : 2,
    'fa'   : 1,
    'matric':1,
}

def get_qual_level(qual_str):
    """Get numeric level from Qualification string  (use in auto-assign)"""
    q = qual_str.lower()
    for key, val in QUAL_LEVEL.items():
        if key in q:
            return val
    return 1


class Teachers(models.Model):
    """School teacher"""
    id            = models.AutoField(primary_key=True)
    Employee_ID   = models.CharField(max_length=100, unique=True)
    First_Name    = models.CharField(max_length=50)
    Last_Name     = models.CharField(max_length=50)
    Email         = models.EmailField()
    Contact       = models.CharField(max_length=20)
    Address       = models.CharField(max_length=1000)
    Image         = models.ImageField(upload_to='image', blank=True, default='')
    Qualification = models.CharField(max_length=200)
    # Subject specialization — match in auto assign
    specialization = models.CharField(max_length=200, blank=True, default='',
                                      help_text="Subjects that teacher can teach (comma separated)")
    Gender = models.CharField(max_length=20, default=''),
    Title=models.CharField(max_length=30,default='')

    def qual_level(self):
        """Return numeric level through qualification"""
        return get_qual_level(self.Qualification)

    def __str__(self):
        return f"{self.Employee_ID} ({self.First_Name})"


class Entry(models.Model):
    """Teacher login credentials"""
    Employer_ID = models.ForeignKey(Teachers, on_delete=models.CASCADE)
    Password    = models.CharField(max_length=50)

    def __str__(self):
        return str(self.Employer_ID)
