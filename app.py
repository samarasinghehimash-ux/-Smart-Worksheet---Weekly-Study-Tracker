import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
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
        admin_pass = hashlib.sha256(str.encode("admin123")).hexdigest()
        cursor.execute("INSERT OR IGNORE INTO users VALUES (?, ?)", ("admin", admin_pass))
        conn.commit()

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return make_hashes(password) == hashed_text

init_db()

# --- Page Config ---
st.set_page_config(page_title="A/L Study Tracker Pro", layout="wide")

# --- UI Styles ---
st.markdown("""
    <style>
    .main-title { font-size: 3.5rem !important; font-weight: 900 !important; color: #ffffff; text-align: center; text-shadow: 3px 3px 6px #000000; margin-bottom: 5px; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-weight: bold !important; font-size: 2rem !important; }
    [data-testid="stMetricLabel"] p { color: #444444 !important; font-weight: bold !important; font-size: 1.1rem !important; }
    div[data-testid="stMetric"] { background-color: #ffffff !important; padding: 20px; border-radius: 15px; border: 1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .subject-card { background-color: #ffffff; padding: 18px; border-radius: 12px; border-left: 10px solid #2196f3; color: #000000 !important; margin-bottom: 12px; font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.05); font-size: 1.1rem; }
    .feedback-box { padding: 20px; border-radius: 15px; text-align: center; font-size: 1.5rem; font-weight: bold; margin: 20px 0; border: 2px solid; }
    .business-name { color: #2ecc71; font-weight: bold; font-size: 1.2rem; }
    .stButton>button { border-radius: 8px; }
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

# --- Sidebar Login ---
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

# --- Analytics Function ---
def display_full_analytics(df, start_date):
    end_date = start_date + timedelta(days=6)
    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
    week_df = df.loc[mask].sort_values('date')
    
    if not week_df.empty:
        total_h = week_df[['sub1_h', 'sub2_h', 'sub3_h']].sum().sum()
        
        # 1. Feedback System
        if total_h < 40:
            st.markdown(f'<div class="feedback-box" style="background-color: #ffebee; color: #c62828; border-color: #ef9a9a;">😟 ඔබ තවමත් දුර්වල මට්ටමක සිටින්නේ. තව ගොඩක් මහන්සි වෙන්න! (Total: {total_h:.1f}h)</div>', unsafe_allow_html=True)
        elif total_h < 60:
            st.markdown(f'<div class="feedback-box" style="background-color: #e8f5e9; color: #2e7d32; border-color: #a5d6a7;">🙂 ඉතා හොඳයි! තව උත්සාහ කරන්න, ඔබට පුළුවන්! (Total: {total_h:.1f}h)</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="feedback-box" style="background-color: #fff8e1; color: #ff8f00; border-color: #ffe082;">🔥 සුපිරි! ඔබ ඉතා දක්ෂ ලෙස වැඩ කර තිබෙනවා. මේ විදිහටම කරගෙන යමු! (Total: {total_h:.1f}h)</div>', unsafe_allow_html=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("📅 සතියේ මුළු පැය", f"{total_h:.1f} h")
        m2.metric("📊 දිනකට සාමාන්‍යය", f"{(total_h/7):.1f} h")
        m3.metric("✅ සටහන් කළ දින", f"{len(week_df)} / 7")
        st.write("---")
        
        last_entry = week_df.iloc[-1]
        sub_names = [last_entry['sub1_name'], last_entry['sub2_name'], last_entry['sub3_name']]
        sub_totals = {sub_names[0]: week_df['sub1_h'].sum(), sub_names[1]: week_df['sub2_h'].sum(), sub_names[2]: week_df['sub3_h'].sum()}

        cols = st.columns(3)
        for i, (name, val) in enumerate(sub_totals.items()):
            cols[i].markdown(f"<div class='subject-card'><span style='color: #555;'>විෂය:</span> {name}<br><span style='font-size: 1.5rem; color: #2196f3;'>{val:.1f} h</span></div>", unsafe_allow_html=True)
        
        st.markdown(f"### 📈 ප්‍රගති ප්‍රස්ථාරය ({start_date} සිට {end_date} දක්වා)")
        fig, ax = plt.subplots(figsize=(14, 6))
        dates = week_df['date'].astype(str).tolist()
        x = np.arange(len(dates))
        width = 0.25
        ax.bar(x - width, week_df['sub1_h'], width, label=sub_names[0], color='#2ecc71')
        ax.bar(x, week_df['sub2_h'], width, label=sub_names[1], color='#3498db')
        ax.bar(x + width, week_df['sub3_h'], width, label=sub_names[2], color='#e67e22')
        ax.set_xticks(x); ax.set_xticklabels(dates, rotation=45); ax.legend()
        st.pyplot(fig)
    else: st.warning(f"දත්ත නැත.")

# --- Main App Logic ---
if st.session_state.logged_in:
    st.markdown('<p class="main-title">🎓 A/L Study Tracker Pro</p>', unsafe_allow_html=True)
    st.markdown(f"<div style='text-align: center;'>Concept by: <b>Plan Master Charaka Dhananjaya</b> | Developed by: <span class='business-name'>Hiratrix IT Solutions</span></div>", unsafe_allow_html=True)
    st.divider()

    conn_db = sqlite3.connect('alevel_tracker_final.db')

    if st.session_state.username == "admin":
        st.header("👨‍🏫 ගුරු මණ්ඩල පුවරුව (Admin)")
        all_logs = pd.read_sql_query("SELECT * FROM study_logs", conn_db)
        if not all_logs.empty:
            all_logs['date'] = pd.to_datetime(all_logs['date']).dt.date
            selected_student = st.selectbox("ශිෂ්‍යයා තෝරන්න", all_logs['username'].unique())
            admin_date = st.date_input("සතියේ ආරම්භය", datetime.now() - timedelta(days=6))
            display_full_analytics(all_logs[all_logs['username'] == selected_student], admin_date)
            
            st.divider()
            if st.button(f"🗑️ {selected_student} ගේ සියලුම දත්ත මකන්න (Danger Area)"):
                conn_db.execute(f"DELETE FROM study_logs WHERE username='{selected_student}'")
                conn_db.commit()
                st.success("දත්ත මැකීම සාර්ථකයි.")
                st.rerun()

    else:
        tab1, tab2 = st.tabs(["📝 දත්ත ඇතුළත් කිරීම", "📊 පැරණි වාර්තා"])
        my_data = pd.read_sql_query(f"SELECT * FROM study_logs WHERE username='{st.session_state.username}'", conn_db)
        if not my_data.empty: my_data['date'] = pd.to_datetime(my_data['date']).dt.date

        with tab1:
            st.sidebar.subheader("📝 දත්ත ඇතුළත් කරන්න")
            entry_date = st.sidebar.date_input("දින තේරීම", datetime.now())
            stream = st.sidebar.selectbox("විෂය ධාරාව", list(SUBJECTS_DATA.keys()))
            names, hours = [], []
            for i in range(3):
                n = st.sidebar.selectbox(f"විෂය {i+1}", SUBJECTS_DATA[stream], key=f"n{i}", index=i)
                h = st.sidebar.number_input("Hours", 0, 20, key=f"h{i}")
                m = st.sidebar.number_input("Mins", 0, 59, key=f"m{i}")
                names.append(n); hours.append(h + (m/60))
            
            if st.sidebar.button("SAVE DATA"):
                conn_db.execute('''INSERT INTO study_logs VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(username, date) DO UPDATE SET sub1_h=excluded.sub1_h, sub2_h=excluded.sub2_h, sub3_h=excluded.sub3_h''', (st.session_state.username, str(entry_date), stream, names[0], hours[0], names[1], hours[1], names[2], hours[2]))
                conn_db.commit()
                st.rerun()
            
            # --- බොත්තම 1: අද දත්ත මකන්න ---
            st.sidebar.divider()
            if st.sidebar.button("🗑️ අද දත්ත මකන්න"):
                conn_db.execute(f"DELETE FROM study_logs WHERE username='{st.session_state.username}' AND date='{entry_date}'")
                conn_db.commit()
                st.rerun()
                
            # --- බොත්තම 2: සියලු දත්ත මකන්න ---
            if st.sidebar.button("🚨 සියලු දත්ත මකන්න"):
                conn_db.execute(f"DELETE FROM study_logs WHERE username='{st.session_state.username}'")
                conn_db.commit()
                st.rerun()

            st.markdown("### 📅 මෙම සතියේ සාරාංශය")
            main_date = st.date_input("සතිය ආරම්භ වන දිනය", datetime.now() - timedelta(days=6), key="main")
            if not my_data.empty: display_full_analytics(my_data, main_date)

        with tab2:
            st.header("🔍 පැරණි වාර්තා පරීක්ෂාව")
            old_date = st.date_input("සතිය ආරම්භ වන දිනය", datetime.now() - timedelta(days=14), key="old")
            if not my_data.empty: display_full_analytics(my_data, old_date)

    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()
    conn_db.close()
else:
    st.info("පද්ධතිය භාවිතා කිරීමට Login වන්න.")