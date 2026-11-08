#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated MySQL verification and PDF report generator for:
Topic 01: Tutoring Center Management System (tutoring_mini)
Output: Bao_cao_De_01.pdf
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
    """Start a temporary local MySQL instance for verification and live result extraction."""
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
    raise RuntimeError("Failed to start local MySQL Server instance.")


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
        raise RuntimeError(f"Error executing {filename}:\n{res.stderr}")


def run_query(sql: str):
    """Execute a SELECT query on MySQL and return (headers, rows)."""
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
        raise RuntimeError(f"SQL Query Error:\n{res.stderr}\nSQL:\n{sql}")
    lines = [line for line in res.stdout.splitlines() if line.strip() != ""]
    if not lines:
        return [], []
    headers = lines[0].split("\t")
    rows = [line.split("\t") for line in lines[1:]]
    return headers, rows


def render_table(headers, rows, caption=None, compact=False):
    if not headers:
        empty_html = (
            '<div class="empty-result">✓ Query Result: <strong>0 rows (Empty set)</strong> '
            "— No constraint violations detected!</div>"
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
            elif cell in ("Completed", "Pending", "Cancelled", "VALID"):
                badge_cls = {
                    "Completed": "badge-completed",
                    "Pending": "badge-pending",
                    "Cancelled": "badge-cancelled",
                    "VALID": "badge-completed",
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
    """Build a clean, well-proportioned SVG Entity-Relationship Diagram (ERD) in English."""
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
          <text x="465" y="244" text-anchor="middle" fill="#ffffff" font-weight="bold" font-size="12.5">4. lessons (Core Table)</text>
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
          <text x="817" y="44" text-anchor="middle" fill="#ffffff" font-weight="bold" font-size="12.5">5. lesson_reports (1-1 Relation)</text>
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
          <text x="817" y="244" text-anchor="middle" fill="#ffffff" font-weight="bold" font-size="12.5">6. payments (1-N Relation)</text>
          <text x="706" y="272" font-size="11" fill="#0f172a"><tspan font-weight="bold" fill="#b91c1c">PK</tspan>  payment_id : INT</text>
          <text x="706" y="293" font-size="11" fill="#0f172a"><tspan font-weight="bold" fill="#7c3aed">FK</tspan>  lesson_id : INT NOT NULL</text>
          <text x="706" y="314" font-size="11" fill="#0f172a"><tspan font-weight="bold" fill="#b45309">CK</tspan>  amount : DECIMAL(12,2) (&gt; 0)</text>
          <text x="706" y="335" font-size="11" fill="#0f172a">     payment_date : DATE NOT NULL</text>
          <text x="706" y="356" font-size="11" fill="#0f172a">     method : ENUM('Cash','BankTransfer','Card')</text>
        </g>

        <!-- Legend at bottom -->
        <rect x="20" y="392" width="920" height="24" rx="4" fill="#e2e8f0"/>
        <text x="480" y="408" text-anchor="middle" font-size="10.8" fill="#1e293b" font-weight="600">
          Legend: [PK] Primary Key   |   [FK] Foreign Key   |   [UQ] Unique Constraint (UNIQUE)   |   [CK] Check Constraint (CHECK)
        </text>
      </svg>
      <div class="table-caption">Figure 2.1: Entity-Relationship Diagram (ERD) of the Tutoring Center Management Database (<code>tutoring_mini</code>).</div>
    </div>
    """


def generate_html_report():
    started_by_us = ensure_mysql_running()
    try:
        # Execute the 4 SQL files sequentially
        run_sql_file("schema.sql")
        run_sql_file("seed.sql")
        run_sql_file("queries.sql")
        run_sql_file("views.sql")

        # Read schema.sql source code
        schema_code = (BASE_DIR / "schema.sql").read_text(encoding="utf-8")

        # Extract seeded data tables
        tbl_subjects = render_table(
            *run_query("SELECT * FROM subjects ORDER BY subject_id;"),
            caption="Table 3.1: Seeded data in the subjects table (6 records).",
            compact=True,
        )
        tbl_tutors = render_table(
            *run_query("SELECT * FROM tutors ORDER BY tutor_id;"),
            caption="Table 3.2: Seeded data in the tutors table (6 records).",
            compact=True,
        )
        tbl_students = render_table(
            *run_query("SELECT * FROM students ORDER BY student_id;"),
            caption="Table 3.3: Seeded data in the students table (11 records).",
            compact=True,
        )
        tbl_lessons = render_table(
            *run_query("SELECT * FROM lessons ORDER BY lesson_id;"),
            caption="Table 3.4: Seeded data in the lessons table (23 records).",
            compact=True,
        )
        tbl_reports = render_table(
            *run_query(
                "SELECT report_id, lesson_id, content, feedback, duration_minutes, fee FROM lesson_reports ORDER BY report_id;"
            ),
            caption="Table 3.5: Seeded data in the lesson_reports table (16 records, strict 1-1 relation with Completed lessons).",
            compact=True,
        )
        tbl_payments = render_table(
            *run_query("SELECT * FROM payments ORDER BY payment_id;"),
            caption="Table 3.6: Seeded data in the payments table (17 records).",
            compact=True,
        )

        # Verification results from seed.sql
        ver_1a = render_table(
            *run_query(
                """
                SELECT l.status, COUNT(l.lesson_id) AS total_lessons, COUNT(lr.report_id) AS total_reports
                FROM lessons l LEFT JOIN lesson_reports lr ON l.lesson_id = lr.lesson_id
                GROUP BY l.status;
                """
            ),
            caption="Table 3.7: Verification 1A Result — Lesson counts by status vs. corresponding lesson report counts.",
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
            caption="Table 3.8: Verification 1B Result — Checking for any lessons violating the 1-1 report rule.",
        )
        ver_2a = render_table(
            *run_query(
                """
                SELECT lr.lesson_id, l.status, lr.fee AS confirmed_fee,
                       COALESCE(SUM(p.amount), 0) AS total_paid,
                       lr.fee - COALESCE(SUM(p.amount), 0) AS remaining_debt,
                       CASE WHEN COALESCE(SUM(p.amount), 0) <= lr.fee THEN 'VALID' ELSE 'VIOLATION' END AS validation_status
                FROM lesson_reports lr
                JOIN lessons l ON lr.lesson_id = l.lesson_id
                LEFT JOIN payments p ON lr.lesson_id = p.lesson_id
                GROUP BY lr.lesson_id, l.status, lr.fee
                ORDER BY lr.lesson_id;
                """
            ),
            caption="Table 3.9: Verification 2A Result — Reconciling confirmed tuition fees and total payments per lesson.",
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
            caption="Table 3.10: Verification 2B Result — Checking for payments exceeding the confirmed fee or lacking a lesson report.",
        )

        # 10 Analytical Queries in queries.sql
        q_specs = [
            {
                "num": 1,
                "title": "List Completed Lessons in January 2025",
                "req": "List all <code>Completed</code> lessons in January 2025, including student ID + name, tutor ID + name, and <code>lesson_date</code>.",
                "analysis": (
                    "Perform an <code>INNER JOIN</code> from <code>lessons</code> to <code>students</code> "
                    "(on <code>student_id</code>) and <code>tutors</code> (on <code>tutor_id</code>). "
                    "Filter by <code>l.status = 'Completed'</code> combined with the half-open date range "
                    "<code>l.lesson_date &gt;= '2025-01-01' AND l.lesson_date &lt; '2025-02-01'</code> (which preserves B-Tree index efficiency and is safe for both <code>DATE</code> and <code>DATETIME</code> types). "
                    "Lesson 22 (on <code>2025-01-29</code> for student Bui Duc Thinh) has status <code>Cancelled</code> and is therefore accurately excluded."
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
                "title": "Count Total Lessons per Subject in Q1/2025",
                "req": "Count the total number of lessons per subject in Q1/2025 (from <code>2025-01-01</code> through <code>2025-03-31</code>) across all statuses; include subjects with a count of <code>0</code>.",
                "analysis": (
                    "Start from the parent table <code>subjects</code> and perform a <code>LEFT JOIN</code> to <code>tutors</code> and then to <code>lessons</code>. "
                    "<strong>Key Technical Point:</strong> The Q1/2025 date filter (<code>l.lesson_date &gt;= '2025-01-01' AND l.lesson_date &lt; '2025-04-01'</code>) "
                    "must be placed directly inside the <code>ON</code> clause of the <code>LEFT JOIN lessons</code> rather than in the <code>WHERE</code> clause. "
                    "Placing it in <code>WHERE</code> would convert the outer join into an inner join and eliminate subjects with zero Q1/2025 lessons (such as <em>Macroeconomics 1</em>, which only had lessons in 2024, and <em>General Law</em>, which has no lessons at all). "
                    "Using <code>COUNT(l.lesson_id)</code> counts only non-NULL lesson IDs, accurately returning <code>0</code> for those two subjects."
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
                "title": "List Students with Unreported Lessons (Excluding Cancelled)",
                "req": "List students who have at least one lesson without a lesson report, excluding <code>Cancelled</code> lessons. Each student must appear only once.",
                "analysis": (
                    "Perform an <code>INNER JOIN</code> from <code>students</code> to <code>lessons</code> and a <code>LEFT JOIN</code> to <code>lesson_reports</code>. "
                    "Lessons lacking a report are identified via the anti-join condition <code>lr.report_id IS NULL</code>, while cancelled lessons are excluded with <code>l.status &lt;&gt; 'Cancelled'</code>. "
                    "Because a student may have multiple unreported <code>Pending</code> lessons (for example, <code>student_id = 8</code> Bui Duc Thinh has 2 <code>Pending</code> lessons: 19 and 20), "
                    "<code>SELECT DISTINCT</code> guarantees that each student appears at most once. Student 5 (Hoang Mai Linh) only has an unreported lesson with status <code>Cancelled</code> and is properly excluded."
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
                "title": "Average Tuition Fee per Completed Lesson by Subject",
                "req": "Calculate the average tuition fee per <code>Completed</code> lesson for each subject across all time; include only subjects that have incurred fees.",
                "analysis": (
                    "Use <code>INNER JOIN</code> across the chain <code>subjects → tutors → lessons → lesson_reports</code> with the filter <code>l.status = 'Completed'</code>. "
                    "Because the specification requires <em>only subjects that have incurred fees</em>, <code>INNER JOIN</code> naturally excludes <em>General Law</em> (which has no completed lessons). "
                    "<strong>Anti-Fanout / Chasm Trap Prevention:</strong> We strictly avoid joining the <code>payments</code> table here; if a lesson was paid in two installments (such as <code>lesson_id = 1</code> and <code>lesson_id = 6</code> in <em>Data Analysis with Python</em>), "
                    "joining <code>payments</code> would duplicate those lessons' fee rows and distort <code>AVG(lr.fee)</code>."
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
                "title": "Top 3 Tutors with the Most Completed Lessons in 2025",
                "req": "List the top 3 tutors with the highest number of <code>Completed</code> lessons in 2025. Break ties by <code>tutor_id</code> ascending; include only tutors with activity.",
                "analysis": (
                    "Use an <code>INNER JOIN</code> between <code>tutors</code> and <code>lessons</code> filtered by <code>l.status = 'Completed'</code> and the 2025 date range (<code>l.lesson_date &gt;= '2025-01-01' AND l.lesson_date &lt; '2026-01-01'</code>) "
                    "so that only tutors with completed lessons in 2025 are considered. "
                    "Group by <code>t.tutor_id, t.full_name</code> and sort using <code>ORDER BY completed_lessons_2025 DESC, t.tutor_id ASC LIMIT 3</code>. "
                    "In the dataset, Tutor 1 (Dr. Tran Hung) and Tutor 2 (Dr. Vu Duc Minh) both have 4 <code>Completed</code> lessons in 2025, and the tie-breaker orders <code>tutor_id = 1</code> first."
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
                "title": "Total Amount Paid by Each Student in 2025",
                "req": "Calculate the total amount paid by each student in 2025 based on <code>payment_date</code>; display <code>0</code> for students who made no payments.",
                "analysis": (
                    "Start from <code>students</code> and perform a <code>LEFT JOIN</code> to <code>lessons</code> and <code>LEFT JOIN</code> to <code>payments</code>. "
                    "The 2025 payment date filter (<code>p.payment_date &gt;= '2025-01-01' AND p.payment_date &lt; '2026-01-01'</code>) is placed inside the <code>ON</code> clause of <code>LEFT JOIN payments</code>. "
                    "Consequently, students who only paid in 2024 (Student 6 Dang Tuan Kiet, Student 9 Do Khanh Huyen), students with 100% unpaid balance (Student 7 Vu Ngoc Ha), and students who never took a lesson (Student 10 Ngo Hai Dang, Student 11 Ly Thanh Truc) are all preserved and displayed with <code>0.00</code> via <code>COALESCE(SUM(p.amount), 0.00)</code>."
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
                "title": "List Students with Zero Payment Records Across All Time",
                "req": "List all students who do not have any payment records across the entire dataset, including students who have never had a lesson.",
                "analysis": (
                    "Perform a <code>LEFT JOIN</code> from <code>students</code> to <code>lessons</code> and <code>payments</code> across all time. "
                    "Group by student and filter using <code>HAVING COUNT(p.payment_id) = 0</code>. "
                    "The result captures both edge-case groups: (1) Students who have lesson history but have never made a payment (Vu Ngoc Ha <code>student_id = 7</code>, Bui Duc Thinh <code>student_id = 8</code>) "
                    "and (2) Newly registered students who have never booked a lesson (Ngo Hai Dang <code>student_id = 10</code>, Ly Thanh Truc <code>student_id = 11</code>)."
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
                "title": "Rank All Students by Total Confirmed Tuition Fee Descending",
                "req": "List all students ordered by total confirmed tuition fee descending, regardless of whether they have paid; break ties by <code>student_id</code> ascending.",
                "analysis": (
                    "<strong>Anti-Fanout / Chasm Trap Prevention:</strong> Confirmed tuition fees reside in <code>lesson_reports</code> (which has a strict 1–1 relationship with <code>lessons</code> via <code>lesson_id UNIQUE</code>). "
                    "Thus, we perform a <code>LEFT JOIN</code> from <code>students</code> to <code>lessons</code> (with <code>l.status = 'Completed'</code>) and <code>lesson_reports</code> without joining <code>payments</code>. "
                    "If <code>payments</code> were joined directly, Le Hoang Minh Khoi (<code>student_id = 1</code>, who paid for Lesson 1 in 2 installments) would have Lesson 1's fee of 500,000 VND double-counted. "
                    "Students tied in total confirmed fee (e.g., Students 6 and 9 at <code>400000.00</code>; Students 8, 10, 11 at <code>0.00</code>) are ordered deterministically by <code>student_id ASC</code>."
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
                "title": "Calculate Each Tutor's Lesson Cancellation Rate in 2025",
                "req": "Calculate the cancellation rate for each tutor in 2025: <code>(Cancelled lessons / total lessons in 2025) * 100</code>. Round to 2 decimal places; return <code>NULL</code> if total lessons is <code>0</code>.",
                "analysis": (
                    "Use a <code>LEFT JOIN</code> from <code>tutors</code> to <code>lessons</code> with the 2025 date range inside the <code>ON</code> clause so tutors with no lessons in 2025 are retained (Tutor 6 M.Sc. Pham Duc Chung only taught in 2024). "
                    "Count cancelled lessons conditionally via <code>SUM(CASE WHEN l.status = 'Cancelled' THEN 1 ELSE 0 END)</code>. "
                    "To prevent division by zero and return <code>NULL</code> when a tutor has 0 lessons in 2025, use <code>NULLIF(COUNT(l.lesson_id), 0)</code> in the denominator wrapped inside <code>ROUND(..., 2)</code>."
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
                "title": "List Students with More Than 3 Completed Lessons in 2025",
                "req": "List students who have more than 3 <code>Completed</code> lessons in 2025, along with their lesson count; order by count descending.",
                "analysis": (
                    "Perform an <code>INNER JOIN</code> between <code>students</code> and <code>lessons</code>, filtering for <code>l.status = 'Completed'</code> and the 2025 date range in the <code>WHERE</code> clause. "
                    "Group by student (<code>GROUP BY s.student_id, s.full_name</code>) and apply the post-aggregation filter <code>HAVING COUNT(l.lesson_id) &gt; 3</code> (i.e., 4 or more completed lessons). "
                    "The query accurately returns the 2 qualifying students: Le Hoang Minh Khoi (5 lessons) and Nguyen Phuong Anh (4 lessons)."
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
                caption=f"Table 4.{q['num']}: Live execution result of Query {q['num']} on MySQL.",
            )
            queries_html_blocks.append(
                f"""
                <div class="query-card">
                    <div class="query-header">
                        <span class="query-badge">Query {q['num']}</span>
                        <h3>{q['title']}</h3>
                    </div>
                    <div class="query-body">
                        <p class="query-req"><strong>Requirement:</strong> {q['req']}</p>
                        <p class="query-analysis"><strong>Technical Analysis &amp; Solution Design:</strong> {q['analysis']}</p>
                        <pre class="sql-code"><code>{html.escape(q['sql'])}</code></pre>
                        {out_tbl}
                    </div>
                </div>
                """
            )

        # Extract results of the 3 VIEWs in views.sql
        tbl_v_detail = render_table(
            *run_query("SELECT * FROM v_detail ORDER BY lesson_id ASC;"),
            caption="Table 5.1: Live query result from VIEW v_detail (all 23 lessons across all time, retaining fee = NULL for unreported lessons).",
            compact=True,
        )
        tbl_v_group = render_table(
            *run_query("SELECT * FROM v_group_summary ORDER BY subject_id ASC;"),
            caption="Table 5.2: Live query result from VIEW v_group_summary (all-time summary across all 6 subjects).",
        )
        tbl_v_debt = render_table(
            *run_query(
                "SELECT * FROM v_debt ORDER BY remaining_debt DESC, student_id ASC;"
            ),
            caption="Table 5.3: Live query result from VIEW v_debt (accounts receivable summary for all 11 students with anti-fanout protection).",
        )

    finally:
        if started_by_us:
            stop_mysql()

    neu_logo_uri = img_to_data_uri(ASSETS_DIR / "logo_neu.png")
    fda_logo_uri = img_to_data_uri(ASSETS_DIR / "logo_fda.png")
    erd_svg = build_erd_svg()

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Report Topic 01: Tutoring Center Management System (tutoring_mini)</title>
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
    margin: 0 0 10px 0;
    text-align: center;
  }}
  .faculty-name {{
    font-size: 12pt;
    font-weight: 800;
    color: #0f172a;
    margin: 0;
    text-align: center;
  }}

  .logo-row {{
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 48px;
    margin: 22px 0 12px 0;
  }}
  .logo-box {{
    display: flex;
    flex-direction: column;
    align-items: center;
  }}
  .logo-box img {{
    width: 104px;
    height: 104px;
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
    padding: 18px 14px;
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    border-top: 2.5px solid #1e3a8a;
    border-bottom: 2.5px solid #1e3a8a;
    border-radius: 8px;
    margin: 8px 0;
  }}
  .report-type {{
    font-size: 12.5pt;
    font-weight: 800;
    color: #1e40af;
    letter-spacing: 1px;
    margin-bottom: 8px;
  }}
  .report-main-title {{
    font-size: 17.5pt;
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
  .instructor-line {{
    font-size: 10.5pt;
    font-weight: 700;
    color: #0f172a;
    text-align: center;
    margin: 0 0 12px 0;
    padding: 6px 14px;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 6px;
  }}
  .instructor-line span {{
    color: #1e3a8a;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    margin-right: 6px;
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
  .github-repo-box {{
    margin-top: 12px;
    padding: 8px 14px;
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    text-align: center;
    font-size: 9.5pt;
    color: #1e293b;
  }}
  .github-repo-box a {{
    color: #1d4ed8;
    font-weight: 700;
    text-decoration: none;
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 9.2pt;
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
<!-- COVER PAGE                                                            -->
<!-- ===================================================================== -->
<div class="cover-page">
  <div class="cover-inner-border">
    <div class="cover-top">
      <div class="quoc-hieu">SOCIALIST REPUBLIC OF VIETNAM</div>
      <div class="tieu-ngu">Independence - Freedom - Happiness</div>
      <div class="divider-short"></div>

      <p class="uni-name">NATIONAL ECONOMICS UNIVERSITY (NEU)</p>
      <p class="faculty-name">FACULTY OF DATA SCIENCE AND ARTIFICIAL INTELLIGENCE (FDA)</p>

      <div class="logo-row">
        <div class="logo-box">
          <img src="{neu_logo_uri}" alt="NEU Logo">
          <span class="logo-caption">UNIVERSITY LOGO (NEU)</span>
        </div>
        <div class="logo-box">
          <img src="{fda_logo_uri}" alt="FDA Logo">
          <span class="logo-caption">FACULTY LOGO (FDA)</span>
        </div>
      </div>
    </div>

    <div class="cover-title-block">
      <div class="report-type">MYSQL DATABASE PRACTICAL PROJECT REPORT</div>
      <h1 class="report-main-title">TOPIC 01: TUTORING CENTER MANAGEMENT SYSTEM</h1>
      <div class="report-db-badge">Database Schema: tutoring_mini</div>
    </div>

    <div class="cover-meta">
      <div class="instructor-line">
        <span>Instructor:</span> Dr. Tran Duc Minh
      </div>
      <div class="meta-member-title">PROJECT TEAM MEMBERS</div>
      <table class="member-table">
        <thead>
          <tr>
            <th style="width: 8%; text-align: center;">No.</th>
            <th style="width: 32%;">Student Full Name</th>
            <th style="width: 18%; text-align: center;">Student ID</th>
            <th style="width: 42%;">Assigned Responsibilities</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td class="center-cell"><strong>1</strong></td>
            <td><strong>Pham Ngoc Danh</strong></td>
            <td class="center-cell"><strong>11251809</strong></td>
            <td>Database schema design (<code>schema.sql</code>), analytical VIEWs (<code>views.sql</code>) &amp; Report compilation</td>
          </tr>
          <tr>
            <td class="center-cell"><strong>2</strong></td>
            <td><strong>Nguyen Manh Dung</strong></td>
            <td class="center-cell"><strong>11252140</strong></td>
            <td>Sample dataset design (<code>seed.sql</code>), integrity verification &amp; Queries 1 – 5</td>
          </tr>
          <tr>
            <td class="center-cell"><strong>3</strong></td>
            <td><strong>Hoang Duc Duong</strong></td>
            <td class="center-cell"><strong>11252228</strong></td>
            <td>Development &amp; testing of Queries 6 – 10 in <code>queries.sql</code> &amp; GitHub repository packaging</td>
          </tr>
        </tbody>
      </table>
      <div class="github-repo-box">
        <strong>GitHub Repository:</strong>
        <a href="https://github.com/pdanh4992/mysql-tutoring-center-management">https://github.com/pdanh4992/mysql-tutoring-center-management</a>
      </div>
    </div>

    <div class="cover-footer">
      HANOI — 2026
    </div>
  </div>
</div>

<!-- ===================================================================== -->
<!-- SECTION 1: OVERVIEW & BUSINESS PROBLEM ANALYSIS                       -->
<!-- ===================================================================== -->
<div class="section-banner">
  <h1>Section 1. Overview &amp; Business Problem Analysis</h1>
</div>

<h2>1.1. Objectives and Business Context</h2>
<p>
  The <strong>Tutoring Center Management System (<code>tutoring_mini</code>)</strong> relational database is engineered to standardize and automate the end-to-end operational workflow of a modern academic tutoring center: from managing the catalog of academic subjects (<code>subjects</code>), tutor qualifications and subject assignments (<code>tutors</code>), and student profiles (<code>students</code>), to coordinating lesson schedules and lifecycle statuses (<code>lessons</code>), recording post-lesson academic evaluations and confirmed tuition fees (<code>lesson_reports</code>), and tracking single or multi-installment tuition payments (<code>payments</code>).
</p>

<h2>1.2. Core Business Rules &amp; Data Integrity Constraints</h2>
<div class="callout">
  <div class="callout-title">5 Mandatory Business &amp; Integrity Rules in tutoring_mini</div>
  <ol style="margin-bottom:0;">
    <li><strong>Tutor Subject Assignment (1 – N):</strong> Each academic subject has a unique name (<code>UNIQUE</code>). Each tutor specializes in teaching one specific subject and holds a unique institutional <code>email</code> address.</li>
    <li><strong>Lesson Status Lifecycle (<code>ENUM</code>):</strong> Every scheduled lesson between a student and a tutor must be in one of three states: <code>'Pending'</code> (Scheduled/Awaiting completion), <code>'Completed'</code> (Finished), or <code>'Cancelled'</code> (Cancelled).</li>
    <li><strong>Post-Lesson Reporting Rule (Strict 1 – 1 Relationship):</strong> Only lessons with status <code>'Completed'</code> may have a <code>lesson_reports</code> entry, and <strong>every</strong> <code>'Completed'</code> lesson must have exactly one report (enforced via <code>lesson_id UNIQUE</code>, positive duration <code>duration_minutes &gt; 0</code>, and non-negative tuition fee <code>fee &gt;= 0</code>).</li>
    <li><strong>Tuition Collection &amp; Installment Payments (1 – N Relationship):</strong> Payments are collected only for lessons that already have a confirmed report (<code>lesson_reports</code>). A lesson may be paid in full at once, paid across multiple installments (multiple rows in <code>payments</code> sharing the same <code>lesson_id</code>), or remain partially/fully unpaid, provided the cumulative amount paid (<code>SUM(amount)</code>) for any <code>lesson_id</code> never exceeds its confirmed tuition fee (<code>fee</code>).</li>
    <li><strong>Anti-Fanout / Chasm Trap Prevention:</strong> Because <code>lesson_reports</code> has a 1–1 relationship with <code>lessons</code> whereas <code>payments</code> has a 1–N relationship with <code>lessons</code>, any query or view that simultaneously aggregates confirmed fees (<code>fee</code>) and paid amounts (<code>amount</code>) must pre-aggregate <code>payments</code> by <code>lesson_id</code> inside a Subquery/CTE before joining to <code>lesson_reports</code> so that tuition fees are never multiplied.</li>
  </ol>
</div>

<!-- ===================================================================== -->
<!-- SECTION 2: DATABASE SCHEMA DESIGN (PART A)                            -->
<!-- ===================================================================== -->
<div class="section-banner">
  <h1>Section 2. Database Schema Design (Part A — schema.sql)</h1>
</div>

<h2>2.1. Entity-Relationship Diagram (ERD)</h2>
<p>
  The <code>tutoring_mini</code> database is normalized to Third Normal Form (<strong>3NF</strong>), eliminating data redundancy and update, insertion, or deletion anomalies. The relationships among the 6 tables are illustrated in Figure 2.1:
</p>
{erd_svg}

<h2>2.2. Detailed Specification of the 6 Tables and Integrity Constraints</h2>
<div class="table-wrap">
  <table class="data-table compact-table">
    <thead>
      <tr>
        <th style="width:14%;">Table Name</th>
        <th style="width:24%;">Columns (Primary Key First)</th>
        <th style="width:18%;">Primary / Foreign Keys</th>
        <th style="width:44%;">Integrity Constraints (UNIQUE, CHECK, ENUM) &amp; Design Rationale</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><code>subjects</code></td>
        <td><code>subject_id</code>, <code>name</code></td>
        <td><strong>PK:</strong> <code>subject_id</code></td>
        <td><code>name VARCHAR(100) NOT NULL UNIQUE</code> — Prevents duplicate subject names in the academic catalog.</td>
      </tr>
      <tr>
        <td><code>tutors</code></td>
        <td><code>tutor_id</code>, <code>full_name</code>, <code>email</code>, <code>qualification</code>, <code>subject_id</code></td>
        <td><strong>PK:</strong> <code>tutor_id</code><br><strong>FK:</strong> <code>subject_id</code> → <code>subjects(subject_id)</code></td>
        <td>All columns are <code>NOT NULL</code>; <code>email UNIQUE</code> prevents duplicate tutor accounts; <code>FK</code> ensures every tutor is assigned to a valid subject.</td>
      </tr>
      <tr>
        <td><code>students</code></td>
        <td><code>student_id</code>, <code>full_name</code>, <code>dob</code>, <code>phone</code></td>
        <td><strong>PK:</strong> <code>student_id</code></td>
        <td><code>full_name</code>, <code>dob (DATE)</code>, and <code>phone</code> are all <code>NOT NULL</code> — Stores complete identity and contact records for each student.</td>
      </tr>
      <tr>
        <td><code>lessons</code></td>
        <td><code>lesson_id</code>, <code>student_id</code>, <code>tutor_id</code>, <code>lesson_date</code>, <code>status</code></td>
        <td><strong>PK:</strong> <code>lesson_id</code><br><strong>FK1:</strong> <code>student_id</code> → <code>students</code><br><strong>FK2:</strong> <code>tutor_id</code> → <code>tutors</code></td>
        <td><code>lesson_date DATE NOT NULL</code>; <code>status ENUM('Pending', 'Completed', 'Cancelled') NOT NULL</code> — Strictly restricts lesson status values at the storage engine level.</td>
      </tr>
      <tr>
        <td><code>lesson_reports</code></td>
        <td><code>report_id</code>, <code>lesson_id</code>, <code>content</code>, <code>feedback</code>, <code>duration_minutes</code>, <code>fee</code></td>
        <td><strong>PK:</strong> <code>report_id</code><br><strong>FK + UQ:</strong> <code>lesson_id</code> → <code>lessons(lesson_id)</code></td>
        <td><code>lesson_id UNIQUE</code> enforces a strict <strong>1–1</strong> relationship (at most one report per lesson); <code>CHECK (duration_minutes &gt; 0)</code> and <code>CHECK (fee &gt;= 0)</code> enforce valid numeric domains.</td>
      </tr>
      <tr>
        <td><code>payments</code></td>
        <td><code>payment_id</code>, <code>lesson_id</code>, <code>amount</code>, <code>payment_date</code>, <code>method</code></td>
        <td><strong>PK:</strong> <code>payment_id</code><br><strong>FK:</strong> <code>lesson_id</code> → <code>lessons(lesson_id)</code></td>
        <td>No <code>UNIQUE</code> constraint on <code>lesson_id</code> to allow multi-installment payments (1–N); <code>CHECK (amount &gt; 0)</code>; <code>method ENUM('Cash', 'BankTransfer', 'Card') NOT NULL</code>.</td>
      </tr>
    </tbody>
  </table>
  <div class="table-caption">Table 2.1: Summary of the 6-table schema architecture and integrity constraints in <code>schema.sql</code>.</div>
</div>

<p>
  <strong>MySQL Technical Note:</strong> In MySQL 8.0/9.0, <code>CHECK</code> constraints cannot contain subqueries referencing other tables. Therefore, single-table domain rules (<code>duration_minutes &gt; 0</code>, <code>fee &gt;= 0</code>, <code>amount &gt; 0</code>) are enforced directly via declarative <code>CHECK</code> constraints in <code>schema.sql</code>, while cross-table business rules (only <code>Completed</code> lessons have reports, and cumulative <code>amount &lt;= fee</code>) are verified via automated reconciliation queries at the end of <code>seed.sql</code>.
</p>

<h2>2.3. Complete Source Code of <code>schema.sql</code></h2>
<pre class="sql-code"><code>{html.escape(schema_code)}</code></pre>

<!-- ===================================================================== -->
<!-- SECTION 3: SAMPLE DATA & INTEGRITY VERIFICATION (PART B)              -->
<!-- ===================================================================== -->
<div class="section-banner section-page-break">
  <h1>Section 3. Sample Data &amp; Integrity Verification (Part B — seed.sql)</h1>
</div>

<h2>3.1. Sample Dataset Design Matrix Covering All Required Edge Cases</h2>
<p>
  The sample dataset in <code>seed.sql</code> exceeds all minimum row-count thresholds and is systematically designed to cover all 10 required edge-case scenarios for testing the 10 analytical queries and 3 VIEWs:
</p>

<div class="table-wrap">
  <table class="data-table compact-table">
    <thead>
      <tr>
        <th style="width:5%;">No.</th>
        <th style="width:35%;">Required Data Scenario / Edge Case</th>
        <th style="width:20%;">Actual Coverage</th>
        <th style="width:40%;">Specific Records in <code>seed.sql</code></th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td class="center-cell">1</td>
        <td>Minimum row count per table</td>
        <td>6 / 6 / 11 / 23 / 16 / 17</td>
        <td><code>subjects</code>=6 (≥5), <code>tutors</code>=6 (≥6), <code>students</code>=11 (≥10), <code>lessons</code>=23 (≥12), <code>lesson_reports</code>=16 (≥10), <code>payments</code>=17 (≥10).</td>
      </tr>
      <tr>
        <td class="center-cell">2</td>
        <td>Temporal diversity: Jan 2025, rest of Q1/2025 (Feb, Mar), outside Q1/2025, outside 2025</td>
        <td>All 4 time partitions covered</td>
        <td>• Jan 2025: <code>lesson_id</code> 1, 2, 6, 10, 22<br>• Feb &amp; Mar 2025: <code>lesson_id</code> 3, 4, 7, 8, 11, 12, 15, 17, 19, 20, 21, 23<br>• Outside Q1/2025 (May, Jun 2025): <code>lesson_id</code> 5, 9, 13, 18<br>• Year 2024: <code>lesson_id</code> 14 (<code>2024-11-15</code>), 16 (<code>2024-12-10</code>).</td>
      </tr>
      <tr>
        <td class="center-cell">3</td>
        <td>All 3 lesson statuses &amp; strict 1–1 mapping between <code>Completed</code> and <code>lesson_reports</code></td>
        <td>16 Completed, 4 Pending, 3 Cancelled</td>
        <td>All 16/16 <code>Completed</code> lessons (<code>lesson_id</code> 1..16) have reports in <code>lesson_reports</code>; 0 <code>Pending</code>/<code>Cancelled</code> lessons have reports.</td>
      </tr>
      <tr>
        <td class="center-cell">4</td>
        <td>At least 1 student with <strong>more than 3 Completed lessons</strong> in 2025 (≥ 4 lessons)</td>
        <td>2 qualifying students</td>
        <td>• <code>student_id = 1</code> (Le Hoang Minh Khoi): <strong>5 Completed lessons</strong> in 2025 (lessons 1, 2, 3, 4, 5)<br>• <code>student_id = 2</code> (Nguyen Phuong Anh): <strong>4 Completed lessons</strong> in 2025 (lessons 6, 7, 8, 9).</td>
      </tr>
      <tr>
        <td class="center-cell">5</td>
        <td>At least 1 student with lesson history but zero payments</td>
        <td>2 students</td>
        <td>• <code>student_id = 7</code> (Vu Ngoc Ha): Has lesson 15 (<code>Completed</code>, fee 450,000) and lesson 18 (<code>Pending</code>), but 0 records in <code>payments</code>.<br>• <code>student_id = 8</code> (Bui Duc Thinh): Has lessons 19, 20 (<code>Pending</code>) and 22 (<code>Cancelled</code>), 0 payments.</td>
      </tr>
      <tr>
        <td class="center-cell">6</td>
        <td>At least 1 student who has never had any lessons</td>
        <td>2 students</td>
        <td><code>student_id = 10</code> (Ngo Hai Dang) and <code>student_id = 11</code> (Ly Thanh Truc) — 0 rows in <code>lessons</code>.</td>
      </tr>
      <tr>
        <td class="center-cell">7</td>
        <td>At least 1 lesson paid in multiple installments (multiple <code>payments</code> rows for the same <code>lesson_id</code>)</td>
        <td>2 multi-installment lessons</td>
        <td>• <code>lesson_id = 1</code>: <code>payment_id</code> 1 (300,000) + <code>payment_id</code> 2 (200,000) = 500,000 (fully paid in 2 installments).<br>• <code>lesson_id = 6</code>: <code>payment_id</code> 7 (200,000) + <code>payment_id</code> 8 (150,000) = 350,000 / 500,000 (paid in 2 installments, owes 150,000).</td>
      </tr>
      <tr>
        <td class="center-cell">8</td>
        <td>At least 1 lesson with outstanding debt (total <code>amount &lt; fee</code>)</td>
        <td>4 lessons with remaining debt</td>
        <td><code>lesson_id = 6</code> (owes 150,000), <code>lesson_id = 10</code> (owes 200,000), <code>lesson_id = 13</code> (owes 200,000), <code>lesson_id = 15</code> (owes 450,000 — unpaid).</td>
      </tr>
      <tr>
        <td class="center-cell">9</td>
        <td>At least 1 subject with no lessons in Q1/2025</td>
        <td>2 subjects</td>
        <td>• <code>subject_id = 5</code> (Macroeconomics 1): only has 2 lessons in 2024.<br>• <code>subject_id = 6</code> (General Law): 0 lessons across all time.</td>
      </tr>
      <tr>
        <td class="center-cell">10</td>
        <td>At least 1 tutor with no lessons in 2025</td>
        <td>1 tutor</td>
        <td>• <code>tutor_id = 6</code> (M.Sc. Pham Duc Chung): taught 2 lessons in 2024, 0 lessons in 2025.</td>
      </tr>
    </tbody>
  </table>
  <div class="table-caption">Table 3.0: Traceability matrix mapping <code>seed.sql</code> sample data to all project requirements.</div>
</div>

<h2>3.2. Seeded Data Across the 6 Tables</h2>
{tbl_subjects}
{tbl_tutors}
{tbl_students}
{tbl_lessons}
{tbl_reports}
{tbl_payments}

<h2>3.3. Execution Results of Data Integrity Verification Queries in <code>seed.sql</code></h2>
<p>
  At the end of <code>seed.sql</code>, 4 automated reconciliation <code>SELECT</code> queries verify that the seeded dataset strictly satisfies the 1–1 reporting rule (for <code>Completed</code> lessons) and the payment cap rule (<code>SUM(amount) &lt;= fee</code>):
</p>
{ver_1a}
{ver_1b}
{ver_2a}
{ver_2b}

<h2>3.4. Analysis of Commented-Out Constraint Violation <code>INSERT</code> Statements</h2>
<div class="callout callout-warn">
  <div class="callout-title">4 Negative Test Cases Included as Comments at the End of seed.sql</div>
  <ul style="margin-bottom:0;">
    <li><strong>Foreign Key Violation (<code>FOREIGN KEY</code>):</strong> <code>INSERT INTO lessons ... VALUES (999, 1, '2025-04-01', 'Pending');</code> — Rejected by <code>fk_lessons_student</code> (MySQL <code>ERROR 1452: Cannot add or update a child row</code>) because <code>student_id = 999</code> does not exist.</li>
    <li><strong>Check Constraint Violation (<code>duration_minutes &lt;= 0</code>):</strong> <code>INSERT INTO lesson_reports ... VALUES (17, 'Review Data Analysis with Python', 'Good', 0, 450000.00);</code> — Rejected by <code>chk_report_duration</code> (MySQL <code>ERROR 3819: Check constraint is violated</code>).</li>
    <li><strong>Check Constraint Violation (<code>amount &lt;= 0</code>):</strong> <code>INSERT INTO payments ... VALUES (1, -50000.00, '2025-01-15', 'Cash');</code> — Rejected by <code>chk_payment_amount</code> (MySQL <code>ERROR 3819</code>).</li>
    <li><strong>Unique Constraint Violation (Duplicate <code>lesson_id</code>):</strong> <code>INSERT INTO lesson_reports (lesson_id, ...) VALUES (1, ...);</code> — Rejected by <code>UNIQUE (lesson_id)</code> (MySQL <code>ERROR 1062: Duplicate entry '1'</code>).</li>
  </ul>
</div>

<!-- ===================================================================== -->
<!-- SECTION 4: 10 ANALYTICAL DATA QUERIES (PART C)                        -->
<!-- ===================================================================== -->
<div class="section-banner section-page-break">
  <h1>Section 4. 10 Analytical Data Queries (Part C — queries.sql)</h1>
</div>

<div class="callout callout-success">
  <div class="callout-title">Core Technical Principle: Anti-Fanout / Chasm Trap Prevention</div>
  <p style="margin-bottom:0;">
    In the <code>tutoring_mini</code> schema, a lesson (<code>lessons</code>) has at most <strong>1</strong> tuition report (<code>lesson_reports.fee</code>) but can have <strong>N</strong> payment installments (<code>payments.amount</code>). Joining <code>lessons JOIN lesson_reports JOIN payments</code> directly and computing <code>SUM(lr.fee)</code> or <code>AVG(lr.fee)</code> causes multi-installment lessons (such as <code>lesson_id = 1</code> and <code>lesson_id = 6</code>, each paid in 2 installments) to duplicate <code>lr.fee</code>! To eliminate this fanout error: (1) Queries that only aggregate tuition fees (Query 4, Query 8, <code>v_group_summary</code>) join <code>lesson_reports</code> without joining <code>payments</code>; (2) Reconciliations that combine both fees and payments (such as <code>v_debt</code>) <strong>pre-aggregate <code>payments</code> by <code>lesson_id</code> inside a Subquery first</strong> to restore a 1–1 cardinality before performing the outer join.
  </p>
</div>

{''.join(queries_html_blocks)}

<!-- ===================================================================== -->
<!-- SECTION 5: ALL-TIME ANALYTICAL VIEWS (PART D)                         -->
<!-- ===================================================================== -->
<div class="section-banner section-page-break">
  <h1>Section 5. All-Time Analytical VIEWs (Part D — views.sql)</h1>
</div>

<p>
  The three views (<code>VIEW</code>) in <code>views.sql</code> operate across the entire historical timeline (covering both 2024 and 2025 records), providing standardized reporting interfaces for executive management and student accounts receivable:
</p>

<h2>5.1. Design and Live Output of <code>v_detail</code></h2>
<p>
  <strong>Design Logic:</strong> View <code>v_detail</code> performs an <code>INNER JOIN</code> from <code>lessons</code> to <code>students</code>, <code>tutors</code>, and <code>subjects</code> to retrieve both IDs and names for students, tutors, and subjects, followed by a <code>LEFT JOIN</code> to <code>lesson_reports</code> so that <code>Pending</code> and <code>Cancelled</code> lessons without a report are preserved (displaying <code>fee</code> as <code>NULL</code>).
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

<h2>5.2. Design and Live Output of <code>v_group_summary</code></h2>
<p>
  <strong>Design Logic:</strong> View <code>v_group_summary</code> starts from <code>subjects</code> and chains <code>LEFT JOIN</code> operations through <code>tutors → lessons → lesson_reports</code>. Consequently, subjects that have never had any lessons (<em>General Law</em>, <code>subject_id = 6</code>) are retained with zero counts and <code>total_fee = 0.00</code>. Omitting the <code>payments</code> table guarantees that <code>SUM(lr.fee)</code> is free of installment fanout.
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

<h2>5.3. Design and Live Output of <code>v_debt</code> (Anti-Fanout Protection)</h2>
<p>
  <strong>Design Logic:</strong> View <code>v_debt</code> summarizes tuition obligations and payments for all 11 students. To <strong>prevent tuition fee duplication</strong> when a lesson is paid across multiple installments (such as <code>lesson_id = 1</code> for Le Hoang Minh Khoi and <code>lesson_id = 6</code> for Nguyen Phuong Anh), the derived table <code>pay_per_lesson</code> pre-aggregates <code>SUM(amount)</code> grouped by <code>lesson_id</code> before left-joining with <code>lessons</code> and <code>lesson_reports</code>:
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
    print(f"Generated HTML preview: {HTML_OUTPUT}")

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
              <span><strong>FDA - NEU</strong> | Faculty of Data Science and Artificial Intelligence</span>
              <span>Topic 01: Tutoring Center Management System (tutoring_mini)</span>
            </div>
            """,
            footer_template="""
            <div style="width:100%; font-size:7.5pt; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color:#64748b; padding:0 16mm; display:flex; justify-content:space-between; border-top:0.5px solid #cbd5e1;">
              <span>MySQL Database Practical Project Report — Topic 01 (tutoring_mini)</span>
              <span>Page <span class="pageNumber"></span> / <span class="totalPages"></span></span>
            </div>
            """,
        )
        browser.close()

    if HTML_OUTPUT.exists():
        HTML_OUTPUT.unlink()
    print(f"Successfully rendered PDF: {PDF_OUTPUT} ({PDF_OUTPUT.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    generate_html_report()
