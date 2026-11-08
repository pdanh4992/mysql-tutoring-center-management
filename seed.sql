USE tutoring_mini;

-- 1. Nạp dữ liệu bảng subjects (6 môn học >= 5)
-- Lưu ý:
--   - Môn 5 (Kinh tế vĩ mô 1): chỉ có buổi học năm 2024 -> không có giao dịch Quý I/2025
--   - Môn 6 (Pháp luật đại cương): chưa từng có giao dịch nào toàn thời gian
INSERT INTO subjects (subject_id, name) VALUES
(1, 'Phân tích dữ liệu với Python'),
(2, 'Cấu trúc dữ liệu và giải thuật với Python'),
(3, 'Nhập môn cơ sở dữ liệu'),
(4, 'Nhập môn Trí tuệ nhân tạo'),
(5, 'Kinh tế vĩ mô 1'),
(6, 'Pháp luật đại cương');

-- 2. Nạp dữ liệu bảng tutors (6 gia sư >= 6)
-- Lưu ý:
--   - Gia sư 6 (ThS. Phạm Đức Chung): chỉ dạy năm 2024, chưa có giao dịch năm 2025
INSERT INTO tutors (tutor_id, full_name, email, qualification, subject_id) VALUES
(1, 'TS. Trần Hùng', 'hung.tran@neu.edu.vn', 'Tiến sĩ Khoa học Dữ liệu', 1),
(2, 'TS. Vũ Đức Minh', 'minhvd@neu.edu.vn', 'Tiến sĩ Khoa học Máy tính', 2),
(3, 'TS. Trần Đức Minh', 'minhdt@neu.edu.vn', 'Tiến sĩ Hệ thống Thông tin', 3),
(4, 'TS. Nguyễn Trọng Nghĩa', 'nghiant@neu.edu.vn', 'Tiến sĩ Trí tuệ Nhân tạo', 4),
(5, 'TS. Nguyễn Phúc Hải', 'hainp@neu.edu.vn', 'Tiến sĩ Khoa học Dữ liệu & AI', 1),
(6, 'ThS. Phạm Đức Chung', 'chungpd@neu.edu.vn', 'Thạc sĩ Kinh tế học', 5);

-- 3. Nạp dữ liệu bảng students (11 học viên >= 10)
-- Lưu ý:
--   - Học viên 1 (Lê Hoàng Minh Khôi): 5 buổi Completed trong năm 2025 (> 3 buổi)
--   - Học viên 2 (Nguyễn Phương Anh): 4 buổi Completed trong năm 2025 (> 3 buổi)
--   - Học viên 7 (Vũ Ngọc Hà): có giao dịch Completed & Pending nhưng chưa thanh toán lần nào
--   - Học viên 8 (Bùi Đức Thịnh): có giao dịch Pending & Cancelled nhưng chưa thanh toán lần nào
--   - Học viên 10 (Ngô Hải Đăng) & 11 (Lý Thanh Trúc): chưa từng có buổi học nào
INSERT INTO students (student_id, full_name, dob, phone) VALUES
(1, 'Lê Hoàng Minh Khôi', '2006-03-15', '0912345101'),
(2, 'Nguyễn Phương Anh', '2006-07-22', '0912345102'),
(3, 'Trần Quốc Tuấn', '2006-01-10', '0912345103'),
(4, 'Phạm Gia Bảo', '2006-11-05', '0912345104'),
(5, 'Hoàng Mai Linh', '2005-08-19', '0912345105'),
(6, 'Đặng Tuấn Kiệt', '2005-12-25', '0912345106'),
(7, 'Vũ Ngọc Hà', '2006-04-30', '0912345107'),
(8, 'Bùi Đức Thịnh', '2006-09-12', '0912345108'),
(9, 'Đỗ Khánh Huyền', '2005-05-08', '0912345109'),
(10, 'Ngô Hải Đăng', '2007-02-18', '0912345110'),
(11, 'Lý Thanh Trúc', '2007-06-20', '0912345111');

