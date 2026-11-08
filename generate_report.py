#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script tự động kiểm thử 4 tệp SQL trên MySQL Server thực tế và kết xuất
Báo cáo học thuật chuyên nghiệp: Bao_cao_De_01.pdf
Đề 01: Quản lý trung tâm gia sư (tutoring_mini)
"""

import base64
import html
import subprocess
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
PDF_OUTPUT = BASE_DIR / "Bao_cao_De_01.pdf"
HTML_OUTPUT = BASE_DIR / "report_preview.html"

MYSQLD_BIN = "/usr/local/mysql/bin/mysqld"
MYSQL_BIN = "/usr/local/mysql/bin/mysql"
MYSQLADMIN_BIN = "/usr/local/mysql/bin/mysqladmin"
TMP_MYSQL_DIR = Path("/tmp/mysql_de01")
MYSQL_SOCK = TMP_MYSQL_DIR / "run" / "mysql.sock"


def img_to_data_uri(path: Path) -> str:
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/png;base64,{b64}"


def ensure_mysql_running() -> bool:
    """Khởi động instance MySQL cục bộ phục vụ kiểm thử và trích xuất kết quả."""
    if MYSQL_SOCK.exists():
        res = subprocess.run(
            [MYSQL_BIN, "-u", "root", f"--socket={MYSQL_SOCK}", "-e", "SELECT 1;"],
            capture_output=True,
            text=True,
        )
        if res.returncode == 0:
            return False

    subprocess.run(["rm", "-rf", str(TMP_MYSQL_DIR)], check=True)
    (TMP_MYSQL_DIR / "data").mkdir(parents=True, exist_ok=True)
    (TMP_MYSQL_DIR / "run").mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            MYSQLD_BIN,
            "--initialize-insecure",
            f"--datadir={TMP_MYSQL_DIR / 'data'}",
            "--basedir=/usr/local/mysql",
        ],
        check=True,
        capture_output=True,
    )

    log_file = open(TMP_MYSQL_DIR / "run" / "mysqld.log", "w")
    subprocess.Popen(
        [
            MYSQLD_BIN,
            f"--datadir={TMP_MYSQL_DIR / 'data'}",
            "--basedir=/usr/local/mysql",
            f"--socket={MYSQL_SOCK}",
            "--port=33070",
            f"--pid-file={TMP_MYSQL_DIR / 'run' / 'mysql.pid'}",
            "--mysqlx=0",
        ],
        stdout=log_file,
        stderr=log_file,
    )

    for _ in range(30):
        time.sleep(0.3)
        res = subprocess.run(
            [MYSQL_BIN, "-u", "root", f"--socket={MYSQL_SOCK}", "-e", "SELECT 1;"],
            capture_output=True,
            text=True,
        )
        if res.returncode == 0:
            return True
    raise RuntimeError("Không thể khởi động MySQL Server để trích xuất dữ liệu.")


def stop_mysql():
    if MYSQL_SOCK.exists():
        subprocess.run(
            [MYSQLADMIN_BIN, "-u", "root", f"--socket={MYSQL_SOCK}", "shutdown"],
            capture_output=True,
        )


def run_sql_file(filename: str):
    sql_path = BASE_DIR / filename
    with open(sql_path, "r", encoding="utf-8") as f:
        res = subprocess.run(
            [
                MYSQL_BIN,
                "-u",
                "root",
                f"--socket={MYSQL_SOCK}",
                "--default-character-set=utf8mb4",
            ],
            stdin=f,
            capture_output=True,
            text=True,
        )
    if res.returncode != 0:
        raise RuntimeError(f"Lỗi khi chạy {filename}:\n{res.stderr}")


def run_query(sql: str):
    """Chạy câu lệnh SELECT trên MySQL và trả về (headers, rows)."""
    res = subprocess.run(
        [
            MYSQL_BIN,
            "-u",
            "root",
            f"--socket={MYSQL_SOCK}",
            "--default-character-set=utf8mb4",
            "--batch",
            "--raw",
            "tutoring_mini",
            "-e",
            sql,
        ],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        raise RuntimeError(f"Lỗi truy vấn SQL:\n{res.stderr}\nSQL:\n{sql}")
    lines = [line for line in res.stdout.splitlines() if line.strip() != ""]
    if not lines:
        return [], []
    headers = lines[0].split("\t")
    rows = [line.split("\t") for line in lines[1:]]
    return headers, rows


def render_table(headers, rows, caption=None, compact=False):
    if not headers:
        empty_html = (
            '<div class="empty-result">✓ Kết quả truy vấn: <strong>0 dòng (Tập rỗng)</strong> '
            "— Không có bản ghi nào vi phạm ràng buộc!</div>"
        )
        if caption:
            return f'<div class="table-wrap">{empty_html}<div class="table-caption">{caption}</div></div>'
        return empty_html

    cls = "data-table compact-table" if compact else "data-table"
    th_html = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body_rows = []
    for r in rows:
        tds = []
        for cell in r:
            if cell == "NULL":
                tds.append('<td class="null-cell">NULL</td>')
            elif cell.replace(".", "", 1).replace("-", "", 1).isdigit() and (
                "." in cell or len(cell) <= 4
            ):
                tds.append(f'<td class="num-cell">{html.escape(cell)}</td>')
            elif cell in ("Completed", "Pending", "Cancelled", "HOP_LE"):
                badge_cls = {
                    "Completed": "badge-completed",
                    "Pending": "badge-pending",
                    "Cancelled": "badge-cancelled",
                    "HOP_LE": "badge-completed",
                }[cell]
                tds.append(
                    f'<td class="center-cell"><span class="status-badge {badge_cls}">{html.escape(cell)}</span></td>'
                )
            else:
                tds.append(f"<td>{html.escape(cell)}</td>")
        body_rows.append("<tr>" + "".join(tds) + "</tr>")

    cap_html = f'<div class="table-caption">{caption}</div>' if caption else ""
    return f"""
    <div class="table-wrap">
        <table class="{cls}">
            <thead><tr>{th_html}</tr></thead>
            <tbody>{''.join(body_rows)}</tbody>
        </table>
        {cap_html}
    </div>
    """


def build_erd_svg() -> str:
    """Dựng sơ đồ quan hệ thực thể (ERD) dạng Vector SVG cân đối, rõ nét, không tràn chữ."""
    return """
    <div class="erd-container">
      <svg viewBox="0 0 960 430" xmlns="http://www.w3.org/2000/svg" class="erd-svg">
        <defs>
          <marker id="arrow-blue" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#1e3a8a"/>
          </marker>
          <marker id="arrow-green" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#047857"/>
          </marker>
          <marker id="arrow-amber" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#b45309"/>
          </marker>
          <filter id="shadow" x="-4%" y="-4%" width="108%" height="110%">
            <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#0f172a" flood-opacity="0.08"/>
          </filter>
        </defs>

        <!-- Background Box -->
        <rect x="2" y="2" width="956" height="426" rx="10" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5"/>

        <!-- Relationship Connector Lines -->
        <!-- 1. subjects (1) -> (N) 2. tutors -->
        <path d="M 245 95 L 330 95" stroke="#1e3a8a" stroke-width="2" fill="none" marker-end="url(#arrow-blue)"/>
        <text x="255" y="87" font-size="11" font-weight="bold" fill="#1e40af">1</text>
        <text x="312" y="87" font-size="11" font-weight="bold" fill="#1e40af">N</text>

        <!-- 2. tutors (1) -> (N) 4. lessons -->
        <path d="M 465 170 L 465 225" stroke="#1e3a8a" stroke-width="2" fill="none" marker-end="url(#arrow-blue)"/>
        <text x="474" y="186" font-size="11" font-weight="bold" fill="#1e40af">1</text>
        <text x="474" y="218" font-size="11" font-weight="bold" fill="#1e40af">N</text>

        <!-- 3. students (1) -> (N) 4. lessons -->
        <path d="M 245 305 L 330 305" stroke="#1e3a8a" stroke-width="2" fill="none" marker-end="url(#arrow-blue)"/>
        <text x="255" y="297" font-size="11" font-weight="bold" fill="#1e40af">1</text>
        <text x="312" y="297" font-size="11" font-weight="bold" fill="#1e40af">N</text>

        <!-- 4. lessons (1) -> (0..1) 5. lesson_reports -->
        <path d="M 600 265 L 638 265 L 638 110 L 695 110" stroke="#047857" stroke-width="2.2" fill="none" marker-end="url(#arrow-green)"/>
        <text x="610" y="257" font-size="11" font-weight="bold" fill="#047857">1</text>
        <rect x="612" y="78" width="76" height="18" rx="4" fill="#ecfdf5" stroke="#6ee7b7" stroke-width="1"/>
        <text x="650" y="90" text-anchor="middle" font-size="10" font-weight="bold" fill="#047857">0..1 (1-1)</text>

        <!-- 4. lessons (1) -> (0..N) 6. payments -->
        <path d="M 600 320 L 695 320" stroke="#b45309" stroke-width="2.2" fill="none" marker-end="url(#arrow-amber)"/>
        <text x="610" y="312" font-size="11" font-weight="bold" fill="#b45309">1</text>
        <text x="660" y="312" font-size="11" font-weight="bold" fill="#b45309">0..N</text>

        <!-- TABLE 1: subjects -->
        <g filter="url(#shadow)">
          <rect x="20" y="40" width="225" height="105" rx="6" fill="#ffffff" stroke="#1e3a8a" stroke-width="1.5"/>
          <rect x="20" y="40" width="225" height="28" rx="6" fill="#1e3a8a"/>
          <text x="132" y="59" text-anchor="middle" fill="#ffffff" font-weight="bold" font-size="12.5">1. subjects</text>
          <text x="32" y="88" font-size="11" fill="#0f172a"><tspan font-weight="bold" fill="#b91c1c">PK</tspan>  subject_id : INT</text>
          <text x="32" y="112" font-size="11" fill="#0f172a"><tspan font-weight="bold" fill="#0369a1">UQ</tspan>  name : VARCHAR(100)</text>
          <text x="32" y="132" font-size="9.5" fill="#64748b" font-style="italic">NOT NULL UNIQUE</text>
        </g>

        <!-- TABLE 2: tutors -->
        <g filter="url(#shadow)">
          <rect x="330" y="25" width="270" height="145" rx="6" fill="#ffffff" stroke="#1e3a8a" stroke-width="1.5"/>
          <rect x="330" y="25" width="270" height="28" rx="6" fill="#1e3a8a"/>
          <text x="465" y="44" text-anchor="middle" fill="#ffffff" font-weight="bold" font-size="12.5">2. tutors</text>
          <text x="342" y="72" font-size="11" fill="#0f172a"><tspan font-weight="bold" fill="#b91c1c">PK</tspan>  tutor_id : INT</text>
          <text x="342" y="93" font-size="11" fill="#0f172a">     full_name : VARCHAR(100) NOT NULL</text>
          <text x="342" y="114" font-size="11" fill="#0f172a"><tspan font-weight="bold" fill="#0369a1">UQ</tspan>  email : VARCHAR(150) NOT NULL</text>
          <text x="342" y="135" font-size="11" fill="#0f172a">     qualification : VARCHAR(150) NOT NULL</text>
          <text x="342" y="156" font-size="11" fill="#0f172a"><tspan font-weight="bold" fill="#7c3aed">FK</tspan>  subject_id : INT NOT NULL</text>
        </g>

        <!-- TABLE 3: students -->
        <g filter="url(#shadow)">
          <rect x="20" y="230" width="225" height="140" rx="6" fill="#ffffff" stroke="#1e3a8a" stroke-width="1.5"/>
          <rect x="20" y="230" width="225" height="28" rx="6" fill="#1e3a8a"/>
          <text x="132" y="249" text-anchor="middle" fill="#ffffff" font-weight="bold" font-size="12.5">3. students</text>
          <text x="32" y="278" font-size="11" fill="#0f172a"><tspan font-weight="bold" fill="#b91c1c">PK</tspan>  student_id : INT</text>
          <text x="32" y="301" font-size="11" fill="#0f172a">     full_name : VARCHAR(100) NOT NULL</text>
          <text x="32" y="324" font-size="11" fill="#0f172a">     dob : DATE NOT NULL</text>
          <text x="32" y="347" font-size="11" fill="#0f172a">     phone : VARCHAR(20) NOT NULL</text>
        </g>

        <!-- TABLE 4: lessons -->
        <g filter="url(#shadow)">
          <rect x="330" y="225" width="270" height="150" rx="6" fill="#ffffff" stroke="#1e40af" stroke-width="2"/>
          <rect x="330" y="225" width="270" height="28" rx="6" fill="#1e40af"/>
          <text x="465" y="244" text-anchor="middle" fill="#ffffff" font-weight="bold" font-size="12.5">4. lessons (Bảng Trung tâm)</text>
          <text x="342" y="272" font-size="11" fill="#0f172a"><tspan font-weight="bold" fill="#b91c1c">PK</tspan>  lesson_id : INT</text>
          <text x="342" y="293" font-size="11" fill="#0f172a"><tspan font-weight="bold" fill="#7c3aed">FK</tspan>  student_id : INT NOT NULL</text>
          <text x="342" y="314" font-size="11" fill="#0f172a"><tspan font-weight="bold" fill="#7c3aed">FK</tspan>  tutor_id : INT NOT NULL</text>
          <text x="342" y="335" font-size="11" fill="#0f172a">     lesson_date : DATE NOT NULL</text>
          <text x="342" y="356" font-size="11" fill="#0f172a">     status : ENUM('Pending','Completed','Cancelled')</text>
        </g>

        <!-- TABLE 5: lesson_reports -->
        <g filter="url(#shadow)">
          <rect x="695" y="25" width="245" height="165" rx="6" fill="#ffffff" stroke="#047857" stroke-width="1.8"/>
          <rect x="695" y="25" width="245" height="28" rx="6" fill="#047857"/>
          <text x="817" y="44" text-anchor="middle" fill="#ffffff" font-weight="bold" font-size="12.5">5. lesson_reports (Quan hệ 1-1)</text>
          <text x="706" y="70" font-size="11" fill="#0f172a"><tspan font-weight="bold" fill="#b91c1c">PK</tspan>  report_id : INT</text>
          <text x="706" y="91" font-size="11" fill="#0f172a"><tspan font-weight="bold" fill="#047857">FK,UQ</tspan> lesson_id : INT NOT NULL UNIQUE</text>
          <text x="706" y="112" font-size="11" fill="#0f172a">     content : TEXT NOT NULL</text>
          <text x="706" y="133" font-size="11" fill="#0f172a">     feedback : TEXT NOT NULL</text>
          <text x="706" y="154" font-size="11" fill="#0f172a"><tspan font-weight="bold" fill="#b45309">CK</tspan>  duration_minutes : INT (&gt; 0)</text>
          <text x="706" y="175" font-size="11" fill="#0f172a"><tspan font-weight="bold" fill="#b45309">CK</tspan>  fee : DECIMAL(12,2) (&gt;= 0)</text>
        </g>

        <!-- TABLE 6: payments -->
        <g filter="url(#shadow)">
          <rect x="695" y="225" width="245" height="150" rx="6" fill="#ffffff" stroke="#b45309" stroke-width="1.8"/>
          <rect x="695" y="225" width="245" height="28" rx="6" fill="#b45309"/>
          <text x="817" y="244" text-anchor="middle" fill="#ffffff" font-weight="bold" font-size="12.5">6. payments (Quan hệ 1-N)</text>
          <text x="706" y="272" font-size="11" fill="#0f172a"><tspan font-weight="bold" fill="#b91c1c">PK</tspan>  payment_id : INT</text>
          <text x="706" y="293" font-size="11" fill="#0f172a"><tspan font-weight="bold" fill="#7c3aed">FK</tspan>  lesson_id : INT NOT NULL</text>
          <text x="706" y="314" font-size="11" fill="#0f172a"><tspan font-weight="bold" fill="#b45309">CK</tspan>  amount : DECIMAL(12,2) (&gt; 0)</text>
          <text x="706" y="335" font-size="11" fill="#0f172a">     payment_date : DATE NOT NULL</text>
          <text x="706" y="356" font-size="11" fill="#0f172a">     method : ENUM('Cash','BankTransfer','Card')</text>
        </g>

        <!-- Legend at bottom -->
        <rect x="20" y="392" width="920" height="24" rx="4" fill="#e2e8f0"/>
        <text x="480" y="408" text-anchor="middle" font-size="10.8" fill="#1e293b" font-weight="600">
          Chú giải: [PK] Khóa chính (Primary Key)   |   [FK] Khóa ngoại (Foreign Key)   |   [UQ] Duy nhất (UNIQUE)   |   [CK] Ràng buộc miền giá trị (CHECK Constraint)
        </text>
      </svg>
      <div class="table-caption">Hình 2.1: Sơ đồ Quan hệ Thực thể (ERD) của Cơ sở dữ liệu Quản lý Trung tâm Gia sư (<code>tutoring_mini</code>).</div>
    </div>
    """


def generate_html_report():
    started_by_us = ensure_mysql_running()
    try:
        # Chạy tuần tự 4 tệp SQL
        run_sql_file("schema.sql")
        run_sql_file("seed.sql")
        run_sql_file("queries.sql")
        run_sql_file("views.sql")

        # Đọc nội dung 4 file SQL
        schema_code = (BASE_DIR / "schema.sql").read_text(encoding="utf-8")

        # Trích xuất các bảng dữ liệu đã nạp trong seed.sql
        tbl_subjects = render_table(
            *run_query("SELECT * FROM subjects ORDER BY subject_id;"),
            caption="Bảng 3.1: Dữ liệu bảng danh mục môn học (subjects — 6 bản ghi).",
            compact=True,
        )
        tbl_tutors = render_table(
            *run_query("SELECT * FROM tutors ORDER BY tutor_id;"),
            caption="Bảng 3.2: Dữ liệu bảng danh sách gia sư (tutors — 6 bản ghi).",
            compact=True,
        )
        tbl_students = render_table(
            *run_query("SELECT * FROM students ORDER BY student_id;"),
            caption="Bảng 3.3: Dữ liệu bảng danh sách học viên (students — 11 bản ghi).",
            compact=True,
        )
        tbl_lessons = render_table(
            *run_query("SELECT * FROM lessons ORDER BY lesson_id;"),
            caption="Bảng 3.4: Dữ liệu bảng lịch sử buổi học (lessons — 23 bản ghi).",
            compact=True,
        )
        tbl_reports = render_table(
            *run_query(
                "SELECT report_id, lesson_id, content, feedback, duration_minutes, fee FROM lesson_reports ORDER BY report_id;"
            ),
            caption="Bảng 3.5: Dữ liệu bảng báo cáo kết quả buổi học (lesson_reports — 16 bản ghi, tỷ lệ 1-1 với buổi Completed).",
            compact=True,
        )
        tbl_payments = render_table(
            *run_query("SELECT * FROM payments ORDER BY payment_id;"),
            caption="Bảng 3.6: Dữ liệu bảng giao dịch thanh toán (payments — 17 bản ghi).",
            compact=True,
        )

        # Kết quả kiểm chứng trong seed.sql
        ver_1a = render_table(
            *run_query(
                """
                SELECT l.status, COUNT(l.lesson_id) AS total_lessons, COUNT(lr.report_id) AS total_reports
                FROM lessons l LEFT JOIN lesson_reports lr ON l.lesson_id = lr.lesson_id
                GROUP BY l.status;
                """
            ),
            caption="Bảng 3.7: Kết quả Kiểm chứng 1A — Đối chiếu trạng thái buổi học và số lượng báo cáo.",
        )
        ver_1b = render_table(
            *run_query(
                """
                SELECT l.lesson_id, l.status, lr.report_id
                FROM lessons l LEFT JOIN lesson_reports lr ON l.lesson_id = lr.lesson_id
                WHERE (l.status = 'Completed' AND lr.report_id IS NULL)
                   OR (l.status <> 'Completed' AND lr.report_id IS NOT NULL);
                """
            ),
            caption="Bảng 3.8: Kết quả Kiểm chứng 1B — Kiểm tra buổi học vi phạm quy tắc báo cáo 1-1.",
        )
        ver_2a = render_table(
            *run_query(
                """
                SELECT lr.lesson_id, l.status, lr.fee AS confirmed_fee,
                       COALESCE(SUM(p.amount), 0) AS total_paid,
                       lr.fee - COALESCE(SUM(p.amount), 0) AS remaining_debt,
                       CASE WHEN COALESCE(SUM(p.amount), 0) <= lr.fee THEN 'HOP_LE' ELSE 'VI_PHAM' END AS validation_status
                FROM lesson_reports lr
                JOIN lessons l ON lr.lesson_id = l.lesson_id
                LEFT JOIN payments p ON lr.lesson_id = p.lesson_id
                GROUP BY lr.lesson_id, l.status, lr.fee
                ORDER BY lr.lesson_id;
                """
            ),
            caption="Bảng 3.9: Kết quả Kiểm chứng 2A — Đối chiếu học phí xác nhận và tổng tiền thực thu theo từng buổi học.",
            compact=True,
        )
        ver_2b = render_table(
            *run_query(
                """
                SELECT p.lesson_id, SUM(p.amount) AS total_paid, lr.fee
                FROM payments p LEFT JOIN lesson_reports lr ON p.lesson_id = lr.lesson_id
                GROUP BY p.lesson_id, lr.fee
                HAVING lr.fee IS NULL OR SUM(p.amount) > lr.fee;
                """
            ),
            caption="Bảng 3.10: Kết quả Kiểm chứng 2B — Kiểm tra giao dịch thu tiền vượt học phí hoặc chưa có báo cáo.",
        )

        # 10 Truy vấn trong queries.sql
        q_specs = [
            {
                "num": 1,
                "title": "Liệt kê các buổi học Completed trong tháng 01/2025",
                "req": "Liệt kê các buổi học <code>Completed</code> trong tháng 01/2025, kèm mã + tên học viên, mã + tên gia sư và <code>lesson_date</code>.",
                "analysis": (
                    "Sử dụng phép nối trong (<code>INNER JOIN</code>) từ bảng <code>lessons</code> sang bảng <code>students</code> "
                    "(theo <code>student_id</code>) và bảng <code>tutors</code> (theo <code>tutor_id</code>). "
                    "Áp dụng bộ lọc <code>l.status = 'Completed'</code> kết hợp miền thời gian nửa mở "
                    "<code>l.lesson_date &gt;= '2025-01-01' AND l.lesson_date &lt; '2025-02-01'</code> (giúp tận dụng chỉ mục B-Tree và an toàn tuyệt đối cho cả kiểu <code>DATE</code> lẫn <code>DATETIME</code>). "
                    "Buổi học số 22 (ngày <code>2025-01-29</code> của học viên Bùi Đức Thịnh) có trạng thái <code>Cancelled</code> nên bị loại bỏ chính xác."
                ),
                "sql": """SELECT
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
ORDER BY l.lesson_date ASC, l.lesson_id ASC;""",
            },
            {
                "num": 2,
                "title": "Đếm tổng số buổi học theo từng môn học trong Quý I/2025",
                "req": "Đếm tổng số buổi học theo từng môn học trong Quý I/2025 (<code>01/01/2025</code> đến hết <code>31/03/2025</code>), tính mọi trạng thái; hiển thị cả nhóm có số lượng bằng <code>0</code>.",
                "analysis": (
                    "Xuất phát từ bảng gốc <code>subjects</code> và dùng <code>LEFT JOIN</code> sang <code>tutors</code> rồi tới <code>lessons</code>. "
                    "<strong>Kỹ thuật trọng tâm:</strong> Điều kiện lọc thời gian Quý I/2025 (<code>l.lesson_date &gt;= '2025-01-01' AND l.lesson_date &lt; '2025-04-01'</code>) "
                    "bắt buộc phải đặt ngay trong mệnh đề <code>ON</code> của phép <code>LEFT JOIN lessons</code> thay vì đặt ở <code>WHERE</code>. "
                    "Nếu đặt ở <code>WHERE</code>, các môn học không có giao dịch trong Quý I/2025 (như <em>Kinh tế vĩ mô 1</em> chỉ có buổi học năm 2024 và <em>Pháp luật đại cương</em> chưa có buổi học nào) sẽ bị biến thành <code>INNER JOIN</code> và biến mất khỏi kết quả. "
                    "Hàm <code>COUNT(l.lesson_id)</code> chỉ đếm các dòng khác <code>NULL</code> nên trả về đúng <code>0</code> cho 2 môn học này."
                ),
                "sql": """SELECT
    sub.subject_id,
    sub.name AS subject_name,
    COUNT(l.lesson_id) AS total_lessons_q1_2025
