-- ============================================================================
-- ĐỀ 01: QUẢN LÝ TRUNG TÂM GIA SƯ (tutoring_mini)
-- Tệp 2: seed.sql - Nạp dữ liệu mẫu & Truy vấn kiểm chứng toàn vẹn dữ liệu
-- ============================================================================

USE tutoring_mini;

-- ----------------------------------------------------------------------------
-- 1. Nạp dữ liệu bảng subjects (6 môn học >= 5)
-- Lưu ý:
--   - Môn 5 (Kinh tế vi mô): chỉ có buổi học năm 2024 -> không có giao dịch Quý I/2025
--   - Môn 6 (Hóa học đại cương): chưa từng có giao dịch nào toàn thời gian
-- ----------------------------------------------------------------------------
INSERT INTO subjects (subject_id, name) VALUES
(1, 'Toán cao cấp & Đại số tuyến tính'),
(2, 'Lập trình Python & Khoa học dữ liệu'),
(3, 'Tiếng Anh học thuật (IELTS)'),
(4, 'Vật lý đại cương'),
(5, 'Kinh tế vi mô'),
(6, 'Hóa học đại cương');

-- ----------------------------------------------------------------------------
-- 2. Nạp dữ liệu bảng tutors (7 gia sư >= 6)
-- Lưu ý:
--   - Gia sư 6 (TS. Đặng Văn Khoa): chỉ dạy năm 2024, chưa có giao dịch năm 2025
--   - Gia sư 7 (ThS. Bùi Thanh Tùng): chưa từng có giao dịch nào
-- ----------------------------------------------------------------------------
INSERT INTO tutors (tutor_id, full_name, email, qualification, subject_id) VALUES
(1, 'TS. Nguyễn Minh Hoàng', 'hoang.nm@tutoring.edu.vn', 'Tiến sĩ Toán ứng dụng', 1),
(2, 'ThS. Trần Thu Hà', 'ha.tt@tutoring.edu.vn', 'Thạc sĩ Khoa học Dữ liệu & AI', 2),
(3, 'ThS. Lê Quốc Bảo', 'bao.lq@tutoring.edu.vn', 'Thạc sĩ TESOL - IELTS 8.5', 3),
(4, 'CN. Phạm Quang Huy', 'huy.pq@tutoring.edu.vn', 'Cử nhân Sư phạm Toán xuất sắc', 1),
(5, 'ThS. Vũ Thị Mai Anh', 'maianh.vt@tutoring.edu.vn', 'Thạc sĩ Vật lý lý thuyết', 4),
(6, 'TS. Đặng Văn Khoa', 'khoa.dv@tutoring.edu.vn', 'Tiến sĩ Kinh tế học', 5),
(7, 'ThS. Bùi Thanh Tùng', 'tung.bt@tutoring.edu.vn', 'Thạc sĩ Hóa hữu cơ', 6);

-- ----------------------------------------------------------------------------
-- 3. Nạp dữ liệu bảng students (11 học viên >= 10)
-- Lưu ý:
--   - Học viên 1 (Phạm Ngọc Danh): 5 buổi Completed trong năm 2025 (> 3 buổi)
--   - Học viên 2 (Nguyễn Trịnh Anh Tuấn): 4 buổi Completed trong năm 2025 (> 3 buổi)
--   - Học viên 7 (Đỗ Thùy Linh): có giao dịch Completed & Pending nhưng chưa thanh toán lần nào
--   - Học viên 8 (Vũ Hoàng Nam): có giao dịch Pending & Cancelled nhưng chưa thanh toán lần nào
--   - Học viên 10 (Bùi Quốc Khánh) & 11 (Đinh Mai Phương): chưa từng có buổi học nào
-- ----------------------------------------------------------------------------
INSERT INTO students (student_id, full_name, dob, phone) VALUES
(1, 'Phạm Ngọc Danh', '2006-05-14', '0912345101'),
(2, 'Nguyễn Trịnh Anh Tuấn', '2006-08-22', '0912345102'),
(3, 'Cao Đình Bình', '2006-02-10', '0912345103'),
(4, 'Hoàng Anh Tú', '2006-11-03', '0912345104'),
(5, 'Lê Thị Hồng Nhung', '2005-07-19', '0912345105'),
(6, 'Trần Minh Đức', '2005-12-25', '0912345106'),
(7, 'Đỗ Thùy Linh', '2006-04-30', '0912345107'),
(8, 'Vũ Hoàng Nam', '2006-09-15', '0912345108'),
(9, 'Ngô Phương Thảo', '2005-03-08', '0912345109'),
(10, 'Bùi Quốc Khánh', '2007-01-20', '0912345110'),
(11, 'Đinh Mai Phương', '2007-06-12', '0912345111');

