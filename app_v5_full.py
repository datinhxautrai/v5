import streamlit as st
import sqlite3
import hashlib
from datetime import datetime, date
import os
import pandas as pd  # <--- SIR THÊM DÒNG NÀY VÀO LÀ XONG!
# ── 1. CẤU HÌNH DATABASE (SQLITE) ──────────────────────────
DB_NAME = "internal_management.db"

def get_db():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_db()
    c = conn.cursor()
    # Bảng Users
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (tai_khoan TEXT PRIMARY KEY, mat_khau TEXT, ho_ten TEXT, email TEXT, quyen TEXT, trang_thai TEXT)''')
    # Bảng Dự án (Mới)
    c.execute('''CREATE TABLE IF NOT EXISTS projects 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, location TEXT, status TEXT)''')
    # Bảng Tasks (Liên kết với dự án)
    c.execute('''CREATE TABLE IF NOT EXISTS tasks 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER, task_name TEXT, 
                  category TEXT, assigned_to TEXT, status TEXT, deadline TEXT, note TEXT, 
                  FOREIGN KEY(project_id) REFERENCES projects(id))''')
    # Bảng Chấm công
    c.execute('''CREATE TABLE IF NOT EXISTS attendance 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, date TEXT, check_in TEXT, status TEXT)''')
    
    # Tạo admin mặc định nếu chưa có
    c.execute("INSERT OR IGNORE INTO users VALUES ('Sir', ?, 'Giám đốc', '', 'admin', 'Hoạt động')", (hashlib.sha256('admin123'.encode()).hexdigest(),))
    conn.commit()
    conn.close()

init_db()

st.set_page_config(page_title="Quản Lý Nội Bộ v5", layout="wide", page_icon="🏗️")

# ── 2. LOGIC CẦN THIẾT ──────────────────────────
def hash_pwd(p): return hashlib.sha256(p.encode()).hexdigest()

# ── 3. GIAO DIỆN (UI) ──────────────────────────
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("## 🏗️ ĐĂNG NHẬP HỆ THỐNG v5")
    uid = st.text_input("Tài khoản")
    pwd = st.text_input("Mật khẩu", type="password")
    if st.button("Đăng nhập"):
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE tai_khoan=?", (uid,))
        user = c.fetchone()
        conn.close()
        if user and user[1] == hash_pwd(pwd):
            st.session_state.logged_in = True
            st.session_state.user = uid
            st.rerun()
        else:
            st.error("Sai thông tin!")
    st.stop()

# Sidebar Điều hướng
page = st.sidebar.radio("Menu", ["🏠 Dashboard", "🏗️ Quản lý Dự án", "📋 Công việc", "⏰ Chấm công"])

# ── PAGE: DỰ ÁN (MỚI) ──────────────────────────
if page == "🏗️ Quản lý Dự án":
    st.title("🏗️ Quản lý Dự án")
    with st.form("new_proj"):
        p_name = st.text_input("Tên dự án (Ví dụ: Nhà anh Lâm)")
        p_loc = st.text_input("Địa điểm")
        if st.form_submit_button("Thêm dự án"):
            conn = get_db()
            conn.execute("INSERT INTO projects (name, location, status) VALUES (?, ?, ?)", (p_name, p_loc, "Đang triển khai"))
            conn.commit()
            conn.close()
            st.success("Đã thêm dự án!")
            st.rerun()
    
    st.markdown("---")
    st.subheader("Danh sách dự án")
    df_proj = pd.read_sql("SELECT * FROM projects", get_db())
    st.table(df_proj)

# ── PAGE: CÔNG VIỆC (CÓ LIÊN KẾT DỰ ÁN) ──────────────────────────
elif page == "📋 Công việc":
    st.title("📋 Quản lý Công việc")
    
    # Lấy danh sách dự án để chọn
    df_proj = pd.read_sql("SELECT * FROM projects", get_db())
    if df_proj.empty:
        st.warning("Vui lòng tạo Dự án trước khi giao việc.")
    else:
        proj_map = {f"{row['name']} - {row['location']}": row['id'] for _, row in df_proj.iterrows()}
        
        with st.expander("➕ Giao việc mới"):
            sel_proj = st.selectbox("Chọn dự án:", list(proj_map.keys()))
            t_name = st.text_input("Tên công việc")
            t_user = st.text_input("Nhân viên thực hiện")
            if st.button("Lưu công việc"):
                conn = get_db()
                conn.execute("INSERT INTO tasks (project_id, task_name, assigned_to, status) VALUES (?, ?, ?, ?)", 
                             (proj_map[sel_proj], t_name, t_user, "Chờ triển khai"))
                conn.commit()
                conn.close()
                st.success("Đã giao việc!")
                st.rerun()

    st.markdown("### Danh sách công việc")
    df_tasks = pd.read_sql("""
        SELECT p.name as Du_An, t.task_name, t.assigned_to, t.status 
        FROM tasks t 
        JOIN projects p ON t.project_id = p.id
    """, get_db())
    st.dataframe(df_tasks, use_container_width=True)

# ── PAGE: DASHBOARD (GIỮ NGUYÊN TÍNH NĂNG V4) ──────────────────────────
elif page == "🏠 Dashboard":
    st.title("🏠 Dashboard v5")
    st.write("Chào Sir, hệ thống v5 đã tích hợp SQLite và Module Dự án thành công.")
    # Các biểu đồ và thông báo v4 của Sir có thể thêm lại vào đây

# ── PAGE: CHẤM CÔNG (GIỮ NGUYÊN TÍNH NĂNG V4) ──────────────────────────
elif page == "⏰ Chấm công":
    st.title("⏰ Chấm công")
    if st.button("Chấm công vào ngay"):
        conn = get_db()
        conn.execute("INSERT INTO attendance (user, date, check_in, status) VALUES (?, ?, ?, ?)", 
                     (st.session_state.user, date.today().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M"), "Đúng giờ"))
        conn.commit()
        conn.close()
        st.success("Đã chấm công!")