FROM subjects sub
LEFT JOIN tutors t ON sub.subject_id = t.subject_id
LEFT JOIN lessons l ON t.tutor_id = l.tutor_id
    AND l.lesson_date >= '2025-01-01'
    AND l.lesson_date < '2025-04-01'
GROUP BY sub.subject_id, sub.name
ORDER BY total_lessons_q1_2025 DESC, sub.subject_id ASC;""",
            },
            {
                "num": 3,
                "title": "Liệt kê học viên có buổi học chưa có báo cáo (loại trừ Cancelled)",
                "req": "Liệt kê các học viên có ít nhất một buổi học chưa có báo cáo buổi học, loại trừ <code>Cancelled</code>. Mỗi người chỉ xuất hiện một lần.",
                "analysis": (
                    "Thực hiện <code>JOIN</code> từ <code>students</code> sang <code>lessons</code> và <code>LEFT JOIN</code> sang <code>lesson_reports</code>. "
                    "Buổi học chưa có báo cáo được xác định bởi điều kiện <code>lr.report_id IS NULL</code> (anti-join pattern), đồng thời loại trừ các buổi đã hủy bằng <code>l.status &lt;&gt; 'Cancelled'</code>. "
                    "Do một học viên có thể có nhiều buổi học đang chờ báo cáo (ví dụ học viên <code>student_id = 8</code> Bùi Đức Thịnh có 2 buổi <code>Pending</code> là buổi 19 và 20), "
                    "ta sử dụng từ khóa <code>SELECT DISTINCT</code> để đảm bảo mỗi học viên chỉ xuất hiện duy nhất một lần. Học viên số 5 (Hoàng Mai Linh) chỉ có buổi chưa báo cáo thuộc trạng thái <code>Cancelled</code> nên được loại trừ chính xác."
                ),
                "sql": """SELECT DISTINCT
    s.student_id,
    s.full_name AS student_name