-- 4. Nạp dữ liệu bảng lessons (23 buổi học >= 12)
-- Bao phủ:
--   - Tháng 01/2025 (buổi 1, 2, 6, 10, 22)
--   - Tháng 02 & 03/2025 thuộc Quý I/2025 (buổi 3, 4, 7, 8, 11, 12, 15, 17, 19, 20, 21, 23)
--   - Ngoài Quý I/2025: tháng 05, 06/2025 (buổi 5, 9, 13, 18)
--   - Ngoài năm 2025: năm 2024 (buổi 14, 16)
--   - Đủ 3 trạng thái: 16 Completed (1..16), 4 Pending (17..20), 3 Cancelled (21..23)
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

-- 5. Nạp dữ liệu bảng lesson_reports (16 báo cáo >= 10)
-- Quy tắc 1-1: Đúng 16 buổi Completed (lesson_id 1..16) có báo cáo kết quả theo đúng môn học
INSERT INTO lesson_reports (report_id, lesson_id, content, feedback, duration_minutes, fee) VALUES
(1,  1,  'Xử lý mảng đa chiều NumPy và thao tác DataFrame với Pandas', 'Học viên nắm vững kỹ thuật slicing và vector hóa dữ liệu', 90, 500000.00),
(2,  2,  'Phân tích độ phức tạp thuật toán Big-O, Danh sách liên kết (Linked List)', 'Cài đặt thành thạo Singly & Doubly Linked List trên Python', 120, 600000.00),
(3,  3,  'Làm sạch dữ liệu (Data Cleaning) và xử lý giá trị khuyết thiếu', 'Áp dụng tốt các kỹ thuật nội suy và lọc nhiễu thực tế', 90, 500000.00),
(4,  4,  'Cấu trúc dữ liệu Ngăn xếp (Stack), Hàng đợi (Queue) và Đệ quy', 'Giải quyết tốt bài toán duyệt biểu thức hậu tố và quay lui', 120, 600000.00),
(5,  5,  'Thiết kế sơ đồ thực thể kết hợp (ERD) và ánh xạ sang mô hình quan hệ', 'Xác định đúng khóa chính, khóa ngoại và bản số quan hệ', 90, 550000.00),
(6,  6,  'Phân tích khám phá dữ liệu (EDA) và thống kê mô tả với Python', 'Biết cách tổng hợp dữ liệu bằng groupby và pivot_table', 90, 500000.00),
(7,  7,  'Chuẩn hóa cơ sở dữ liệu (1NF, 2NF, 3NF, BCNF) và phụ thuộc hàm', 'Nắm chắc thuật toán tìm bao đóng và tách bảng bảo toàn thông tin', 90, 550000.00),
(8,  8,  'Cây nhị phân tìm kiếm (BST) và các thuật toán duyệt cây (Inorder, Preorder)', 'Viết code đệ quy rõ ràng, hiểu sâu cơ chế cân bằng cây', 120, 600000.00),
(9,  9,  'Chiến lược tìm kiếm mù (BFS, DFS) và biểu diễn không gian trạng thái', 'Mô hình hóa chính xác bài toán tìm đường trên lưới 2D', 90, 450000.00),
(10, 10, 'Trực quan hóa dữ liệu chuyên sâu với Matplotlib và Seaborn', 'Thiết kế biểu đồ phân phối và tương quan rất trực quan', 90, 500000.00),
(11, 11, 'Kỹ thuật biến đổi đặc trưng (Feature Engineering) và chuẩn hóa dữ liệu', 'Thực hành tốt MinMaxScaler và StandardScaler trên bộ dữ liệu mẫu', 90, 480000.00),
(12, 12, 'Truy vấn SQL nâng cao: INNER/LEFT JOIN, GROUP BY, HAVING và Subquery', 'Viết câu lệnh truy vấn tối ưu, chống cộng lặp chi phí chuẩn xác', 90, 550000.00),
(13, 13, 'Thuật toán sắp xếp nhanh (QuickSort, MergeSort) và Quy hoạch động', 'Tối ưu tốt bộ nhớ và thời gian chạy trên tập dữ liệu lớn', 120, 600000.00),
(14, 14, 'Đo lường sản lượng quốc gia (GDP), chỉ số giá tiêu dùng (CPI) và lạm phát', 'Phân biệt rõ GDP danh nghĩa, GDP thực tế và tốc độ tăng trưởng', 90, 400000.00),
(15, 15, 'Tìm kiếm có thông tin (Greedy Best-First Search, A*) và hàm Heuristic', 'Chứng minh chặt chẽ tính Admissible và Consistent của hàm Manhattan', 90, 450000.00),
(16, 16, 'Mô hình Tổng cầu - Tổng cung (AD-AS) và chính sách tài khóa, tiền tệ', 'Phân tích sắc bén tác động của lãi suất và chi tiêu công tới cân bằng vĩ mô', 90, 400000.00);

