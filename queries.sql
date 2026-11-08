USE tutoring_mini;

-- 1. List all Completed lessons in January 2025, including student ID + name,
-- tutor ID + name, and lesson_date.
SELECT
    l.lesson_id,
    s.student_id,
    s.full_name AS student_name,
    t.tutor_id,
    t.full_name AS tutor_name,
    l.lesson_date,
    l.status
FROM lessons l
JOIN students s ON l.student_id = s.student_id
JOIN tutors t ON l.tutor_id = t.tutor_id
WHERE l.status = 'Completed'
  AND l.lesson_date >= '2025-01-01'
  AND l.lesson_date < '2025-02-01'
ORDER BY l.lesson_date ASC, l.lesson_id ASC;

-- 2. Count total lessons per subject in Q1/2025 (from 2025-01-01 through
-- 2025-03-31) across all statuses; include subjects with 0 lessons.
SELECT
    sub.subject_id,
    sub.name AS subject_name,
    COUNT(l.lesson_id) AS total_lessons_q1_2025
FROM subjects sub
LEFT JOIN tutors t ON sub.subject_id = t.subject_id
LEFT JOIN lessons l ON t.tutor_id = l.tutor_id
    AND l.lesson_date >= '2025-01-01'
    AND l.lesson_date < '2025-04-01'
GROUP BY sub.subject_id, sub.name
ORDER BY total_lessons_q1_2025 DESC, sub.subject_id ASC;

-- 3. List distinct students who have at least one lesson without a lesson report,
-- excluding Cancelled lessons. Each student appears only once.
SELECT DISTINCT
    s.student_id,
    s.full_name AS student_name
FROM students s
JOIN lessons l ON s.student_id = l.student_id
LEFT JOIN lesson_reports lr ON l.lesson_id = lr.lesson_id
WHERE l.status <> 'Cancelled'
  AND lr.report_id IS NULL
ORDER BY s.student_id ASC;

-- 4. Calculate the average tuition fee per Completed lesson for each subject
-- across all time; include only subjects that have incurred fees.
SELECT
    sub.subject_id,
    sub.name AS subject_name,
    COUNT(lr.report_id) AS completed_lessons_count,
    ROUND(AVG(lr.fee), 2) AS avg_completed_fee
FROM subjects sub
JOIN tutors t ON sub.subject_id = t.subject_id
JOIN lessons l ON t.tutor_id = l.tutor_id
JOIN lesson_reports lr ON l.lesson_id = lr.lesson_id
WHERE l.status = 'Completed'
GROUP BY sub.subject_id, sub.name
ORDER BY avg_completed_fee DESC, sub.subject_id ASC;

-- 5. List the top 3 tutors with the most Completed lessons in 2025.
-- Break ties by tutor_id ascending; include only tutors with Completed lessons.
SELECT
    t.tutor_id,
    t.full_name AS tutor_name,
    COUNT(l.lesson_id) AS completed_lessons_2025
FROM tutors t
JOIN lessons l ON t.tutor_id = l.tutor_id
WHERE l.status = 'Completed'
  AND l.lesson_date >= '2025-01-01'
  AND l.lesson_date < '2026-01-01'
GROUP BY t.tutor_id, t.full_name
ORDER BY completed_lessons_2025 DESC, t.tutor_id ASC
LIMIT 3;

-- 6. Calculate the total amount paid by each student in 2025 based on
-- payment_date; display 0 for students with no payments in 2025.
SELECT
    s.student_id,
    s.full_name AS student_name,
    COALESCE(SUM(p.amount), 0.00) AS total_paid_2025
FROM students s
LEFT JOIN lessons l ON s.student_id = l.student_id
LEFT JOIN payments p ON l.lesson_id = p.lesson_id
    AND p.payment_date >= '2025-01-01'
    AND p.payment_date < '2026-01-01'
GROUP BY s.student_id, s.full_name
ORDER BY total_paid_2025 DESC, s.student_id ASC;

-- 7. List all students who have no payment records across the entire database,
-- including students who have never had any lessons.
SELECT
    s.student_id,
    s.full_name AS student_name,
    s.dob,
    s.phone
FROM students s
LEFT JOIN lessons l ON s.student_id = l.student_id
LEFT JOIN payments p ON l.lesson_id = p.lesson_id
GROUP BY s.student_id, s.full_name, s.dob, s.phone
HAVING COUNT(p.payment_id) = 0
ORDER BY s.student_id ASC;

-- 8. Rank all students by total confirmed tuition fee in descending order,
-- regardless of payment status; break ties by student_id ascending.
SELECT
    s.student_id,
    s.full_name AS student_name,
    COALESCE(SUM(lr.fee), 0.00) AS total_confirmed_fee
FROM students s
LEFT JOIN lessons l ON s.student_id = l.student_id
    AND l.status = 'Completed'
LEFT JOIN lesson_reports lr ON l.lesson_id = lr.lesson_id
GROUP BY s.student_id, s.full_name
ORDER BY total_confirmed_fee DESC, s.student_id ASC;

-- 9. Calculate the cancellation rate for each tutor in 2025:
-- (Cancelled lessons / total lessons in 2025) * 100.
-- Round to 2 decimal places; return NULL if total lessons in 2025 is 0.
SELECT
    t.tutor_id,
    t.full_name AS tutor_name,
    COUNT(l.lesson_id) AS total_lessons_2025,
    SUM(CASE WHEN l.status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_lessons_2025,
    ROUND(
        SUM(CASE WHEN l.status = 'Cancelled' THEN 1 ELSE 0 END) * 100.0
        / NULLIF(COUNT(l.lesson_id), 0),
        2
    ) AS cancel_rate_2025_pct
FROM tutors t
LEFT JOIN lessons l ON t.tutor_id = l.tutor_id
    AND l.lesson_date >= '2025-01-01'
    AND l.lesson_date < '2026-01-01'
GROUP BY t.tutor_id, t.full_name
ORDER BY t.tutor_id ASC;

-- 10. List students who have more than 3 Completed lessons in 2025,
-- including the count; order by count descending.
SELECT
    s.student_id,
    s.full_name AS student_name,
    COUNT(l.lesson_id) AS completed_lessons_2025
FROM students s
JOIN lessons l ON s.student_id = l.student_id
WHERE l.status = 'Completed'
  AND l.lesson_date >= '2025-01-01'
  AND l.lesson_date < '2026-01-01'
GROUP BY s.student_id, s.full_name
HAVING COUNT(l.lesson_id) > 3
ORDER BY completed_lessons_2025 DESC, s.student_id ASC;
