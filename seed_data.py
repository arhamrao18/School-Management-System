"""
Sample data script — Django shell mein chalao:
  python manage.py shell < seed_data.py

Ya directly:
  python manage.py runscript seed_data  (django-extensions ke saath)
"""



from cls.models import Grade, Section, Subject
from student.models import Students, Logins
from Teacher.models import Teachers, Entry

# ─── 1. Classes (Class I to VI) ──────────────────────────────
print("Creating grades...")
grade_names = ['Class I', 'Class II', 'Class III', 'Class IV', 'Class V', 'Class VI']
grades = {}
for name in grade_names:
    g, _ = Grade.objects.get_or_create(grade=name, defaults={'section_limit': 30})
    grades[name] = g
    print(f"  ✓ {name}")

# ─── 2. Subjects ──────────────────────────────────────────────
print("\nCreating subjects...")
subject_map = {
    'Urdu'       : list(grades.values()),
    'English'    : list(grades.values()),
    'Mathematics': list(grades.values()),
    'General Science': [grades['Class III'], grades['Class IV'], grades['Class V'], grades['Class VI']],
    'Islamiat'   : list(grades.values()),
    'Social Studies': [grades['Class IV'], grades['Class V'], grades['Class VI']],
}
for sname, gs in subject_map.items():
    s, _ = Subject.objects.get_or_create(S=sname)
    s.grade.set(gs)
    s.save()
    print(f"  ✓ {sname}")

# ─── 3. Students — 35 per Class I (triggers new section) ─────
print("\nCreating students...")

# Fake student data
first_names = ['Ahmed','Ali','Usman','Hassan','Ibrahim','Zaid','Omar','Bilal','Tariq','Hamza',
                'Sara','Fatima','Ayesha','Maryam','Zainab','Hina','Noor','Sana','Rabia','Amna']
last_names  = ['Khan','Malik','Sheikh','Qureshi','Chaudhry','Akhtar','Hussain','Ahmed','Butt','Mirza']

import itertools
name_cycle = itertools.cycle(
    [(f, l) for f in first_names for l in last_names]
)

roll_counter = 1

for g_name, grade in grades.items():
    # Class I aur II mein 35 students (new section banegi)
    # Baaki classes mein 25 students
    count = 35 if g_name in ['Class I', 'Class II'] else 25

    for i in range(count):
        first, last = next(name_cycle)
        roll = f"{g_name[:3].upper().replace(' ','')}{roll_counter:04d}"
        roll_counter += 1

        # auto section assign
        section = grade.get_or_create_section()

        s, created = Students.objects.get_or_create(
            Roll=roll,
            defaults={
                'Name'   : f"{first} {last}",
                'F_Name' : f"{last_names[(roll_counter) % len(last_names)]} Khan",
                'Contact': f"03{roll_counter % 10}{roll_counter:08d}"[:11],
                'Address': f"House {i+1}, Street {(i%10)+1}, Lahore",
                'grade'  : grade,
                'section': section,
                'Image'  : '',
            }
        )
        if created:
            Logins.objects.get_or_create(Roll=s, defaults={'Password': f"pass{roll[-4:]}"})

    secs = Section.objects.filter(grade=grade)
    print(f"  ✓ {g_name}: {count} students, {secs.count()} section(s) — ", end="")
    for sec in secs:
        print(f"Section {sec.section}({sec.student_count()})", end=" ")
    print()

# ─── 4. Teachers ──────────────────────────────────────────────
print("\nCreating teachers...")
teachers_data = [
    ('T001','Muhammad','Aslam','maslam@gvschool.edu','0311-1234567','123 Model Town','MSc Mathematics'),
    ('T002','Zara','Siddiqui','zsiddiqui@gvschool.edu','0322-2345678','45 Garden Town','MA English'),
    ('T003','Bilal','Raza','braza@gvschool.edu','0333-3456789','78 Gulberg','MSc Physics'),
    ('T004','Nadia','Hussain','nhussain@gvschool.edu','0344-4567890','12 DHA Phase 5','MA Urdu'),
    ('T005','Imran','Farooq','ifarooq@gvschool.edu','0355-5678901','34 Johar Town','MSc Computer Science'),
    ('T006','Saba','Malik','smalik@gvschool.edu','0366-6789012','56 Faisal Town','MA Islamiat'),
]
for eid, fn, ln, email, contact, addr, qual in teachers_data:
    t, created = Teachers.objects.get_or_create(
        Employee_ID=eid,
        defaults={
            'First_Name'   : fn,
            'Last_Name'    : ln,
            'Email'        : email,
            'Contact'      : contact,
            'Address'      : addr,
            'Qualification': qual,
            'Image'        : '',
        }
    )
    if created:
        Entry.objects.get_or_create(Employer_ID=t, defaults={'Password': f"teacher{eid[-3:]}"})
    print(f"  ✓ {eid}: {fn} {ln}")

print("\n✅ Sample data successfully create ho gaya!")
print("   Classes I-VI, sections with 30+ students triggering new sections,")
print("   aur 6 teachers ready hain.")
