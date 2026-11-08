USE tutoring_mini;

-- 1. VIEW v_detail:
-- Each row represents a lesson, including lesson ID, date, status, student ID + name,
-- tutor ID + name, subject ID + name, and tuition fee.
-- Retains lessons without a report (fee is NULL).
CREATE OR REPLACE VIEW v_detail AS
SELECT
    l.lesson_id,
    l.lesson_date,
    l.status,
    s.student_id,
    s.full_name AS student_name,
    t.tutor_id,
    t.full_name AS tutor_name,
    sub.subject_id,
    sub.name AS subject_name,
    lr.fee
FROM lessons l
JOIN students s ON l.student_id = s.student_id
JOIN tutors t ON l.tutor_id = t.tutor_id
JOIN subjects sub ON t.subject_id = sub.subject_id
LEFT JOIN lesson_reports lr ON l.lesson_id = lr.lesson_id;

-- 2. VIEW v_group_summary:
-- Each row represents a subject, including ID, name, total lessons, Completed count,
-- Cancelled count, and total tuition fee (0 if none);
-- retains subjects with no lessons.
CREATE OR REPLACE VIEW v_group_summary AS
SELECT
    sub.subject_id,
    sub.name AS subject_name,
    COUNT(l.lesson_id) AS total_lessons,
    COALESCE(SUM(CASE WHEN l.status = 'Completed' THEN 1 ELSE 0 END), 0) AS completed_lessons,
    COALESCE(SUM(CASE WHEN l.status = 'Cancelled' THEN 1 ELSE 0 END), 0) AS cancelled_lessons,
    COALESCE(SUM(lr.fee), 0.00) AS total_fee
FROM subjects sub
LEFT JOIN tutors t ON sub.subject_id = t.subject_id
LEFT JOIN lessons l ON t.tutor_id = l.tutor_id
LEFT JOIN lesson_reports lr ON l.lesson_id = lr.lesson_id
GROUP BY sub.subject_id, sub.name;

-- 3. VIEW v_debt:
-- Each row represents a student, including ID, name, total confirmed tuition fee,
-- total paid, and remaining debt (debt = confirmed fee - total paid).
-- Anti-Fanout / Chasm Trap Prevention: Pre-aggregates payments by lesson_id in
-- subquery pay_per_lesson before joining with lessons and lesson_reports.
-- Retains students with 0 fees or 0 payments (displayed as 0).
CREATE OR REPLACE VIEW v_debt AS
SELECT
    s.student_id,
    s.full_name AS student_name,
    COALESCE(SUM(lr.fee), 0.00) AS total_confirmed_fee,
    COALESCE(SUM(pay_per_lesson.paid_amount), 0.00) AS total_paid,
    COALESCE(SUM(lr.fee), 0.00) - COALESCE(SUM(pay_per_lesson.paid_amount), 0.00) AS remaining_debt
FROM students s
LEFT JOIN lessons l
    ON s.student_id = l.student_id
LEFT JOIN lesson_reports lr
    ON l.lesson_id = lr.lesson_id
LEFT JOIN (
    SELECT
        lesson_id,
        SUM(amount) AS paid_amount
    FROM payments
    GROUP BY lesson_id
) pay_per_lesson
    ON l.lesson_id = pay_per_lesson.lesson_id
GROUP BY s.student_id, s.full_name;

-- Verification queries for the 3 VIEWs
SELECT * FROM v_detail ORDER BY lesson_id ASC;
SELECT * FROM v_group_summary ORDER BY subject_id ASC;
SELECT * FROM v_debt ORDER BY remaining_debt DESC, student_id ASC;