-- 6. Nạp dữ liệu bảng payments (17 giao dịch thanh toán >= 10)
-- Bao phủ:
--   - Giao dịch trả nhiều lần:
--       + lesson_id = 1: trả 2 lần (300,000 + 200,000 = 500,000 -> trả đủ)
--       + lesson_id = 6: trả 2 lần (200,000 + 150,000 = 350,000 < 500,000 -> còn nợ 150,000)
--   - Giao dịch còn nợ một phần: lesson_id = 6 (nợ 150k), lesson_id = 10 (nợ 200k), lesson_id = 13 (nợ 200k)
--   - Giao dịch Completed chưa trả lần nào: lesson_id = 15 (Vũ Ngọc Hà - nợ 450,000)
--   - Thanh toán năm 2024: lesson_id = 14, 16 (ngoài năm 2025)
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
SELECT
    l.status,
    COUNT(l.lesson_id) AS total_lessons,
    COUNT(lr.report_id) AS total_reports
FROM lessons l
LEFT JOIN lesson_reports lr ON l.lesson_id = lr.lesson_id
GROUP BY l.status;

-- Kiểm chứng 1B: Tìm các bản ghi bất thường (Completed nhưng thiếu report, hoặc chưa Completed nhưng có report)
SELECT
    l.lesson_id,
    l.status,
    lr.report_id
FROM lessons l
LEFT JOIN lesson_reports lr ON l.lesson_id = lr.lesson_id
WHERE (l.status = 'Completed' AND lr.report_id IS NULL)
   OR (l.status <> 'Completed' AND lr.report_id IS NOT NULL);

-- Kiểm chứng 2A: Đối chiếu tổng tiền thu trong payments với học phí fee trong lesson_reports
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
-- VALUES (17, 'Ôn tập Phân tích dữ liệu với Python', 'Tốt', 0, 450000.00);
-- -> Lỗi MySQL: ERROR 3819 (HY000): Check constraint 'chk_report_duration' is violated.

-- 3. Minh họa vi phạm CHECK (amount <= 0): Số tiền thanh toán bằng 0 hoặc âm
-- INSERT INTO payments (lesson_id, amount, payment_date, method)
-- VALUES (1, -50000.00, '2025-01-15', 'Cash');
-- -> Lỗi MySQL: ERROR 3819 (HY000): Check constraint 'chk_payment_amount' is violated.

-- 4. Minh họa vi phạm UNIQUE (trùng lesson_id trong lesson_reports): Buổi học số 1 đã có báo cáo
-- INSERT INTO lesson_reports (lesson_id, content, feedback, duration_minutes, fee)
-- VALUES (1, 'Báo cáo trùng lặp buổi 1', 'Nhận xét thêm', 90, 500000.00);
-- -> Lỗi MySQL: ERROR 1062 (23000): Duplicate entry '1' for key 'lesson_reports.lesson_id'