FROM students s
JOIN lessons l ON s.student_id = l.student_id
LEFT JOIN lesson_reports lr ON l.lesson_id = lr.lesson_id
WHERE l.status <> 'Cancelled'
  AND lr.report_id IS NULL
ORDER BY s.student_id ASC;""",
            },
            {
                "num": 4,
                "title": "Tính học phí trung bình trên một giao dịch Completed của từng môn học",
                "req": "Tính học phí trung bình trên một giao dịch <code>Completed</code> của từng môn học, xét toàn bộ thời gian; chỉ lấy nhóm đã phát sinh chi phí.",
                "analysis": (
                    "Sử dụng <code>INNER JOIN</code> xuyên suốt từ <code>subjects → tutors → lessons → lesson_reports</code> với điều kiện <code>l.status = 'Completed'</code>. "
                    "Vì đề bài yêu cầu <em>chỉ lấy nhóm đã phát sinh chi phí</em>, phép <code>INNER JOIN</code> tự động loại bỏ môn <em>Pháp luật đại cương</em> (chưa có buổi học hoàn thành). "
                    "<strong>Chống cộng lặp chi phí:</strong> Tuyệt đối không nối bảng <code>payments</code> trong câu truy vấn này vì nếu một buổi học trả góp 2 lần (như <code>lesson_id = 1</code> và <code>lesson_id = 6</code> của môn <em>Phân tích dữ liệu với Python</em>), "
                    "phép nối với <code>payments</code> sẽ nhân đôi bản ghi học phí của buổi đó và làm sai lệch giá trị trung bình <code>AVG(lr.fee)</code>."
                ),
                "sql": """SELECT
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
ORDER BY avg_completed_fee DESC, sub.subject_id ASC;""",
            },
            {
                "num": 5,
                "title": "Top 3 gia sư có nhiều buổi học Completed nhất trong năm 2025",
                "req": "Liệt kê 3 gia sư có nhiều buổi học <code>Completed</code> nhất trong năm 2025. Nếu bằng nhau, ưu tiên <code>tutor_id</code> tăng dần; chỉ lấy đối tượng có giao dịch.",
                "analysis": (
                    "Dùng <code>INNER JOIN</code> giữa <code>tutors</code> và <code>lessons</code> kèm điều kiện <code>l.status = 'Completed'</code> và năm 2025 (<code>l.lesson_date &gt;= '2025-01-01' AND l.lesson_date &lt; '2026-01-01'</code>) "
                    "để chỉ lấy các gia sư thực sự có giao dịch hoàn thành trong năm 2025. "
                    "Gom nhóm theo <code>t.tutor_id, t.full_name</code> và sắp xếp theo <code>ORDER BY completed_lessons_2025 DESC, t.tutor_id ASC LIMIT 3</code>. "
                    "Trên bộ dữ liệu thực tế, gia sư số 1 (TS. Trần Hùng) và gia sư số 2 (TS. Vũ Đức Minh) cùng có 4 buổi <code>Completed</code>, hệ thống tự động ưu tiên xếp <code>tutor_id = 1</code> đứng trước."
                ),
                "sql": """SELECT
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
LIMIT 3;""",
            },
            {
                "num": 6,
                "title": "Tổng số tiền từng học viên đã thanh toán trong năm 2025",
                "req": "Tính tổng số tiền từng học viên đã thanh toán trong năm 2025 theo <code>payment_date</code>; hiển thị cả người chưa trả tiền với tổng bằng <code>0</code>.",
                "analysis": (
                    "Bắt đầu từ bảng <code>students</code>, thực hiện <code>LEFT JOIN lessons</code> và <code>LEFT JOIN payments</code>. "
                    "Điều kiện lọc ngày thanh toán trong năm 2025 (<code>p.payment_date &gt;= '2025-01-01' AND p.payment_date &lt; '2026-01-01'</code>) được đặt ngay tại mệnh đề <code>ON</code> của phép <code>LEFT JOIN payments</code>. "
                    "Nhờ đó, cả những học viên chỉ thanh toán trong năm 2024 (học viên 6 Đặng Tuấn Kiệt, học viên 9 Đỗ Khánh Huyền), học viên nợ 100% (học viên 7 Vũ Ngọc Hà) và học viên chưa từng học (học viên 10 Ngô Hải Đăng, học viên 11 Lý Thanh Trúc) đều được giữ lại đầy đủ và hiển thị <code>0.00</code> thông qua hàm <code>COALESCE(SUM(p.amount), 0.00)</code>."
                ),
                "sql": """SELECT
    s.student_id,
    s.full_name AS student_name,
    COALESCE(SUM(p.amount), 0.00) AS total_paid_2025
