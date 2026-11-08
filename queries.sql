-- ============================================================================
-- ĐỀ 01: QUẢN LÝ TRUNG TÂM GIA SƯ (tutoring_mini)
-- Tệp 3: queries.sql - 10 Truy vấn khai thác dữ liệu chuẩn nghiệp vụ
-- ============================================================================

USE tutoring_mini;

-- ----------------------------------------------------------------------------
-- 1. Liệt kê các buổi học Completed trong tháng 01/2025, kèm mã + tên
-- học viên, mã + tên gia sư và lesson_date.
-- ----------------------------------------------------------------------------
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

-- ----------------------------------------------------------------------------
-- 2. Đếm tổng số buổi học theo từng môn học trong Quý I/2025 (01/01/2025
-- đến hết 31/03/2025), tính mọi trạng thái; hiển thị cả nhóm có số lượng bằng 0.
-- ----------------------------------------------------------------------------
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

-- ----------------------------------------------------------------------------
-- 3. Liệt kê các học viên có ít nhất một buổi học chưa có báo cáo buổi học,
-- loại trừ Cancelled. Mỗi người chỉ xuất hiện một lần.
-- ----------------------------------------------------------------------------
SELECT DISTINCT
    s.student_id,
    s.full_name AS student_name
FROM students s
JOIN lessons l ON s.student_id = l.student_id
LEFT JOIN lesson_reports lr ON l.lesson_id = lr.lesson_id
WHERE l.status <> 'Cancelled'
  AND lr.report_id IS NULL
ORDER BY s.student_id ASC;

-- ----------------------------------------------------------------------------
-- 4. Tính học phí trung bình trên một giao dịch Completed của từng môn học,
-- xét toàn bộ thời gian; chỉ lấy nhóm đã phát sinh chi phí.
-- Lưu ý chống cộng lặp: Chỉ nối tới lesson_reports (quan hệ 1-1 với lessons),
-- tuyệt đối không nối trực tiếp bảng payments để tránh nhân bản học phí.
-- ----------------------------------------------------------------------------
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

-- ----------------------------------------------------------------------------
-- 5. Liệt kê 3 gia sư có nhiều buổi học Completed nhất trong năm 2025.
-- Nếu bằng nhau, ưu tiên tutor_id tăng dần; chỉ lấy đối tượng có giao dịch.
-- ----------------------------------------------------------------------------
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

-- ----------------------------------------------------------------------------
-- 6. Tính tổng số tiền từng học viên đã thanh toán trong năm 2025 theo
-- payment_date; hiển thị cả người chưa trả tiền với tổng bằng 0.
-- ----------------------------------------------------------------------------
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

-- ----------------------------------------------------------------------------
-- 7. Liệt kê các học viên chưa có bất kỳ bản ghi thanh toán nào trong
-- toàn bộ dữ liệu, kể cả người chưa có giao dịch.
-- ----------------------------------------------------------------------------
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

-- ----------------------------------------------------------------------------
-- 8. Liệt kê toàn bộ học viên theo tổng học phí đã xác nhận giảm dần,
-- không phụ thuộc đã thanh toán hay chưa; nếu bằng nhau, sắp theo mã tăng dần.
-- Lưu ý chống cộng lặp: Tính tổng fee trực tiếp từ lesson_reports (1-1 với
-- lessons) mà không nối trực tiếp với bảng payments.
-- ----------------------------------------------------------------------------
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

-- ----------------------------------------------------------------------------
-- 9. Tính tỷ lệ hủy của từng gia sư trong năm 2025:
-- (số buổi học Cancelled / tổng số buổi học của năm) * 100.
-- Làm tròn 2 chữ số thập phân; trả NULL nếu tổng bằng 0.
-- ----------------------------------------------------------------------------
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

-- ----------------------------------------------------------------------------
-- 10. Liệt kê các học viên có hơn 3 buổi học Completed trong năm 2025,
-- kèm số lần; sắp số lần giảm dần.
-- ----------------------------------------------------------------------------
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
