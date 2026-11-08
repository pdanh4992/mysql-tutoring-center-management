USE tutoring_mini;

-- 1. VIEW v_detail:
-- Mỗi dòng là một buổi học, gồm mã buổi học, ngày, trạng thái, mã + tên học viên,
-- mã + tên gia sư, mã + tên môn học và học phí.
-- Giữ cả giao dịch chưa có kết quả (fee là NULL).
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
-- Mỗi dòng là một môn học, gồm mã, tên, tổng giao dịch, số Completed,
-- số Cancelled và tổng học phí (bằng 0 nếu chưa phát sinh);
-- giữ cả nhóm chưa phát sinh giao dịch.
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
-- Mỗi dòng là một học viên, gồm mã, tên, tổng học phí đã xác nhận, tổng đã trả
-- và còn nợ (công nợ = tổng chi phí đã xác nhận - tổng tiền thực thu).
-- Chống cộng lặp chi phí: Gom nhóm bảng payments theo lesson_id trong subquery
-- pay_per_lesson trước khi LEFT JOIN với lessons và lesson_reports.
-- Giữ cả người chưa phát sinh chi phí hoặc thanh toán (hiển thị 0).
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

-- Truy vấn kiểm tra kết quả của 3 VIEW
SELECT * FROM v_detail ORDER BY lesson_id ASC;
SELECT * FROM v_group_summary ORDER BY subject_id ASC;
SELECT * FROM v_debt ORDER BY remaining_debt DESC, student_id ASC;
