# Topic 01: Tutoring Center Management System (`tutoring_mini`) — MySQL Database Project

> **National Economics University (NEU)**  
> **Faculty of Data Science and Artificial Intelligence (FDA)**  
> **MySQL Database Practical Project Report**

---

## 1. Project Overview

This project implements a complete relational database system for a **Tutoring Center Management System (`tutoring_mini`)** on **MySQL (InnoDB, UTF8MB4)**, satisfying all business rules and data integrity constraints:
- Manages academic subjects (`subjects`), tutor profiles (`tutors`), and student records (`students`).
- Tracks lesson schedules and status lifecycles (`lessons`: `Pending`, `Completed`, `Cancelled`).
- Stores post-lesson evaluations and confirmed tuition fees (`lesson_reports` — enforcing a strict **1–1** relationship with `Completed` lessons).
- Handles single and multi-installment tuition payments (`payments` — **1–N** relationship with `lessons`), applying **Anti-Fanout / Chasm Trap Prevention** techniques when aggregating financial and accounts-receivable reports.

---

## 2. Repository Structure

```text
De01_QuanLyTrungTamGiaSu/
├── schema.sql            # Part A: Database initialization & 6 tables with PK, FK, UNIQUE, CHECK, ENUM
├── seed.sql              # Part B: Sample dataset covering all edge cases & automated verification queries
├── queries.sql           # Part C: 10 analytical SQL queries (with anti-fanout fee aggregation)
├── views.sql             # Part D: 3 all-time analytical VIEWs (v_detail, v_group_summary, v_debt)
├── Bao_cao_De_01.pdf     # Academic PDF Report (NEU & FDA logos, ERD, SQL analysis & live MySQL outputs)
├── generate_report.py    # Python automation script to test SQL files on MySQL and render Bao_cao_De_01.pdf
├── assets/               # Official NEU University and FDA Faculty logos
│   ├── logo_neu.png
│   ├── logo_fda.png
│   └── logo_fda_banner.png
├── .gitignore            # Git ignore rules (.DS_Store, __pycache__, venv, ...)
└── README.md             # Project documentation and quick-start guide
```

---

## 3. Database Schema Overview (6 Tables)

| No. | Table Name | Primary Key (`PK`) | Foreign Keys (`FK`) | Key Integrity Constraints (`UNIQUE`, `CHECK`, `ENUM`) |
|:---:|---|---|---|---|
| 1 | `subjects` | `subject_id` | — | `name NOT NULL UNIQUE` |
| 2 | `tutors` | `tutor_id` | `subject_id` → `subjects(subject_id)` | `email NOT NULL UNIQUE` |
| 3 | `students` | `student_id` | — | `full_name`, `dob (DATE)`, `phone` all `NOT NULL` |
| 4 | `lessons` | `lesson_id` | `student_id` → `students(student_id)`<br>`tutor_id` → `tutors(tutor_id)` | `status ENUM('Pending', 'Completed', 'Cancelled') NOT NULL` |
| 5 | `lesson_reports` | `report_id` | `lesson_id` → `lessons(lesson_id)` | `lesson_id UNIQUE` (1–1 relation)<br>`CHECK (duration_minutes > 0)`<br>`CHECK (fee >= 0)` |
| 6 | `payments` | `payment_id` | `lesson_id` → `lessons(lesson_id)` | 1–N relation (supports multi-installment payments)<br>`CHECK (amount > 0)`<br>`method ENUM('Cash', 'BankTransfer', 'Card')` |

---

## 4. Quick-Start & Verification Guide

### Option 1: Run via MySQL CLI (Terminal / Command Prompt)

Execute the 4 `.sql` scripts sequentially on a fresh MySQL Server instance:

```bash
mysql -u root -p --default-character-set=utf8mb4 < schema.sql
mysql -u root -p --default-character-set=utf8mb4 -t < seed.sql
mysql -u root -p --default-character-set=utf8mb4 -t < queries.sql
mysql -u root -p --default-character-set=utf8mb4 -t < views.sql
```

Or run all 4 scripts in a single command:

```bash
cat schema.sql seed.sql queries.sql views.sql | mysql -u root -p --default-character-set=utf8mb4 -t
```

### Option 2: Run via MySQL Workbench

1. Open **MySQL Workbench** and connect to your MySQL Server (`Local instance 3306`).
2. Select **File → Open SQL Script...** and execute the files in order:
   - Step 1: Open `schema.sql` → Click ⚡ (**Execute**) to create `tutoring_mini` and all 6 tables.
   - Step 2: Open `seed.sql` → Click ⚡ to populate sample data and inspect the 4 verification result sets.
   - Step 3: Open `queries.sql` → Click ⚡ to run all 10 analytical queries (Queries 1–10).
   - Step 4: Open `views.sql` → Click ⚡ to create and query the 3 VIEWs (`v_detail`, `v_group_summary`, `v_debt`).

### Option 3: Regenerate the PDF Report Automatically

To re-verify all SQL scripts against MySQL and regenerate `Bao_cao_De_01.pdf`:

```bash
python3 generate_report.py
```

---

## 5. Project Team Members

| No. | Full Name | Student ID | Faculty / Institution |
|:---:|---|---|---|
| 1 | **Pham Ngoc Danh** | `11251809` | Faculty of Data Science & AI (FDA - NEU) |
| 2 | **Nguyen Manh Dung** | `11252140` | Faculty of Data Science & AI (FDA - NEU) |
| 3 | **Hoang Duc Duong** | `11252228` | Faculty of Data Science & AI (FDA - NEU) |
