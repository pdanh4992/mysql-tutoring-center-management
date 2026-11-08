USE tutoring_mini;

-- 1. Seed data for subjects (6 subjects >= 5)
-- Notes:
--   - Subject 5 (Macroeconomics 1): only has lessons in 2024 -> 0 lessons in Q1/2025
--   - Subject 6 (General Law): 0 lessons across all time
INSERT INTO subjects (subject_id, name) VALUES
(1, 'Data Analysis with Python'),
(2, 'Data Structures and Algorithms with Python'),
(3, 'Introduction to Databases'),
(4, 'Introduction to Artificial Intelligence'),
(5, 'Macroeconomics 1'),
(6, 'General Law');

-- 2. Seed data for tutors (6 tutors >= 6)
-- Notes:
--   - Tutor 6 (M.Sc. Pham Duc Chung): only taught in 2024, 0 lessons in 2025
INSERT INTO tutors (tutor_id, full_name, email, qualification, subject_id) VALUES
(1, 'Dr. Tran Hung', 'hung.tran@neu.edu.vn', 'Ph.D. in Data Science', 1),
(2, 'Dr. Vu Duc Minh', 'minhvd@neu.edu.vn', 'Ph.D. in Computer Science', 2),
(3, 'Dr. Tran Duc Minh', 'minhdt@neu.edu.vn', 'Ph.D. in Information Systems', 3),
(4, 'Dr. Nguyen Trong Nghia', 'nghiant@neu.edu.vn', 'Ph.D. in Artificial Intelligence', 4),
(5, 'Dr. Nguyen Phuc Hai', 'hainp@neu.edu.vn', 'Ph.D. in Data Science & AI', 1),
(6, 'M.Sc. Pham Duc Chung', 'chungpd@neu.edu.vn', 'M.Sc. in Economics', 5);

-- 3. Seed data for students (11 students >= 10)
-- Notes:
--   - Student 1 (Le Hoang Minh Khoi): 5 Completed lessons in 2025 (> 3 lessons)
--   - Student 2 (Nguyen Phuong Anh): 4 Completed lessons in 2025 (> 3 lessons)
--   - Student 7 (Vu Ngoc Ha): has Completed & Pending lessons but 0 payments
--   - Student 8 (Bui Duc Thinh): has Pending & Cancelled lessons but 0 payments
--   - Students 10 (Ngo Hai Dang) & 11 (Ly Thanh Truc): never had any lessons
INSERT INTO students (student_id, full_name, dob, phone) VALUES
(1, 'Le Hoang Minh Khoi', '2006-03-15', '0912345101'),
(2, 'Nguyen Phuong Anh', '2006-07-22', '0912345102'),
(3, 'Tran Quoc Tuan', '2006-01-10', '0912345103'),
(4, 'Pham Gia Bao', '2006-11-05', '0912345104'),
(5, 'Hoang Mai Linh', '2005-08-19', '0912345105'),
(6, 'Dang Tuan Kiet', '2005-12-25', '0912345106'),
(7, 'Vu Ngoc Ha', '2006-04-30', '0912345107'),
(8, 'Bui Duc Thinh', '2006-09-12', '0912345108'),
(9, 'Do Khanh Huyen', '2005-05-08', '0912345109'),
(10, 'Ngo Hai Dang', '2007-02-18', '0912345110'),
(11, 'Ly Thanh Truc', '2007-06-20', '0912345111');

-- 4. Seed data for lessons (23 lessons >= 12)
-- Coverage:
--   - January 2025 (lessons 1, 2, 6, 10, 22)
--   - February & March 2025 in Q1/2025 (lessons 3, 4, 7, 8, 11, 12, 15, 17, 19, 20, 21, 23)
--   - Outside Q1/2025: May & June 2025 (lessons 5, 9, 13, 18)
--   - Outside 2025: Year 2024 (lessons 14, 16)
--   - All 3 statuses: 16 Completed (1..16), 4 Pending (17..20), 3 Cancelled (21..23)
INSERT INTO lessons (lesson_id, student_id, tutor_id, lesson_date, status) VALUES
-- Group of 16 Completed lessons (lesson_id 1 -> 16)
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