-- ----------------------------------------------------------------------------
-- 4. Nạp dữ liệu bảng lessons (23 buổi học >= 12)
-- Bao phủ:
--   - Tháng 01/2025 (buổi 1, 2, 6, 10, 22)
--   - Tháng 02 & 03/2025 thuộc Quý I/2025 (buổi 3, 4, 7, 8, 11, 12, 15, 17, 19, 20, 21, 23)
--   - Ngoài Quý I/2025: tháng 05, 06/2025 (buổi 5, 9, 13, 18)
--   - Ngoài năm 2025: năm 2024 (buổi 14, 16)
--   - Đủ 3 trạng thái: 16 Completed (1..16), 4 Pending (17..20), 3 Cancelled (21..23)
-- ----------------------------------------------------------------------------
INSERT INTO lessons (lesson_id, student_id, tutor_id, lesson_date, status) VALUES
-- Nhóm 16 buổi học Completed (lesson_id 1 -> 16)
(1,  1, 1, '2025-01-08', 'Completed'),
(2,  1, 2, '2025-01-18', 'Completed'),
(3,  1, 1, '2025-02-10', 'Completed'),
(4,  1, 2, '2025-03-05', 'Completed'),
(5,  1, 3, '2025-05-14', 'Completed'),
(6,  2, 1, '2025-01-22', 'Completed'),
(7,  2, 3, '2025-02-15', 'Completed'),
(8,  2, 2, '2025-03-20', 'Completed'),
(9,  2, 4, '2025-06-10', 'Completed'),
(10, 3, 1, '2025-01-25', 'Completed'),
(11, 3, 5, '2025-02-22', 'Completed'),
(12, 4, 3, '2025-03-12', 'Completed'),
(13, 5, 2, '2025-05-20', 'Completed'),
(14, 6, 6, '2024-11-15', 'Completed'),
(15, 7, 4, '2025-03-28', 'Completed'),
(16, 9, 6, '2024-12-10', 'Completed'),

-- Nhóm 4 buổi học Pending (lesson_id 17 -> 20): chưa có báo cáo buổi học
(17, 4, 5, '2025-03-29', 'Pending'),
(18, 7, 3, '2025-05-25', 'Pending'),
(19, 8, 4, '2025-02-18', 'Pending'),
(20, 8, 2, '2025-03-30', 'Pending'),

-- Nhóm 3 buổi học Cancelled (lesson_id 21 -> 23): đã hủy, không có báo cáo
(21, 5, 1, '2025-02-05', 'Cancelled'),
(22, 8, 3, '2025-01-29', 'Cancelled'),
(23, 3, 5, '2025-03-15', 'Cancelled');