FROM students s
LEFT JOIN lessons l ON s.student_id = l.student_id
LEFT JOIN payments p ON l.lesson_id = p.lesson_id
    AND p.payment_date >= '2025-01-01'
    AND p.payment_date < '2026-01-01'
GROUP BY s.student_id, s.full_name
ORDER BY total_paid_2025 DESC, s.student_id ASC;""",
            },
            {
                "num": 7,
                "title": "Liệt kê các học viên chưa có bất kỳ bản ghi thanh toán nào",
                "req": "Liệt kê các học viên chưa có bất kỳ bản ghi thanh toán nào trong toàn bộ dữ liệu, kể cả người chưa có giao dịch.",
                "analysis": (
                    "Thực hiện <code>LEFT JOIN</code> từ <code>students</code> sang <code>lessons</code> và <code>payments</code> trên toàn bộ thời gian. "
                    "Gom nhóm theo từng học viên và lọc bằng <code>HAVING COUNT(p.payment_id) = 0</code>. "
                    "Kết quả trả về đầy đủ 2 nhóm đối tượng: (1) Học viên đã có lịch sử buổi học nhưng chưa trả tiền lần nào (Vũ Ngọc Hà <code>student_id = 7</code>, Bùi Đức Thịnh <code>student_id = 8</code>) "
                    "và (2) Học viên mới đăng ký chưa từng phát sinh buổi học (Ngô Hải Đăng <code>student_id = 10</code>, Lý Thanh Trúc <code>student_id = 11</code>)."
                ),
                "sql": """SELECT
    s.student_id,
    s.full_name AS student_name,
    s.dob,
    s.phone
FROM students s
LEFT JOIN lessons l ON s.student_id = l.student_id
LEFT JOIN payments p ON l.lesson_id = p.lesson_id
GROUP BY s.student_id, s.full_name, s.dob, s.phone
HAVING COUNT(p.payment_id) = 0
ORDER BY s.student_id ASC;""",
            },
            {
                "num": 8,
                "title": "Xếp hạng toàn bộ học viên theo tổng học phí đã xác nhận giảm dần",
                "req": "Liệt kê toàn bộ học viên theo tổng học phí đã xác nhận giảm dần, không phụ thuộc đã thanh toán hay chưa; nếu bằng nhau, sắp theo mã tăng dần.",
                "analysis": (
                    "<strong>Chống cộng lặp chi phí:</strong> Học phí đã xác nhận nằm ở bảng <code>lesson_reports</code> (quan hệ 1-1 chặt chẽ với <code>lessons</code> nhờ ràng buộc <code>lesson_id UNIQUE</code>). "
                    "Do đó, ta chỉ thực hiện <code>LEFT JOIN</code> từ <code>students</code> sang <code>lessons</code> (lọc <code>l.status = 'Completed'</code>) và <code>lesson_reports</code> mà tuyệt đối không nối bảng <code>payments</code>. "
                    "Nếu nối thêm <code>payments</code>, học viên Lê Hoàng Minh Khôi (<code>student_id = 1</code>, có buổi học số 1 trả 2 lần) sẽ bị cộng lặp thêm 500,000 VNĐ. "
                    "Các học viên có cùng mức học phí (ví dụ học viên 6 và 9 cùng đạt <code>400000.00</code>; học viên 8, 10, 11 cùng đạt <code>0.00</code>) được sắp xếp chính xác theo <code>student_id ASC</code>."
                ),
                "sql": """SELECT
    s.student_id,
    s.full_name AS student_name,
    COALESCE(SUM(lr.fee), 0.00) AS total_confirmed_fee
FROM students s
LEFT JOIN lessons l ON s.student_id = l.student_id
    AND l.status = 'Completed'