-- Group of 4 Pending lessons (lesson_id 17 -> 20): no lesson report yet
(17, 4, 5, '2025-03-29', 'Pending'),
(18, 7, 3, '2025-05-25', 'Pending'),
(19, 8, 4, '2025-02-18', 'Pending'),
(20, 8, 2, '2025-03-30', 'Pending'),

-- Group of 3 Cancelled lessons (lesson_id 21 -> 23): cancelled, no lesson report
(21, 5, 1, '2025-02-05', 'Cancelled'),
(22, 8, 3, '2025-01-29', 'Cancelled'),
(23, 3, 5, '2025-03-15', 'Cancelled');

-- 5. Seed data for lesson_reports (16 reports >= 10)
-- Strict 1-1 rule: Exactly 16 Completed lessons (lesson_id 1..16) have a corresponding report
INSERT INTO lesson_reports (report_id, lesson_id, content, feedback, duration_minutes, fee) VALUES
(1,  1,  'Multidimensional NumPy arrays and Pandas DataFrame manipulation', 'Student mastered array slicing and vectorized data operations', 90, 500000.00),
(2,  2,  'Big-O algorithmic complexity analysis and Linked Lists', 'Implemented Singly and Doubly Linked Lists fluently in Python', 120, 600000.00),
(3,  3,  'Data cleaning techniques and handling missing values', 'Applied interpolation and outlier filtering effectively on real datasets', 90, 500000.00),
(4,  4,  'Stacks, Queues, and Recursive problem-solving in Python', 'Solved postfix expression evaluation and backtracking problems well', 120, 600000.00),
(5,  5,  'Entity-Relationship Diagram (ERD) design and relational mapping', 'Correctly identified primary keys, foreign keys, and cardinalities', 90, 550000.00),
(6,  6,  'Exploratory Data Analysis (EDA) and descriptive statistics with Python', 'Proficient in aggregating data using groupby and pivot_table', 90, 500000.00),
(7,  7,  'Database normalization (1NF, 2NF, 3NF, BCNF) and functional dependencies', 'Solid grasp of attribute closure and lossless-join decomposition', 90, 550000.00),
(8,  8,  'Binary Search Trees (BST) and tree traversal algorithms (Inorder, Preorder)', 'Wrote clean recursive code and understood tree balancing concepts', 120, 600000.00),
(9,  9,  'Uninformed search strategies (BFS, DFS) and state-space formulation', 'Accurately modeled 2D grid pathfinding problems', 90, 450000.00),
(10, 10, 'Advanced data visualization with Matplotlib and Seaborn', 'Designed clear distribution plots and correlation heatmaps', 90, 500000.00),
(11, 11, 'Feature engineering and data scaling techniques', 'Practiced MinMaxScaler and StandardScaler effectively on sample data', 90, 480000.00),
(12, 12, 'Advanced SQL queries: INNER/LEFT JOIN, GROUP BY, HAVING, and Subqueries', 'Wrote optimized queries and prevented chasm-trap fanout errors', 90, 550000.00),
(13, 13, 'Sorting algorithms (QuickSort, MergeSort) and Dynamic Programming', 'Optimized memory usage and runtime on large input arrays', 120, 600000.00),
(14, 14, 'Measuring National Income (GDP), Consumer Price Index (CPI), and inflation', 'Clearly distinguished nominal vs. real GDP and growth rates', 90, 400000.00),
(15, 15, 'Informed search algorithms (Greedy Best-First Search, A*) and heuristics', 'Proved admissibility and consistency of Manhattan distance heuristic', 90, 450000.00),
(16, 16, 'Aggregate Demand - Aggregate Supply (AD-AS) model and fiscal/monetary policy', 'Provided sharp analysis of interest rate and public spending impacts', 90, 400000.00);

-- 6. Seed data for payments (17 payment records >= 10)
-- Coverage:
--   - Multi-installment payments:
--       + lesson_id = 1: paid in 2 installments (300,000 + 200,000 = 500,000 -> fully paid)
--       + lesson_id = 6: paid in 2 installments (200,000 + 150,000 = 350,000 < 500,000 -> owes 150,000)
--   - Partially unpaid lessons: lesson_id = 6 (owes 150k), lesson_id = 10 (owes 200k), lesson_id = 13 (owes 200k)
--   - Completed lesson with 0 payments: lesson_id = 15 (Vu Ngoc Ha - owes 450,000)
--   - Payments in 2024: lesson_id = 14, 16 (outside 2025)
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
-- DATA INTEGRITY VERIFICATION QUERIES
-- ============================================================================

