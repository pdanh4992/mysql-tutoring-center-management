# Đề 01: Quản Lý Trung Tâm Gia Sư (`tutoring_mini`) — MySQL Database Project

> **Trường Đại học Kinh tế Quốc dân (NEU)**  
> **Khoa Khoa học Dữ liệu và Trí tuệ Nhân tạo (FDA)**  
> **Báo cáo Bài tập Thực hành Cơ sở Dữ liệu MySQL**

---

## 1. Giới thiệu Dự án

Dự án xây dựng trọn gói Cơ sở dữ liệu **Quản lý Trung tâm Gia sư (`tutoring_mini`)** trên Hệ quản trị CSDL **MySQL (InnoDB, UTF8MB4)** đáp ứng đầy đủ các quy tắc nghiệp vụ:
- Quản lý danh mục môn học (`subjects`), đội ngũ gia sư (`tutors`) và danh sách học viên (`students`).
- Theo dõi lịch học và vòng đời trạng thái buổi học (`lessons`: `Pending`, `Completed`, `Cancelled`).
- Lưu trữ báo cáo chuyên môn và học phí xác nhận sau buổi học (`lesson_reports` — quan hệ **1–1** chặt chẽ với các buổi học `Completed`).
- Quản lý giao dịch thu học phí một lần hoặc trả góp nhiều đợt (`payments` — quan hệ **1–N** với `lessons`) kèm kỹ thuật **chống cộng lặp chi phí (Anti-Fanout / Chasm Trap Prevention)** khi tổng hợp báo cáo tài chính và công nợ.

---

## 2. Cấu trúc Thư mục Repository

```text
De01_QuanLyTrungTamGiaSu/
├── schema.sql            # Phần A: Khởi tạo CSDL tutoring_mini & 6 bảng kèm PK, FK, UNIQUE, CHECK, ENUM
├── seed.sql              # Phần B: Nạp dữ liệu mẫu bao phủ mọi edge-case & Truy vấn kiểm chứng toàn vẹn
├── queries.sql           # Phần C: 10 Truy vấn khai thác dữ liệu chuẩn nghiệp vụ (chống cộng lặp chi phí)
├── views.sql             # Phần D: 3 VIEW toàn thời gian (v_detail, v_group_summary, v_debt)
├── Bao_cao_De_01.pdf     # Báo cáo học thuật PDF đầy đủ (Trang bìa Logo NEU & FDA, ERD, Phân tích & Output thực tế)
├── generate_report.py    # Script Python tự động kiểm thử MySQL và kết xuất Bao_cao_De_01.pdf
├── assets/               # Thư mục chứa Logo chính thức của Trường (NEU) và Khoa (FDA)
│   ├── logo_neu.png
│   ├── logo_fda.png
│   └── logo_fda_banner.png
├── .gitignore            # Cấu hình loại bỏ file rác (.DS_Store, __pycache__, venv, ...)
└── README.md             # Tài liệu hướng dẫn sử dụng và kiểm thử nhanh
```

---

## 3. Sơ đồ Lược đồ Cơ sở Dữ liệu (6 Bảng)

| STT | Tên Bảng | Khóa Chính (`PK`) | Khóa Ngoại (`FK`) | Ràng buộc Nổi bật (`UNIQUE`, `CHECK`, `ENUM`) |
|:---:|---|---|---|---|
| 1 | `subjects` | `subject_id` | — | `name NOT NULL UNIQUE` |
| 2 | `tutors` | `tutor_id` | `subject_id` → `subjects(subject_id)` | `email NOT NULL UNIQUE` |
| 3 | `students` | `student_id` | — | `full_name`, `dob (DATE)`, `phone` đều `NOT NULL` |
| 4 | `lessons` | `lesson_id` | `student_id` → `students(student_id)`<br>`tutor_id` → `tutors(tutor_id)` | `status ENUM('Pending', 'Completed', 'Cancelled') NOT NULL` |
| 5 | `lesson_reports` | `report_id` | `lesson_id` → `lessons(lesson_id)` | `lesson_id UNIQUE` (Quan hệ 1–1)<br>`CHECK (duration_minutes > 0)`<br>`CHECK (fee >= 0)` |
| 6 | `payments` | `payment_id` | `lesson_id` → `lessons(lesson_id)` | Quan hệ 1–N (Hỗ trợ trả góp nhiều lần)<br>`CHECK (amount > 0)`<br>`method ENUM('Cash', 'BankTransfer', 'Card')` |

---

## 4. Hướng dẫn Chạy Kiểm thử Nhanh

### Cách 1: Chạy trên MySQL CLI (Terminal / Command Prompt)

Chạy tuần tự 4 tệp `.sql` từ đầu đến cuối trên MySQL Server mới hoàn toàn:

```bash
mysql -u root -p --default-character-set=utf8mb4 < schema.sql
mysql -u root -p --default-character-set=utf8mb4 -t < seed.sql
mysql -u root -p --default-character-set=utf8mb4 -t < queries.sql
mysql -u root -p --default-character-set=utf8mb4 -t < views.sql
```

Hoặc chạy gộp trong 1 lệnh duy nhất:

```bash
cat schema.sql seed.sql queries.sql views.sql | mysql -u root -p --default-character-set=utf8mb4 -t
```

### Cách 2: Chạy trên MySQL Workbench

1. Mở **MySQL Workbench** và kết nối tới MySQL Server (`Local instance 3306`).
2. Vào menu **File → Open SQL Script...** và mở lần lượt theo đúng thứ tự:
   - Bước 1: Mở `schema.sql` → Nhấn biểu tượng ⚡ (**Execute**) để tạo CSDL `tutoring_mini` và 6 bảng.
   - Bước 2: Mở `seed.sql` → Nhấn ⚡ để nạp dữ liệu mẫu và xem kết quả 4 bảng kiểm chứng tự động.
   - Bước 3: Mở `queries.sql` → Nhấn ⚡ để xem kết quả của 10 câu truy vấn từ Câu 1 đến Câu 10.
   - Bước 4: Mở `views.sql` → Nhấn ⚡ để khởi tạo và xem kết quả của 3 VIEW (`v_detail`, `v_group_summary`, `v_debt`).

### Cách 3: Tự động Kết xuất lại Báo cáo PDF

Nếu muốn chỉnh sửa thông tin hoặc tái tạo tệp `Bao_cao_De_01.pdf`:

```bash
python3 generate_report.py
```

---

## 5. Thành viên Thực hiện

| STT | Họ và Tên | Mã Sinh viên | Đơn vị |
|:---:|---|---|---|
| 1 | **Phạm Ngọc Danh** | `11251809` | Khoa KHDL & TTNT (FDA - NEU) |
| 2 | **Nguyễn Mạnh Dũng** | `11252140` | Khoa KHDL & TTNT (FDA - NEU) |
| 3 | **Hoàng Đức Dương** | `11252228` | Khoa KHDL & TTNT (FDA - NEU) |