LEFT JOIN lesson_reports lr ON l.lesson_id = lr.lesson_id
GROUP BY s.student_id, s.full_name
ORDER BY total_confirmed_fee DESC, s.student_id ASC;""",
            },
            {
                "num": 9,
                "title": "Tính tỷ lệ hủy buổi học của từng gia sư trong năm 2025",
                "req": "Tính tỷ lệ hủy của từng gia sư trong năm 2025: <code>(số buổi học Cancelled / tổng số buổi học của năm) * 100</code>. Làm tròn 2 chữ số thập phân; trả <code>NULL</code> nếu tổng bằng <code>0</code>.",
                "analysis": (
                    "Sử dụng <code>LEFT JOIN</code> từ <code>tutors</code> sang <code>lessons</code> với điều kiện năm 2025 đặt trong <code>ON</code> để giữ lại cả gia sư không có buổi dạy nào trong năm 2025 (gia sư số 6 ThS. Phạm Đức Chung chỉ dạy trong năm 2024). "
                    "Đếm số buổi hủy bằng biểu thức điều kiện <code>SUM(CASE WHEN l.status = 'Cancelled' THEN 1 ELSE 0 END)</code>. "
                    "Để xử lý chia cho 0 một cách an toàn và trả về <code>NULL</code> đúng yêu cầu khi tổng số buổi học trong năm bằng 0, ta dùng hàm <code>NULLIF(COUNT(l.lesson_id), 0)</code> ở mẫu số, sau đó bọc ngoài bằng <code>ROUND(..., 2)</code>."
                ),
                "sql": """SELECT
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
ORDER BY t.tutor_id ASC;""",
            },
            {
                "num": 10,
                "title": "Liệt kê các học viên có hơn 3 buổi học Completed trong năm 2025",
                "req": "Liệt kê các học viên có hơn 3 buổi học <code>Completed</code> trong năm 2025, kèm số lần; sắp số lần giảm dần.",
                "analysis": (
                    "Thực hiện <code>INNER JOIN</code> giữa <code>students</code> và <code>lessons</code>, lọc trạng thái <code>l.status = 'Completed'</code> và thời gian trong năm 2025 tại mệnh đề <code>WHERE</code>. "
                    "Gom nhóm theo từng học viên (<code>GROUP BY s.student_id, s.full_name</code>) và áp dụng điều kiện lọc sau gom nhóm <code>HAVING COUNT(l.lesson_id) &gt; 3</code> (tức từ 4 buổi trở lên). "
                    "Kết quả trích xuất chính xác 2 học viên tiêu biểu: Lê Hoàng Minh Khôi (5 buổi) và Nguyễn Phương Anh (4 buổi)."
                ),
                "sql": """SELECT
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
ORDER BY completed_lessons_2025 DESC, s.student_id ASC;""",
            },
        ]

        queries_html_blocks = []
        for q in q_specs:
            headers, rows = run_query(q["sql"])
            out_tbl = render_table(
                headers,
                rows,
                caption=f"Bảng 4.{q['num']}: Kết quả thực thi Truy vấn {q['num']} trên MySQL.",
            )
            queries_html_blocks.append(
                f"""
                <div class="query-card">
                    <div class="query-header">
                        <span class="query-badge">Truy vấn {q['num']}</span>
                        <h3>{q['title']}</h3>
                    </div>
                    <div class="query-body">
                        <p class="query-req"><strong>Yêu cầu đề bài:</strong> {q['req']}</p>
                        <p class="query-analysis"><strong>Phân tích &amp; Hướng giải quyết:</strong> {q['analysis']}</p>
                        <pre class="sql-code"><code>{html.escape(q['sql'])}</code></pre>
                        {out_tbl}
                    </div>
                </div>
                """
            )

        # Kết quả 3 VIEW trong views.sql
        tbl_v_detail = render_table(
            *run_query("SELECT * FROM v_detail ORDER BY lesson_id ASC;"),
            caption="Bảng 5.1: Kết quả truy vấn thực tế từ VIEW v_detail (23 bản ghi buổi học toàn thời gian, giữ cả fee = NULL).",
            compact=True,
        )
        tbl_v_group = render_table(
            *run_query("SELECT * FROM v_group_summary ORDER BY subject_id ASC;"),
            caption="Bảng 5.2: Kết quả truy vấn thực tế từ VIEW v_group_summary (Tổng hợp toàn bộ 6 môn học).",
        )
        tbl_v_debt = render_table(
            *run_query(
                "SELECT * FROM v_debt ORDER BY remaining_debt DESC, student_id ASC;"
            ),
            caption="Bảng 5.3: Kết quả truy vấn thực tế từ VIEW v_debt (Báo cáo công nợ của toàn bộ 11 học viên, chống cộng lặp chi phí).",
        )

    finally:
        if started_by_us:
            stop_mysql()

    neu_logo_uri = img_to_data_uri(ASSETS_DIR / "logo_neu.png")
    fda_logo_uri = img_to_data_uri(ASSETS_DIR / "logo_fda.png")
    erd_svg = build_erd_svg()

    html_doc = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>Báo Cáo Đề 01: Quản Lý Trung Tâm Gia Sư (tutoring_mini)</title>
<style>
  @page {{
    size: A4 portrait;
    margin: 18mm 16mm 18mm 16mm;
  }}
  @page :first {{
    margin: 12mm 14mm 12mm 14mm;
  }}
  * {{
    box-sizing: border-box;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 10.5pt;
    line-height: 1.52;
    color: #1e293b;
    margin: 0;
    padding: 0;
    background: #ffffff;
  }}

  /* ================= COVER PAGE ================= */
  .cover-page {{
    height: 271mm;
    border: 3px double #1e3a8a;
    padding: 10mm 12mm;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
    background: linear-gradient(180deg, #f8fafc 0%, #ffffff 22%, #ffffff 82%, #f1f5f9 100%);
    page-break-after: always;
  }}
  .cover-inner-border {{
    border: 1px solid #93c5fd;
    height: 100%;
    padding: 10mm 12mm;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}
  .cover-top {{
    text-align: center;
  }}
  .cover-top p {{
    text-align: center !important;
  }}
  .quoc-hieu {{
    font-size: 10.5pt;
    font-weight: 700;
    color: #334155;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    margin-bottom: 3px;
    text-align: center;
  }}
  .tieu-ngu {{
    font-size: 10.2pt;
    font-weight: 600;
    color: #475569;
    margin-bottom: 10px;
    text-align: center;
  }}
  .divider-short {{
    width: 140px;
    height: 1.5px;
    background: #475569;
    margin: 0 auto 16px auto;
  }}
  .uni-name {{
    font-size: 13.5pt;
    font-weight: 800;
    color: #1e3a8a;
    letter-spacing: 0.6px;
    margin: 0;
    text-align: center;
  }}
  .uni-name-en {{
    font-size: 9.5pt;
    font-weight: 600;
    color: #2563eb;
    letter-spacing: 1px;
    margin: 3px 0 10px 0;
    text-align: center;
  }}
  .faculty-name {{
    font-size: 12pt;
    font-weight: 800;
    color: #0f172a;
    margin: 0;
    text-align: center;
  }}
  .faculty-name-en {{
    font-size: 9pt;
    font-weight: 600;
    color: #0284c7;
    letter-spacing: 0.8px;
    margin: 3px 0 0 0;
    text-align: center;
  }}

  .logo-row {{
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 48px;
    margin: 18px 0 10px 0;
  }}
  .logo-box {{
    display: flex;
    flex-direction: column;
    align-items: center;
  }}
  .logo-box img {{
    width: 100px;
    height: 100px;
    object-fit: contain;
    filter: drop-shadow(0 3px 6px rgba(15, 23, 42, 0.12));
  }}
  .logo-caption {{
    font-size: 8.2pt;
    font-weight: 700;
    color: #475569;
    margin-top: 6px;
    letter-spacing: 0.5px;
  }}

  .cover-title-block {{
    text-align: center;
    padding: 16px 14px;
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    border-top: 2.5px solid #1e3a8a;
    border-bottom: 2.5px solid #1e3a8a;
    border-radius: 8px;
    margin: 8px 0;
  }}
  .report-type {{
    font-size: 13pt;
    font-weight: 800;
    color: #1e40af;
    letter-spacing: 1px;
    margin-bottom: 8px;
  }}
  .report-main-title {{
    font-size: 19pt;
    font-weight: 900;
    color: #0f172a;
    line-height: 1.28;
    margin: 0 0 10px 0;
    text-transform: uppercase;
  }}
  .report-db-badge {{
    display: inline-block;
    background: #1e3a8a;
    color: #ffffff;
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 10.5pt;
    font-weight: 700;
    padding: 4px 18px;
    border-radius: 20px;
  }}

  .cover-meta {{
    margin-top: 6px;
  }}
  .meta-info-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px 18px;
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 10px 16px;
    margin-bottom: 14px;
    font-size: 9.8pt;
  }}
  .meta-member-title {{
    font-size: 10pt;
    font-weight: 800;
    color: #1e3a8a;
    text-transform: uppercase;
    margin: 0 0 8px 0;
    letter-spacing: 0.4px;
    text-align: center;
  }}
  .member-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 9.5pt;
  }}
  .member-table th {{
    background: #1e3a8a;
    color: #ffffff;
    padding: 7px 10px;
    text-align: left;
    font-weight: 700;
  }}
  .member-table td {{
    padding: 7px 10px;
    border-bottom: 1px solid #cbd5e1;
    color: #1e293b;
  }}
  .member-table tr:nth-child(even) td {{
    background: #f1f5f9;
  }}
  .cover-footer {{
    text-align: center;
    font-size: 10pt;
    font-weight: 700;
    color: #334155;
    padding-top: 8px;
    border-top: 1px solid #cbd5e1;
  }}

  /* ================= SECTION STYLING ================= */
  .section-page-break {{
    page-break-before: always;
  }}
  .section-banner {{
    background: linear-gradient(90deg, #1e3a8a 0%, #2563eb 100%);
    color: #ffffff;
    padding: 9px 14px;
    border-radius: 6px;
    margin: 18px 0 12px 0;
    display: flex;
    align-items: center;
    page-break-after: avoid;
  }}
  .section-banner h1 {{
    font-size: 13.5pt;
    font-weight: 800;
    margin: 0;
    text-transform: uppercase;
    letter-spacing: 0.4px;
  }}
  h2 {{
    font-size: 11.5pt;
    font-weight: 800;
    color: #1e3a8a;
    border-left: 4px solid #2563eb;
    padding-left: 9px;
    margin: 14px 0 8px 0;
    page-break-after: avoid;
  }}
  h3 {{
    font-size: 10.5pt;
    font-weight: 700;
    color: #0f172a;
    margin: 10px 0 5px 0;
    page-break-after: avoid;
  }}
  p {{
    margin: 0 0 8px 0;
    text-align: justify;
  }}
  ul, ol {{
    margin: 0 0 10px 0;
    padding-left: 20px;
  }}
  li {{
    margin-bottom: 4px;
  }}
  code {{
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 9pt;
    background: #f1f5f9;
    color: #0f172a;
    padding: 1px 4px;
    border-radius: 3px;
    border: 1px solid #e2e8f0;
  }}

  /* ================= CALLOUT BOXES ================= */
  .callout {{
    background: #f8fafc;
    border-left: 4px solid #1e3a8a;
    border-top: 1px solid #e2e8f0;
    border-right: 1px solid #e2e8f0;
    border-bottom: 1px solid #e2e8f0;
    padding: 10px 12px;
    border-radius: 0 6px 6px 0;
    margin: 10px 0;
    break-inside: avoid;
  }}
  .callout-warn {{
    background: #fffbeb;
    border-left-color: #d97706;
    border-color: #fde68a;
    border-left-width: 4px;
  }}
  .callout-success {{
    background: #ecfdf5;
    border-left-color: #059669;
    border-color: #a7f3d0;
    border-left-width: 4px;
  }}
  .callout-title {{
    font-weight: 800;
    color: #1e3a8a;
    margin-bottom: 4px;
    font-size: 10pt;
  }}
  .callout-warn .callout-title {{
    color: #b45309;
  }}
  .callout-success .callout-title {{
    color: #047857;
  }}

  /* ================= TABLES ================= */
  .table-wrap {{
    margin: 8px 0 12px 0;
    break-inside: avoid;
  }}
  .data-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 9pt;
  }}
  .compact-table {{
    font-size: 8.3pt;
  }}
  .data-table th {{
    background: #1e3a8a;
    color: #ffffff;
    font-weight: 700;
    padding: 5.5px 7px;
    border: 1px solid #1e3a8a;
    text-align: left;
  }}
  .data-table td {{
    padding: 4.5px 7px;
    border: 1px solid #cbd5e1;
    color: #1e293b;
    vertical-align: top;
  }}
  .data-table tr:nth-child(even) td {{
    background: #f8fafc;
  }}
  .num-cell {{
    text-align: right;
    font-variant-numeric: tabular-nums;
    font-weight: 600;
  }}
  .center-cell {{
    text-align: center;
  }}
  .null-cell {{
    text-align: center;
    color: #94a3b8;
    font-style: italic;
    font-weight: 600;
  }}
  .status-badge {{
    display: inline-block;
    padding: 1px 7px;
    border-radius: 10px;
    font-size: 7.8pt;
    font-weight: 700;
  }}
  .badge-completed {{
    background: #dcfce7;
    color: #166534;
    border: 1px solid #86efac;
  }}
  .badge-pending {{
    background: #fef3c7;
    color: #92400e;
    border: 1px solid #fde68a;
  }}
  .badge-cancelled {{
    background: #fee2e2;
    color: #991b1b;
    border: 1px solid #fca5a5;
  }}
  .table-caption {{
    font-size: 8.6pt;
    color: #475569;
    font-style: italic;
    text-align: center;
    margin-top: 4px;
  }}
  .empty-result {{
    background: #ecfdf5;
    border: 1px dashed #10b981;
    color: #065f46;
    padding: 7px 12px;
    border-radius: 5px;
    font-size: 9.2pt;
    text-align: center;
  }}

  /* ================= CODE BLOCKS & QUERY CARDS ================= */
  .sql-code {{
    background: #0f172a;
    color: #f8fafc;
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 8.3pt;
    line-height: 1.42;
    padding: 9px 12px;
    border-radius: 6px;
    overflow-x: auto;
    margin: 6px 0 8px 0;
    border-left: 4px solid #38bdf8;
    white-space: pre-wrap;
    word-break: break-word;
    break-inside: avoid;
  }}
  .sql-code code {{
    background: transparent;
    color: inherit;
    border: none;
    padding: 0;
    font-size: inherit;
  }}
  .query-card {{
    border: 1px solid #cbd5e1;
    border-radius: 7px;
    margin-bottom: 14px;
    background: #ffffff;
    break-inside: avoid;
    overflow: hidden;
  }}
  .query-header {{
    background: #f1f5f9;
    border-bottom: 1px solid #cbd5e1;
    padding: 7px 12px;
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .query-header h3 {{
    margin: 0;
    font-size: 10.2pt;
    color: #0f172a;
  }}
  .query-badge {{
    background: #1e3a8a;
    color: #ffffff;
    font-size: 8.2pt;
    font-weight: 800;
    padding: 2px 9px;
    border-radius: 12px;
    text-transform: uppercase;
    white-space: nowrap;
  }}
  .query-body {{
    padding: 9px 12px;
  }}
  .query-req, .query-analysis {{
    font-size: 9.5pt;
    margin-bottom: 6px;
  }}

  /* ================= ERD SVG ================= */
  .erd-container {{
    margin: 10px 0 14px 0;
    break-inside: avoid;
  }}
  .erd-svg {{
    width: 100%;
    height: auto;
    display: block;
  }}
</style>
</head>
<body>

<!-- ===================================================================== -->
<!-- TRANG BÌA (COVER PAGE)                                                -->
<!-- ===================================================================== -->
<div class="cover-page">
  <div class="cover-inner-border">
    <div class="cover-top">
      <div class="quoc-hieu">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</div>
      <div class="tieu-ngu">Độc lập - Tự do - Hạnh phúc</div>
      <div class="divider-short"></div>

      <p class="uni-name">ĐẠI HỌC KINH TẾ QUỐC DÂN</p>
      <p class="uni-name-en">NATIONAL ECONOMICS UNIVERSITY (NEU)</p>
      <p class="faculty-name">KHOA KHOA HỌC DỮ LIỆU VÀ TRÍ TUỆ NHÂN TẠO</p>
      <p class="faculty-name-en">FACULTY OF DATA SCIENCE AND ARTIFICIAL INTELLIGENCE (FDA)</p>

      <div class="logo-row">
        <div class="logo-box">
          <img src="{neu_logo_uri}" alt="Logo NEU">
          <span class="logo-caption">LOGO TRƯỜNG (NEU)</span>
        </div>
        <div class="logo-box">
          <img src="{fda_logo_uri}" alt="Logo FDA">
          <span class="logo-caption">LOGO KHOA (FDA)</span>
        </div>
      </div>
    </div>

    <div class="cover-title-block">
      <div class="report-type">BÁO CÁO BÀI TẬP THỰC HÀNH CƠ SỞ DỮ LIỆU MYSQL</div>
      <h1 class="report-main-title">ĐỀ 01: QUẢN LÝ TRUNG TÂM GIA SƯ</h1>
      <div class="report-db-badge">Database Schema: tutoring_mini</div>
    </div>

    <div class="cover-meta">
      <div class="meta-member-title">DANH SÁCH THÀNH VIÊN NHÓM THỰC HIỆN</div>
      <table class="member-table">
        <thead>
          <tr>
            <th style="width: 8%; text-align: center;">STT</th>
            <th style="width: 32%;">Họ và Tên Sinh viên</th>
            <th style="width: 18%; text-align: center;">Mã Sinh viên</th>
            <th style="width: 42%;">Phân công Nhiệm vụ</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td class="center-cell"><strong>1</strong></td>
            <td><strong>Phạm Ngọc Danh</strong></td>
            <td class="center-cell"><strong>11251809</strong></td>
            <td>Thiết kế lược đồ <code>schema.sql</code>, xây dựng VIEW <code>views.sql</code> &amp; Tổng hợp Báo cáo</td>
          </tr>
          <tr>
            <td class="center-cell"><strong>2</strong></td>
            <td><strong>Nguyễn Mạnh Dũng</strong></td>
            <td class="center-cell"><strong>11252140</strong></td>
            <td>Xây dựng dữ liệu mẫu <code>seed.sql</code>, kiểm chứng ràng buộc &amp; Nhóm truy vấn 1 – 5</td>
          </tr>
          <tr>
            <td class="center-cell"><strong>3</strong></td>
            <td><strong>Hoàng Đức Dương</strong></td>
            <td class="center-cell"><strong>11252228</strong></td>
            <td>Phát triển &amp; kiểm thử Nhóm truy vấn 6 – 10 trong <code>queries.sql</code> &amp; Đóng gói GitHub</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="cover-footer">
      HÀ NỘI — 2026
    </div>
  </div>
</div>

<!-- ===================================================================== -->
<!-- MỤC 1: TỔNG QUAN & PHÂN TÍCH BÀI TOÁN                                 -->
<!-- ===================================================================== -->
<div class="section-banner">
  <h1>Mục 1. Tổng Quan &amp; Phân Tích Bài Toán Nghiệp Vụ</h1>
</div>

<h2>1.1. Mục tiêu và Bối cảnh Nghiệp vụ</h2>
<p>
  Hệ thống Cơ sở dữ liệu <strong>Quản lý Trung tâm Gia sư (<code>tutoring_mini</code>)</strong> được thiết kế nhằm chuẩn hóa và tự động hóa toàn bộ quy trình vận hành cốt lõi của một trung tâm đào tạo gia sư hiện đại: từ quản lý danh mục môn học (<code>subjects</code>), hồ sơ năng lực đội ngũ gia sư (<code>tutors</code>), hồ sơ học viên (<code>students</code>), điều phối lịch học và trạng thái buổi học (<code>lessons</code>), cho đến lưu trữ biên bản đánh giá chuyên môn kiêm xác nhận học phí sau buổi học (<code>lesson_reports</code>) và theo dõi dòng tiền thu học phí nhiều đợt (<code>payments</code>).
</p>

<h2>1.2. Các Quy tắc Nghiệp vụ &amp; Ràng buộc Toàn vẹn Cốt lõi</h2>
<div class="callout">
  <div class="callout-title">5 Quy tắc Toàn vẹn Nghiệp vụ Bắt buộc trong Hệ thống tutoring_mini</div>
  <ol style="margin-bottom:0;">
    <li><strong>Phân công Chuyên môn Gia sư (1 – N):</strong> Mỗi môn học có tên duy nhất (<code>UNIQUE</code>). Mỗi gia sư phụ trách giảng dạy một môn học xác định và có địa chỉ <code>email</code> định danh duy nhất.</li>
    <li><strong>Vòng đời Trạng thái Buổi học (<code>ENUM</code>):</strong> Mỗi buổi học giữa một học viên và một gia sư chỉ mang một trong ba trạng thái chuẩn: <code>'Pending'</code> (Đã lên lịch/Chờ học), <code>'Completed'</code> (Đã hoàn thành), hoặc <code>'Cancelled'</code> (Đã hủy).</li>
    <li><strong>Nghiệp vụ Báo cáo Buổi học (Quan hệ 1 – 1 chặt chẽ):</strong> Chỉ những buổi học có trạng thái <code>'Completed'</code> mới được lập <code>lesson_reports</code>, và <strong>mọi</strong> buổi học <code>'Completed'</code> đều bắt buộc có đúng 1 bản ghi <code>lesson_reports</code> (ràng buộc bởi khóa ngoại <code>lesson_id UNIQUE</code>, thời lượng <code>duration_minutes &gt; 0</code> và học phí <code>fee &gt;= 0</code>).</li>
    <li><strong>Nghiệp vụ Thu tiền &amp; Trả góp (Quan hệ 1 – N):</strong> Học viên chỉ thanh toán cho các buổi học đã có báo cáo kết quả (<code>lesson_reports</code>). Một buổi học có thể được thanh toán một lần, trả góp nhiều lần (nhiều dòng trong <code>payments</code> cùng <code>lesson_id</code>) hoặc còn nợ, nhưng tổng số tiền đã thu (<code>SUM(amount)</code>) của một <code>lesson_id</code> không bao giờ vượt quá học phí đã xác nhận (<code>fee</code>).</li>
    <li><strong>Chống cộng lặp chi phí (Anti-Fanout / Chasm Trap Prevention):</strong> Do <code>lesson_reports</code> có quan hệ 1–1 với <code>lessons</code> trong khi <code>payments</code> có quan hệ 1–N với <code>lessons</code>, khi tổng hợp đồng thời học phí (<code>fee</code>) và tiền đã trả (<code>amount</code>), hệ thống bắt buộc phải gom nhóm <code>payments</code> theo <code>lesson_id</code> trong Subquery/CTE trước khi nối với <code>lesson_reports</code> để tránh nhân bản học phí.</li>
  </ol>
</div>

<!-- ===================================================================== -->
<!-- MỤC 2: THIẾT KẾ CƠ SỞ DỮ LIỆU (PHẦN A)                                -->
<!-- ===================================================================== -->
<div class="section-banner">
  <h1>Mục 2. Thiết Kế Cơ Sở Dữ Liệu (Phần A — schema.sql)</h1>
</div>

<h2>2.1. Sơ đồ Quan hệ Thực thể (Entity-Relationship Diagram — ERD)</h2>
<p>
  Cơ sở dữ liệu <code>tutoring_mini</code> được thiết kế đạt chuẩn dạng chuẩn 3 (<strong>3NF</strong>), loại bỏ hoàn toàn dư thừa dữ liệu và dị thường cập nhật. Sơ đồ quan hệ giữa 6 bảng được biểu diễn trực quan tại Hình 2.1:
</p>
{erd_svg}

<h2>2.2. Đặc tả Chi tiết Cấu trúc 6 Bảng và Giải thích Ràng buộc</h2>
<div class="table-wrap">
  <table class="data-table compact-table">
    <thead>
      <tr>
        <th style="width:14%;">Tên Bảng</th>
        <th style="width:24%;">Các Trường (Khóa chính đứng đầu)</th>
        <th style="width:18%;">Khóa Chính / Khóa Ngoại</th>
        <th style="width:44%;">Ràng buộc Toàn vẹn (UNIQUE, CHECK, ENUM) &amp; Giải thích Thiết kế</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><code>subjects</code></td>
        <td><code>subject_id</code>, <code>name</code></td>
        <td><strong>PK:</strong> <code>subject_id</code></td>
        <td><code>name VARCHAR(100) NOT NULL UNIQUE</code> — Đảm bảo không trùng lặp tên môn học trong danh mục đào tạo.</td>
      </tr>
      <tr>
        <td><code>tutors</code></td>
        <td><code>tutor_id</code>, <code>full_name</code>, <code>email</code>, <code>qualification</code>, <code>subject_id</code></td>
        <td><strong>PK:</strong> <code>tutor_id</code><br><strong>FK:</strong> <code>subject_id</code> → <code>subjects(subject_id)</code></td>
        <td>Mọi cột đều <code>NOT NULL</code>; <code>email UNIQUE</code> chống đăng ký trùng tài khoản gia sư; <code>FK</code> đảm bảo gia sư luôn thuộc môn học hợp lệ.</td>
      </tr>
      <tr>
        <td><code>students</code></td>
        <td><code>student_id</code>, <code>full_name</code>, <code>dob</code>, <code>phone</code></td>
        <td><strong>PK:</strong> <code>student_id</code></td>
        <td><code>full_name</code>, <code>dob (DATE)</code>, <code>phone</code> đều <code>NOT NULL</code> — Lưu trữ đầy đủ thông tin định danh và liên lạc của học viên.</td>
      </tr>
      <tr>
        <td><code>lessons</code></td>
        <td><code>lesson_id</code>, <code>student_id</code>, <code>tutor_id</code>, <code>lesson_date</code>, <code>status</code></td>
        <td><strong>PK:</strong> <code>lesson_id</code><br><strong>FK1:</strong> <code>student_id</code> → <code>students</code><br><strong>FK2:</strong> <code>tutor_id</code> → <code>tutors</code></td>
        <td><code>lesson_date DATE NOT NULL</code>; <code>status ENUM('Pending', 'Completed', 'Cancelled') NOT NULL</code> — Giới hạn chặt miền trạng thái buổi học ngay tại tầng lưu trữ.</td>
      </tr>
      <tr>
        <td><code>lesson_reports</code></td>
        <td><code>report_id</code>, <code>lesson_id</code>, <code>content</code>, <code>feedback</code>, <code>duration_minutes</code>, <code>fee</code></td>
        <td><strong>PK:</strong> <code>report_id</code><br><strong>FK + UQ:</strong> <code>lesson_id</code> → <code>lessons(lesson_id)</code></td>
        <td><code>lesson_id UNIQUE</code> ép buộc quan hệ <strong>1–1</strong> (mỗi buổi học có tối đa 1 báo cáo); <code>CHECK (duration_minutes &gt; 0)</code> và <code>CHECK (fee &gt;= 0)</code> bảo vệ miền giá trị hợp lệ.</td>
      </tr>
      <tr>
        <td><code>payments</code></td>
        <td><code>payment_id</code>, <code>lesson_id</code>, <code>amount</code>, <code>payment_date</code>, <code>method</code></td>
        <td><strong>PK:</strong> <code>payment_id</code><br><strong>FK:</strong> <code>lesson_id</code> → <code>lessons(lesson_id)</code></td>
        <td>Không đặt <code>UNIQUE</code> trên <code>lesson_id</code> để cho phép trả góp nhiều lần (1–N); <code>CHECK (amount &gt; 0)</code>; <code>method ENUM('Cash', 'BankTransfer', 'Card') NOT NULL</code>.</td>
      </tr>
    </tbody>
  </table>
  <div class="table-caption">Bảng 2.1: Tổng hợp thiết kế cấu trúc 6 bảng và các ràng buộc toàn vẹn trong <code>schema.sql</code>.</div>
</div>

<p>
  <strong>Lưu ý kỹ thuật MySQL:</strong> Trong MySQL 8.0/9.0, ràng buộc <code>CHECK</code> không cho phép chứa câu truy vấn con (Subquery) tham chiếu sang bảng khác. Do đó, các ràng buộc nội bảng (<code>duration_minutes &gt; 0</code>, <code>fee &gt;= 0</code>, <code>amount &gt; 0</code>) được khai báo trực tiếp bằng <code>CHECK</code> trong <code>schema.sql</code>, còn các quy tắc liên bảng (chỉ buổi <code>Completed</code> mới có báo cáo, tổng <code>amount &lt;= fee</code>) được kiểm chứng chặt chẽ bằng bộ truy vấn đối soát ở cuối tệp <code>seed.sql</code>.
</p>

<h2>2.3. Mã nguồn Tệp <code>schema.sql</code> Hoàn chỉnh</h2>
<pre class="sql-code"><code>{html.escape(schema_code)}</code></pre>

<!-- ===================================================================== -->
<!-- MỤC 3: NẠP DỮ LIỆU MẪU & KIỂM CHỨNG (PHẦN B)                          -->
<!-- ===================================================================== -->
<div class="section-banner section-page-break">
  <h1>Mục 3. Nạp Dữ Liệu Mẫu &amp; Kiểm Chứng (Phần B — seed.sql)</h1>
</div>

<h2>3.1. Ma trận Thiết kế Kịch bản Dữ liệu Mẫu Bao phủ Toàn bộ Edge-Cases</h2>
<p>
  Bộ dữ liệu mẫu trong <code>seed.sql</code> được thiết kế vượt mức tối thiểu của đề bài và bao phủ chính xác tất cả 10 nhóm kịch bản biên (edge-cases) để kiểm thử toàn diện 10 câu truy vấn và 3 VIEW:
</p>

<div class="table-wrap">
  <table class="data-table compact-table">
    <thead>
      <tr>
        <th style="width:5%;">STT</th>
        <th style="width:35%;">Yêu cầu Kịch bản Dữ liệu của Đề bài</th>
        <th style="width:20%;">Số lượng Thực tế</th>
        <th style="width:40%;">Bản ghi Cụ thể Minh chứng trong <code>seed.sql</code></th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td class="center-cell">1</td>
        <td>Số lượng bản ghi tối thiểu mỗi bảng</td>
        <td>6 / 6 / 11 / 23 / 16 / 17</td>
        <td><code>subjects</code>=6 (≥5), <code>tutors</code>=6 (≥6), <code>students</code>=11 (≥10), <code>lessons</code>=23 (≥12), <code>lesson_reports</code>=16 (≥10), <code>payments</code>=17 (≥10).</td>
      </tr>
      <tr>
        <td class="center-cell">2</td>
        <td>Đa dạng thời gian: Tháng 01/2025, Quý I/2025 (T2, T3), ngoài Quý I/2025, ngoài năm 2025</td>
        <td>Đủ 4 phân vùng thời gian</td>
        <td>• Tháng 01/2025: <code>lesson_id</code> 1, 2, 6, 10, 22<br>• Tháng 02 &amp; 03/2025: <code>lesson_id</code> 3, 4, 7, 8, 11, 12, 15, 17, 19, 20, 21, 23<br>• Ngoài Quý I/2025 (T5, T6/2025): <code>lesson_id</code> 5, 9, 13, 18<br>• Năm 2024: <code>lesson_id</code> 14 (<code>2024-11-15</code>), 16 (<code>2024-12-10</code>).</td>
      </tr>
      <tr>
        <td class="center-cell">3</td>
        <td>Đủ 3 trạng thái buổi học &amp; Tỷ lệ 1-1 tuyệt đối giữa <code>Completed</code> và <code>lesson_reports</code></td>
        <td>16 Completed, 4 Pending, 3 Cancelled</td>
        <td>Đúng 16/16 buổi <code>Completed</code> (<code>lesson_id</code> 1..16) có báo cáo trong <code>lesson_reports</code>; 0 buổi <code>Pending</code>/<code>Cancelled</code> có báo cáo.</td>
      </tr>
      <tr>
        <td class="center-cell">4</td>
        <td>Ít nhất 1 học viên có <strong>hơn 3 buổi học Completed</strong> trong năm 2025 (≥ 4 buổi)</td>
        <td>2 học viên đạt điều kiện</td>
        <td>• <code>student_id = 1</code> (Lê Hoàng Minh Khôi): <strong>5 buổi</strong> Completed năm 2025 (buổi 1, 2, 3, 4, 5)<br>• <code>student_id = 2</code> (Nguyễn Phương Anh): <strong>4 buổi</strong> Completed năm 2025 (buổi 6, 7, 8, 9).</td>
      </tr>
      <tr>
        <td class="center-cell">5</td>
        <td>Ít nhất 1 học viên có lịch sử giao dịch nhưng chưa thanh toán lần nào</td>
        <td>2 học viên</td>
        <td>• <code>student_id = 7</code> (Vũ Ngọc Hà): Có buổi 15 (<code>Completed</code>, phí 450,000) và buổi 18 (<code>Pending</code>) nhưng 0 bản ghi <code>payments</code>.<br>• <code>student_id = 8</code> (Bùi Đức Thịnh): Có buổi 19, 20 (<code>Pending</code>) và 22 (<code>Cancelled</code>), 0 thanh toán.</td>
      </tr>
      <tr>
        <td class="center-cell">6</td>
        <td>Ít nhất 1 học viên chưa từng có buổi học nào</td>
        <td>2 học viên</td>
        <td><code>student_id = 10</code> (Ngô Hải Đăng) và <code>student_id = 11</code> (Lý Thanh Trúc) — chưa từng có dòng nào trong <code>lessons</code>.</td>
      </tr>
      <tr>
        <td class="center-cell">7</td>
        <td>Ít nhất 1 giao dịch trả nhiều lần (nhiều bản ghi <code>payments</code> cùng <code>lesson_id</code>)</td>
        <td>2 buổi học trả 2 đợt</td>
        <td>• <code>lesson_id = 1</code>: <code>payment_id</code> 1 (300,000) + <code>payment_id</code> 2 (200,000) = 500,000 (trả đủ sau 2 lần).<br>• <code>lesson_id = 6</code>: <code>payment_id</code> 7 (200,000) + <code>payment_id</code> 8 (150,000) = 350,000 / 500,000 (trả 2 lần, còn nợ 150,000).</td>
      </tr>
      <tr>
        <td class="center-cell">8</td>
        <td>Ít nhất 1 giao dịch còn nợ (tổng <code>amount &lt; fee</code>)</td>
        <td>4 buổi học còn nợ</td>
        <td><code>lesson_id = 6</code> (nợ 150,000), <code>lesson_id = 10</code> (nợ 200,000), <code>lesson_id = 13</code> (nợ 200,000), <code>lesson_id = 15</code> (nợ 450,000 — chưa trả lần nào).</td>
      </tr>
      <tr>
        <td class="center-cell">9</td>
        <td>Ít nhất 1 môn học chưa có giao dịch trong Quý I/2025</td>
        <td>2 môn học</td>
        <td>• <code>subject_id = 5</code> (Kinh tế vĩ mô 1): chỉ có 2 buổi học trong năm 2024.<br>• <code>subject_id = 6</code> (Pháp luật đại cương): chưa có buổi học nào toàn thời gian.</td>
      </tr>
      <tr>
        <td class="center-cell">10</td>
        <td>Ít nhất 1 gia sư chưa có giao dịch trong năm 2025</td>
        <td>1 gia sư</td>
        <td>• <code>tutor_id = 6</code> (ThS. Phạm Đức Chung): chỉ dạy 2 buổi trong năm 2024, chưa có giao dịch năm 2025.</td>
      </tr>
    </tbody>
  </table>
  <div class="table-caption">Bảng 3.0: Ma trận đối chiếu kịch bản dữ liệu mẫu trong <code>seed.sql</code> với toàn bộ yêu cầu đề bài.</div>
</div>

<h2>3.2. Dữ liệu Thực tế Đã Nạp trong 6 Bảng</h2>
{tbl_subjects}
{tbl_tutors}
{tbl_students}
{tbl_lessons}
{tbl_reports}
{tbl_payments}

<h2>3.3. Kết quả Chạy Các Truy vấn Kiểm chứng Toàn vẹn trong <code>seed.sql</code></h2>
<p>
  Cuối tệp <code>seed.sql</code> tích hợp 4 câu lệnh <code>SELECT</code> đối soát tự động nhằm chứng minh dữ liệu mẫu tuân thủ tuyệt đối quy tắc nghiệp vụ báo cáo (1–1 với <code>Completed</code>) và quy tắc thu tiền (<code>SUM(amount) &lt;= fee</code>):
</p>
{ver_1a}
{ver_1b}
{ver_2a}
{ver_2b}

<h2>3.4. Phân tích Các Câu lệnh <code>INSERT</code> Minh họa Vi phạm Ràng buộc (Đặt trong Chú thích)</h2>
<div class="callout callout-warn">
  <div class="callout-title">4 Kịch bản Kiểm thử Âm tính (Negative Test Cases) được Đặt trong Chú thích Cuối Tệp seed.sql</div>
  <ul style="margin-bottom:0;">
    <li><strong>Vi phạm Khóa ngoại (<code>FOREIGN KEY</code>):</strong> <code>INSERT INTO lessons ... VALUES (999, 1, '2025-04-01', 'Pending');</code> — Bị chặn bởi <code>fk_lessons_student</code> (Lỗi MySQL <code>ERROR 1452: Cannot add or update a child row</code>) do <code>student_id = 999</code> không tồn tại.</li>
    <li><strong>Vi phạm Ràng buộc <code>duration_minutes &lt;= 0</code>:</strong> <code>INSERT INTO lesson_reports ... VALUES (17, 'Ôn tập Phân tích dữ liệu với Python', 'Tốt', 0, 450000.00);</code> — Bị chặn bởi <code>chk_report_duration</code> (Lỗi MySQL <code>ERROR 3819: Check constraint is violated</code>).</li>
    <li><strong>Vi phạm Ràng buộc <code>amount &lt;= 0</code>:</strong> <code>INSERT INTO payments ... VALUES (1, -50000.00, '2025-01-15', 'Cash');</code> — Bị chặn bởi <code>chk_payment_amount</code> (Lỗi MySQL <code>ERROR 3819</code>).</li>
    <li><strong>Vi phạm Ràng buộc Trùng <code>lesson_id</code> (<code>UNIQUE</code>):</strong> <code>INSERT INTO lesson_reports (lesson_id, ...) VALUES (1, ...);</code> — Bị chặn bởi khóa <code>UNIQUE (lesson_id)</code> (Lỗi MySQL <code>ERROR 1062: Duplicate entry '1'</code>).</li>
  </ul>
</div>

<!-- ===================================================================== -->
<!-- MỤC 4: GIẢI QUYẾT 10 TRUY VẤN DỮ LIỆU (PHẦN C)                         -->
<!-- ===================================================================== -->
<div class="section-banner section-page-break">
  <h1>Mục 4. Giải Quyết 10 Truy Vấn Dữ Liệu (Phần C — queries.sql)</h1>
</div>

<div class="callout callout-success">
  <div class="callout-title">Nguyên lý Kỹ thuật Trọng tâm: Chống Cộng Lặp Chi Phí (Anti-Fanout / Chasm Trap Prevention)</div>
  <p style="margin-bottom:0;">
    Trong lược đồ <code>tutoring_mini</code>, một buổi học (<code>lessons</code>) có tối đa <strong>1</strong> báo cáo học phí (<code>lesson_reports.fee</code>), nhưng có thể có <strong>N</strong> lần thanh toán (<code>payments.amount</code>). Nếu thực hiện nối trực tiếp <code>lessons JOIN lesson_reports JOIN payments</code> rồi tính <code>SUM(lr.fee)</code> hoặc <code>AVG(lr.fee)</code>, những buổi học trả góp nhiều lần (như <code>lesson_id = 1</code> và <code>lesson_id = 6</code> có 2 lần thanh toán) sẽ làm giá trị <code>lr.fee</code> bị nhân đôi! Để triệt tiêu hoàn toàn lỗi cộng lặp này: (1) Ở các câu chỉ tính học phí (Câu 4, Câu 8, <code>v_group_summary</code>), ta chỉ nối tới <code>lesson_reports</code> mà không nối <code>payments</code>; (2) Ở báo cáo đối chiếu đồng thời cả học phí và thanh toán (như <code>v_debt</code>), ta bắt buộc <strong>gom nhóm bảng <code>payments</code> theo <code>lesson_id</code> trong Subquery trước</strong> để đưa quan hệ về 1–1 rồi mới thực hiện <code>LEFT JOIN</code>.
  </p>
</div>

{''.join(queries_html_blocks)}

<!-- ===================================================================== -->
<!-- MỤC 5: XÂY DỰNG CÁC VIEW TOÀN THỜI GIAN (PHẦN D)                      -->
<!-- ===================================================================== -->
<div class="section-banner section-page-break">
  <h1>Mục 5. Xây Dựng Các VIEW Toàn Thời Gian (Phần D — views.sql)</h1>
</div>

<p>
  Ba khung nhìn (<code>VIEW</code>) trong tệp <code>views.sql</code> được thiết kế bao quát toàn bộ thời gian (bao gồm cả dữ liệu năm 2024 và năm 2025), cung cấp giao diện truy vấn chuẩn hóa cho hệ thống báo cáo điều hành và kế toán công nợ của trung tâm:
</p>

<h2>5.1. Thiết kế và Kết quả Thực tế của <code>v_detail</code></h2>
<p>
  <strong>Logic thiết kế:</strong> Khung nhìn <code>v_detail</code> nối trong (<code>INNER JOIN</code>) từ <code>lessons</code> sang <code>students</code>, <code>tutors</code> và <code>subjects</code> để lấy đầy đủ mã định danh kèm tên học viên, gia sư, môn học; sau đó sử dụng <code>LEFT JOIN lesson_reports</code> để giữ nguyên cả các buổi học <code>Pending</code> và <code>Cancelled</code> chưa có kết quả (cột <code>fee</code> hiển thị <code>NULL</code> đúng yêu cầu).
</p>
<pre class="sql-code"><code>CREATE OR REPLACE VIEW v_detail AS
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
LEFT JOIN lesson_reports lr ON l.lesson_id = lr.lesson_id;</code></pre>
{tbl_v_detail}

<h2>5.2. Thiết kế và Kết quả Thực tế của <code>v_group_summary</code></h2>
<p>
  <strong>Logic thiết kế:</strong> Khung nhìn <code>v_group_summary</code> xuất phát từ bảng <code>subjects</code> và thực hiện chuỗi <code>LEFT JOIN</code> sang <code>tutors → lessons → lesson_reports</code>. Nhờ đó, môn học chưa từng phát sinh giao dịch (<em>Pháp luật đại cương</em>, <code>subject_id = 6</code>) vẫn được giữ lại với các chỉ số đếm và <code>total_fee = 0.00</code>. Việc không nối bảng <code>payments</code> giúp <code>SUM(lr.fee)</code> chính xác tuyệt đối, không bị cộng lặp.
</p>
<pre class="sql-code"><code>CREATE OR REPLACE VIEW v_group_summary AS
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
GROUP BY sub.subject_id, sub.name;</code></pre>
{tbl_v_group}

<h2>5.3. Thiết kế và Kết quả Thực tế của <code>v_debt</code> (Chống Cộng Lặp Chi Phí)</h2>
<p>
  <strong>Logic thiết kế:</strong> Khung nhìn <code>v_debt</code> tổng hợp công nợ cho toàn bộ 11 học viên. Để <strong>bảo đảm chi phí không bị cộng lặp</strong> khi một buổi học có nhiều lần thanh toán (như <code>lesson_id = 1</code> của Lê Hoàng Minh Khôi và <code>lesson_id = 6</code> của Nguyễn Phương Anh), ta sử dụng bảng dẫn xuất (Derived Table) <code>pay_per_lesson</code> gom nhóm <code>SUM(amount)</code> theo <code>lesson_id</code> trước khi <code>LEFT JOIN</code> với <code>lessons</code> và <code>lesson_reports</code>:
</p>
<pre class="sql-code"><code>CREATE OR REPLACE VIEW v_debt AS
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
GROUP BY s.student_id, s.full_name;</code></pre>
{tbl_v_debt}

</body>
</html>
"""
    HTML_OUTPUT.write_text(html_doc, encoding="utf-8")
    print(f"Đã tạo file HTML: {HTML_OUTPUT}")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"file://{HTML_OUTPUT}", wait_until="networkidle")
        page.pdf(
            path=str(PDF_OUTPUT),
            format="A4",
            print_background=True,
            display_header_footer=True,
            header_template="""
            <div style="width:100%; font-size:7.5pt; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color:#64748b; padding:0 16mm; display:flex; justify-content:space-between; border-bottom:0.5px solid #cbd5e1;">
              <span><strong>FDA - NEU</strong> | Khoa Khoa học Dữ liệu và Trí tuệ Nhân tạo</span>
              <span>Đề 01: Quản lý Trung tâm Gia sư (tutoring_mini)</span>
            </div>
            """,
            footer_template="""
            <div style="width:100%; font-size:7.5pt; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color:#64748b; padding:0 16mm; display:flex; justify-content:space-between; border-top:0.5px solid #cbd5e1;">
              <span>Báo cáo Thực hành Cơ sở Dữ liệu MySQL — Đề 01 (tutoring_mini)</span>
              <span>Trang <span class="pageNumber"></span> / <span class="totalPages"></span></span>
            </div>
            """,
        )
        browser.close()

    if HTML_OUTPUT.exists():
        HTML_OUTPUT.unlink()
    print(f"Đã kết xuất thành công PDF: {PDF_OUTPUT} ({PDF_OUTPUT.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    generate_html_report()