-- Verification 1A: Compare lesson counts by status against corresponding report counts
SELECT
    l.status,
    COUNT(l.lesson_id) AS total_lessons,
    COUNT(lr.report_id) AS total_reports
FROM lessons l
LEFT JOIN lesson_reports lr ON l.lesson_id = lr.lesson_id
GROUP BY l.status;

-- Verification 1B: Detect any anomalies (Completed lessons missing reports, or non-Completed lessons having reports)
SELECT
    l.lesson_id,
    l.status,
    lr.report_id
FROM lessons l
LEFT JOIN lesson_reports lr ON l.lesson_id = lr.lesson_id
WHERE (l.status = 'Completed' AND lr.report_id IS NULL)
   OR (l.status <> 'Completed' AND lr.report_id IS NOT NULL);

-- Verification 2A: Reconcile total paid amounts in payments against confirmed fees in lesson_reports
SELECT
    lr.lesson_id,
    l.status,
    lr.fee AS confirmed_fee,
    COALESCE(SUM(p.amount), 0) AS total_paid,
    lr.fee - COALESCE(SUM(p.amount), 0) AS remaining_debt,
    CASE
        WHEN COALESCE(SUM(p.amount), 0) <= lr.fee THEN 'VALID'
        ELSE 'VIOLATION_EXCEEDS_FEE'
    END AS validation_status
FROM lesson_reports lr
JOIN lessons l ON lr.lesson_id = l.lesson_id
LEFT JOIN payments p ON lr.lesson_id = p.lesson_id
GROUP BY lr.lesson_id, l.status, lr.fee
ORDER BY lr.lesson_id;

-- Verification 2B: Detect invalid payment records (payments without lesson_reports or total_paid > fee)
SELECT
    p.lesson_id,
    SUM(p.amount) AS total_paid,
    lr.fee
FROM payments p
LEFT JOIN lesson_reports lr ON p.lesson_id = lr.lesson_id
GROUP BY p.lesson_id, lr.fee
HAVING lr.fee IS NULL OR SUM(p.amount) > lr.fee;

-- ============================================================================
-- NEGATIVE TEST CASES: CONSTRAINT VIOLATION ILLUSTRATIONS (COMMENTED OUT)
-- ============================================================================

-- 1. Foreign Key Violation (FOREIGN KEY): student_id = 999 does not exist in students
-- INSERT INTO lessons (student_id, tutor_id, lesson_date, status)
-- VALUES (999, 1, '2025-04-01', 'Pending');
-- -> MySQL Error: ERROR 1452 (23000): Cannot add or update a child row: a foreign key constraint fails

-- 2. Check Constraint Violation (duration_minutes <= 0): Lesson duration is zero or negative
-- INSERT INTO lesson_reports (lesson_id, content, feedback, duration_minutes, fee)
-- VALUES (17, 'Review Data Analysis with Python', 'Good', 0, 450000.00);
-- -> MySQL Error: ERROR 3819 (HY000): Check constraint 'chk_report_duration' is violated.

-- 3. Check Constraint Violation (amount <= 0): Payment amount is zero or negative
-- INSERT INTO payments (lesson_id, amount, payment_date, method)
-- VALUES (1, -50000.00, '2025-01-15', 'Cash');
-- -> MySQL Error: ERROR 3819 (HY000): Check constraint 'chk_payment_amount' is violated.

-- 4. Unique Constraint Violation (duplicate lesson_id in lesson_reports): Lesson 1 already has a report
-- INSERT INTO lesson_reports (lesson_id, content, feedback, duration_minutes, fee)
-- VALUES (1, 'Duplicate report for lesson 1', 'Additional notes', 90, 500000.00);
-- -> MySQL Error: ERROR 1062 (23000): Duplicate entry '1' for key 'lesson_reports.lesson_id'