-- ----------------------------------------------------------------------------
-- 5. Nạp dữ liệu bảng lesson_reports (16 báo cáo >= 10)
-- Quy tắc 1-1: Đúng 16 buổi Completed (lesson_id 1..16) có báo cáo kết quả
-- ----------------------------------------------------------------------------
INSERT INTO lesson_reports (report_id, lesson_id, content, feedback, duration_minutes, fee) VALUES
(1,  1,  'Ma trận nghịch đảo và hệ phương trình tuyến tính Cramer', 'Học viên nắm vững thuật toán khử Gauss', 90, 500000.00),
(2,  2,  'Cấu trúc dữ liệu List, Dict và xử lý bảng với Pandas', 'Viết code sạch, tư duy vector hóa tốt', 120, 600000.00),
(3,  3,  'Không gian vector, cơ sở và số chiều', 'Giải tốt bài tập tự luận, cần rèn thêm tốc độ', 90, 500000.00),
(4,  4,  'Trực quan hóa dữ liệu với Matplotlib & Seaborn', 'Hoàn thành xuất sắc mini-project phân tích dữ liệu', 120, 600000.00),
(5,  5,  'IELTS Writing Task 2: Phân tích dạng bài Opinion Essay', 'Bố cục đoạn văn mạch lạc, từ vựng học thuật phong phú', 90, 550000.00),
(6,  6,  'Giá trị riêng, vector riêng và chéo hóa ma trận', 'Hiểu bản chất toán học, làm đúng 90% bài tập', 90, 500000.00),
(7,  7,  'IELTS Speaking Part 2 & 3: Chủ đề Technology & Education', 'Phát âm rõ ràng, phản xạ trả lời tự nhiên', 90, 550000.00),
(8,  8,  'Truy vấn SQL nâng cao và kết nối Python - MySQL', 'Nắm chắc kỹ thuật JOIN, GROUP BY và CTE', 120, 600000.00),
(9,  9,  'Tích phân suy rộng và chuỗi số hội tụ', 'Tư duy logic tốt, trình bày lời giải chặt chẽ', 90, 450000.00),
(10, 10, 'Đạo hàm riêng và cực trị hàm nhiều biến', 'Cần chú ý điều kiện đủ của cực trị tự do', 90, 500000.00),
(11, 11, 'Động lực học chất điểm và định luật bảo toàn cơ năng', 'Vận dụng công thức chính xác vào bài toán thực tế', 90, 480000.00),
(12, 12, 'IELTS Reading: Kỹ thuật Skimming & Scanning nâng cao', 'Tăng điểm từ 6.5 lên 7.5 trong bài thi thử', 90, 550000.00),
(13, 13, 'Học máy cơ bản: Hồi quy tuyến tính với Scikit-learn', 'Hiểu rõ hàm mất mát MSE và cách đánh giá mô hình', 120, 600000.00),
(14, 14, 'Cung - Cầu thị trường và độ co giãn của cầu theo giá', 'Phân tích đồ thị kinh tế vi mô rất sắc bén', 90, 400000.00),
(15, 15, 'Phương trình vi phân cấp 1 và cấp 2 hệ số hằng', 'Tiếp thu nhanh, hoàn thành đầy đủ bài tập về nhà', 90, 450000.00),
(16, 16, 'Lý thuyết hành vi người tiêu dùng và tối đa hóa lợi ích', 'Nắm vững đường bàng quan và đường ngân sách', 90, 400000.00);

-- ----------------------------------------------------------------------------
-- 6. Nạp dữ liệu bảng payments (17 giao dịch thanh toán >= 10)
-- Bao phủ:
--   - Giao dịch trả nhiều lần:
--       + lesson_id = 1: trả 2 lần (300,000 + 200,000 = 500,000 -> trả đủ)
--       + lesson_id = 6: trả 2 lần (200,000 + 150,000 = 350,000 < 500,000 -> còn nợ 150,000)
--   - Giao dịch còn nợ một phần: lesson_id = 6 (nợ 150k), lesson_id = 10 (nợ 200k), lesson_id = 13 (nợ 200k)
--   - Giao dịch Completed chưa trả lần nào: lesson_id = 15 (Đỗ Thùy Linh - nợ 450,000)
--   - Thanh toán năm 2024: lesson_id = 14, 16 (ngoài năm 2025)
-- ----------------------------------------------------------------------------
INSERT INTO payments (payment_id, lesson_id, amount, payment_date, method) VALUES
(1,  1,  300000.00, '2025-01-08', 'Cash'),
(2,  1,  200000.00, '2025-01-12', 'BankTransfer'),
(3,  2,  600000.00, '2025-01-19', 'BankTransfer'),
(4,  3,  500000.00, '2025-02-10', 'Card'),
(5,  4,  600000.00, '2025-03-06', 'BankTransfer'),
(6,  5,  550000.00, '2025-05-15', 'Cash'),
(7,  6,  200000.00, '2025-01-22', 'Cash'),
(8,  6,  150000.00, '2025-01-28', 'BankTransfer'),
(9,  7,  550000.00, '2025-02-16', 'Card'),
(10, 8,  600000.00, '2025-03-21', 'BankTransfer'),
(11, 9,  450000.00, '2025-06-11', 'Cash'),
(12, 10, 300000.00, '2025-01-26', 'BankTransfer'),
(13, 11, 480000.00, '2025-02-23', 'Cash'),
(14, 12, 550000.00, '2025-03-12', 'Card'),
(15, 13, 400000.00, '2025-05-21', 'BankTransfer'),
(16, 14, 400000.00, '2024-11-16', 'Cash'),
(17, 16, 400000.00, '2024-12-11', 'BankTransfer');

-- ============================================================================
-- PHẦN KIỂM CHỨNG DỮ LIỆU (VERIFICATION QUERIES)
-- ============================================================================

