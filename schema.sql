DROP DATABASE IF EXISTS tutoring_mini;
CREATE DATABASE tutoring_mini
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE tutoring_mini;

-- 1. Table subjects: Catalog of academic subjects
CREATE TABLE subjects (
    subject_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB;

-- 2. Table tutors: Tutor profiles and subject assignments
CREATE TABLE tutors (
    tutor_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    qualification VARCHAR(150) NOT NULL,
    subject_id INT NOT NULL,
    CONSTRAINT fk_tutors_subject
        FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 3. Table students: Student profiles and contact details
CREATE TABLE students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    dob DATE NOT NULL,
    phone VARCHAR(20) NOT NULL
) ENGINE=InnoDB;

-- 4. Table lessons: Lesson schedule and lifecycle status
CREATE TABLE lessons (
    lesson_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    tutor_id INT NOT NULL,
    lesson_date DATE NOT NULL,
    status ENUM('Pending', 'Completed', 'Cancelled') NOT NULL,
    CONSTRAINT fk_lessons_student
        FOREIGN KEY (student_id) REFERENCES students(student_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_lessons_tutor
        FOREIGN KEY (tutor_id) REFERENCES tutors(tutor_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 5. Table lesson_reports: Post-lesson evaluation and confirmed fee (Strict 1-1 relation with lessons)
CREATE TABLE lesson_reports (
    report_id INT AUTO_INCREMENT PRIMARY KEY,
    lesson_id INT NOT NULL UNIQUE,
    content TEXT NOT NULL,
    feedback TEXT NOT NULL,
    duration_minutes INT NOT NULL,
    fee DECIMAL(12,2) NOT NULL,
    CONSTRAINT chk_report_duration CHECK (duration_minutes > 0),
    CONSTRAINT chk_report_fee CHECK (fee >= 0),
    CONSTRAINT fk_reports_lesson
        FOREIGN KEY (lesson_id) REFERENCES lessons(lesson_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 6. Table payments: Tuition payment transactions (1-N relation with lessons)
CREATE TABLE payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    lesson_id INT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    payment_date DATE NOT NULL,
    method ENUM('Cash', 'BankTransfer', 'Card') NOT NULL,
    CONSTRAINT chk_payment_amount CHECK (amount > 0),
    CONSTRAINT fk_payments_lesson
        FOREIGN KEY (lesson_id) REFERENCES lessons(lesson_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB;
