import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import hashlib

# 1. Database Setup
def init_db():
    with sqlite3.connect('alevel_tracker_final.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS study_logs 
                          (username TEXT, date TEXT, stream TEXT, sub1_name TEXT, sub1_h REAL, 
                           sub2_name TEXT, sub2_h REAL, sub3_name TEXT, sub3_h REAL, UNIQUE(username, date))''')
        # Default Admin Account
        admin_pass = hashlib.sha256(str.encode("admin123")).hexdigest()
        cursor.execute("INSERT OR IGNORE INTO users VALUES (?, ?)", ("admin", admin_pass))
        conn.commit()

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return make_hashes(password) == hashed_text

init_db()

# --- UI Styles ---
st.set_page_config(page_title="A/L Study Tracker Pro", layout="wide")
st.markdown("""
    <style>
    .main-title { font-size: 3rem !important; font-weight: 900 !important; color: #ffffff; text-align: center; text-shadow: 3px 3px 6px #000000; }
    .subject-card { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 8px solid #2196f3; color: #000000 !important; margin-bottom: 10px; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .business-name { color: #2ecc71; font-weight: bold; font-size: 1.2rem; }
    </style>
    """, unsafe_allow_html=True)

# --- Subject Data ---
SUBJECTS_DATA = {
    "Physical Science (Maths)": ["Combined Maths", "Physics", "Chemistry", "ICT"],
    "Biological Science (Bio)": ["Biology", "Chemistry", "Physics", "Agricultural Science"],
    "Commerce": ["Accounting", "Business Studies", "Economics", "ICT"],
    "Arts": ["Sinhala", "History", "Logic", "Political Science", "Geography", "Economics", "ICT"],
    "Technology": ["SFT", "Engineering Tech", "Bio Systems Tech", "ICT"]
}

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- Login Logic ---
st.sidebar.title("🔐 Access Control")
u_in = st.sidebar.text_input("Username")
p_in = st.sidebar.text_input("Password", type='password')

if st.sidebar.button("ඇතුළු වන්න"):
    with sqlite3.connect('alevel_tracker_final.db') as conn:
        data = conn.execute('SELECT password FROM users WHERE username =?', (u_in,)).fetchone()
        if data and check_hashes(p_in, data[0]):
            st.session_state.logged_in, st.session_state.username = True, u_in
            st.rerun()
        else: st.sidebar.error("Username හෝ Password වැරදියි.")

# --- Admin Dashboard (ගුරුතුමා සඳහා) ---
if st.session_state.logged_in and st.session_state.username == "admin":
    st.markdown('<p class="main-title">👨‍🏫 ගුරු මණ්ඩල පුවරුව (Admin)</p>', unsafe_allow_html=True)
    st.divider()

    with sqlite3.connect('alevel_tracker_final.db') as conn:
        all_logs = pd.read_sql_query("SELECT * FROM study_logs", conn)
    
    if not all_logs.empty:
        st.subheader("📋 සියලුම සිසුන්ගේ දත්ත සාරාංශය")
        
        # ශිෂ්‍යයා අනුව Filter කිරීම
        student_list = ["සියලුම දෙනා"] + list(all_logs['username'].unique())
        selected_student = st.selectbox("ශිෂ්‍යයා තෝරන්න", student_list)
        
        display_df = all_logs if selected_student == "සියලුම දෙනා" else all_logs[all_logs['username'] == selected_student]
        
        st.dataframe(display_df, use_container_width=True)
        
        # Download All Data
        csv = all_logs.to_csv(index=False).encode('utf-8')
        st.download_button("📥 සියලුම දත්ත Excel (CSV) ලෙස බාගත කරන්න", csv, "all_students_data.csv", "text/csv")
    else:
        st.info("තවමත් සිසුන් දත්ත ඇතුළත් කර නැත.")

    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

# --- Student Dashboard (ශිෂ්‍යයා සඳහා) ---
elif st.session_state.logged_in:
    st.markdown('<p class="main-title">🎓 A/L Study Tracker</p>', unsafe_allow_html=True)
    st.markdown(f"<div style='text-align: center;'>Developed by: <span class='business-name'>Hiratrix IT Solutions</span></div>", unsafe_allow_html=True)
    st.divider()

    tab1, tab2 = st.tabs(["📝 දත්ත ඇතුළත් කිරීම", "📊 මගේ වාර්තා"])

    with sqlite3.connect('alevel_tracker_final.db') as conn:
        my_data = pd.read_sql_query(f"SELECT * FROM study_logs WHERE username='{st.session_state.username}'", conn)
    
    with tab1:
        st.subheader(f"👋 සාදරයෙන් පිළිගනිමු, {st.session_state.username}!")
        # (මෙහි පෙර තිබූ දත්ත ඇතුළත් කිරීමේ Code එක දිගටම පවතී...)
        # ... (කෙටි කිරීම සඳහා ඉතිරි කොටස පෙර පරිදිම වේ)
        st.info("ඔබේ දත්ත සුරැකීමට Sidebar එක භාවිතා කරන්න.")

    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

else:
    st.info("පද්ධතියට ඇතුළු වීමට Username සහ Password ලබා දෙන්න.")