-- Kiểm chứng 1A: Đối chiếu số lượng buổi học theo trạng thái và số báo cáo tương ứng
-- Kỳ vọng: Completed có total_lessons = total_reports = 16; Pending và Cancelled có total_reports = 0
SELECT
    l.status,
    COUNT(l.lesson_id) AS total_lessons,
    COUNT(lr.report_id) AS total_reports
FROM lessons l
LEFT JOIN lesson_reports lr ON l.lesson_id = lr.lesson_id
GROUP BY l.status;

-- Kiểm chứng 1B: Tìm các bản ghi bất thường (Completed nhưng thiếu report, hoặc chưa Completed nhưng có report)
-- Kỳ vọng: Trả về 0 dòng (tập rỗng)
SELECT
    l.lesson_id,
    l.status,
    lr.report_id
FROM lessons l
LEFT JOIN lesson_reports lr ON l.lesson_id = lr.lesson_id
WHERE (l.status = 'Completed' AND lr.report_id IS NULL)
   OR (l.status <> 'Completed' AND lr.report_id IS NOT NULL);

-- Kiểm chứng 2A: Đối chiếu tổng tiền thu trong payments với học phí fee trong lesson_reports
-- Kỳ vọng: Cột is_valid = 'HOP_LE' cho toàn bộ các buổi học, remaining_debt >= 0
SELECT
    lr.lesson_id,
    l.status,
    lr.fee AS confirmed_fee,
    COALESCE(SUM(p.amount), 0) AS total_paid,
    lr.fee - COALESCE(SUM(p.amount), 0) AS remaining_debt,
    CASE
        WHEN COALESCE(SUM(p.amount), 0) <= lr.fee THEN 'HOP_LE'
        ELSE 'VI_PHAM_VUOT_HOC_PHI'
    END AS validation_status
FROM lesson_reports lr
JOIN lessons l ON lr.lesson_id = l.lesson_id
LEFT JOIN payments p ON lr.lesson_id = p.lesson_id
GROUP BY lr.lesson_id, l.status, lr.fee
ORDER BY lr.lesson_id;

-- Kiểm chứng 2B: Tìm các giao dịch thanh toán vi phạm (thu tiền khi chưa có lesson_reports hoặc tổng thu > fee)
-- Kỳ vọng: Trả về 0 dòng (tập rỗng)
SELECT
    p.lesson_id,
    SUM(p.amount) AS total_paid,
    lr.fee
FROM payments p
LEFT JOIN lesson_reports lr ON p.lesson_id = lr.lesson_id
GROUP BY p.lesson_id, lr.fee
HAVING lr.fee IS NULL OR SUM(p.amount) > lr.fee;

-- ============================================================================
-- MINH HỌA CÁC CÂU LỆNH INSERT VI PHẠM RÀNG BUỘC (ĐẶT TRONG CHÚ THÍCH)
-- ============================================================================

-- 1. Minh họa vi phạm Khóa ngoại (FOREIGN KEY): student_id = 999 không tồn tại trong bảng students
-- INSERT INTO lessons (student_id, tutor_id, lesson_date, status)
-- VALUES (999, 1, '2025-04-01', 'Pending');
-- -> Lỗi MySQL: ERROR 1452 (23000): Cannot add or update a child row: a foreign key constraint fails

-- 2. Minh họa vi phạm CHECK (duration_minutes <= 0): Thời lượng buổi học bằng 0 hoặc âm
-- INSERT INTO lesson_reports (lesson_id, content, feedback, duration_minutes, fee)
-- VALUES (17, 'Ôn tập Vật lý', 'Tốt', 0, 450000.00);
-- -> Lỗi MySQL: ERROR 3819 (HY000): Check constraint 'chk_report_duration' is violated.

-- 3. Minh họa vi phạm CHECK (amount <= 0): Số tiền thanh toán bằng 0 hoặc âm
-- INSERT INTO payments (lesson_id, amount, payment_date, method)
-- VALUES (1, -50000.00, '2025-01-15', 'Cash');
-- -> Lỗi MySQL: ERROR 3819 (HY000): Check constraint 'chk_payment_amount' is violated.

-- 4. Minh họa vi phạm UNIQUE (trùng lesson_id trong lesson_reports): Buổi học số 1 đã có báo cáo
-- INSERT INTO lesson_reports (lesson_id, content, feedback, duration_minutes, fee)
-- VALUES (1, 'Báo cáo trùng lặp buổi 1', 'Nhận xét thêm', 90, 500000.00);
-- -> Lỗi MySQL: ERROR 1062 (23000): Duplicate entry '1' for key 'lesson_reports.lesson_id'
