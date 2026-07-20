# GV School — School Management System

A full-featured, multi-portal School Management System built with Django, designed to streamline daily operations for schools through role-based dashboards for Admins, Teachers, Students, and Parents.

## 🚀 Features

### 🔐 Role-Based Authentication
Secure login system with four distinct portals — **Admin**, **Teacher**, **Student**, and **Parent** — each with permissions and views scoped to their role.

### 🏫 Auto Section Assignment
Automatically assigns students to sections based on predefined rules, eliminating manual sorting and reducing administrative overhead.

### 👨‍🏫 Intelligent Teacher Auto-Assignment
Assigns teachers to subjects and classes based on their qualifications and expertise, ensuring the right teacher is matched to the right subject.

### 📅 Conflict-Free Timetable Generator
- Automatically generates clash-free timetables across sections and teachers.
- Supports **drag-and-drop swapping** of periods with real-time clash detection.
- Handles complex scheduling constraints efficiently using an optimized backtracking algorithm (with async processing to prevent UI freezing on large datasets).

### 🗓️ Attendance Tracking
Daily attendance management for students, with role-specific views for teachers to mark attendance and admins/parents to monitor it.

### 📊 Term-Based Results Management
Structured result generation and management on a per-term basis, allowing teachers and admins to record and publish academic performance.

### 💰 Salary Management
Handles staff salary processing, including deduction logic for leaves, absences, or other adjustments.

### 🧾 Fee Voucher Generation
Generates fee vouchers for students, simplifying the fee collection and tracking process for the administration.

## 🛠️ Tech Stack
- **Backend:** Django
- **Database:** (add your DB, e.g. SQLite / PostgreSQL / MySQL)
- **Frontend:** (add your frontend stack, e.g. HTML, CSS, JS / Bootstrap)

## 📌 Project Highlights
- Solved real-world scheduling problems including inconsistent lecture distribution per section and browser freezing during timetable generation.
- Designed with scalability in mind, supporting multiple portals and complex role hierarchies within a single unified system.


## ⚙️ Installation
```bash
git clone <https://github.com/arhamrao18/School-Management-System.git>
cd gv-school
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```


## 🙋‍♂️ Author
**Arham** — Django Backend Developer
