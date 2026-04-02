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
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_prefs 
                          (username TEXT PRIMARY KEY, stream TEXT, sub1 TEXT, sub2 TEXT, sub3 TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS study_logs 
                          (username TEXT, date TEXT, stream TEXT, 
                           sub1_name TEXT, sub1_h REAL, 
                           sub2_name TEXT, sub2_h REAL, 
                           sub3_name TEXT, sub3_h REAL, UNIQUE(username, date))''')
        conn.commit()

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return make_hashes(password) == hashed_text

init_db()

# --- Page Config (Force Light Theme) ---
st.set_page_config(page_title="A/L Study Tracker Pro", layout="wide", initial_sidebar_state="expanded")

# --- UI Styles (එකම සුදු පැහැය සහ Calendar එක සකස් කිරීම) ---
st.markdown("""
    <style>
    /* මුළු App එකම සහ Sidebar එකම සුදු පැහැයට හැරවීම */
    [data-testid="stAppViewContainer"], [data-testid="stSidebar"], .stApp {
        background-color: #FFFFFF !important;
    }
    
    /* Sidebar අකුරු කළු කිරීම */
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label, [data-testid="stSidebar"] p {
        color: #000000 !important;
        font-weight: bold;
    }

    /* මාතෘකා සැකසුම් */
    .main-title { font-size: 2.5rem !important; font-weight: 800 !important; color: #1e272e; text-align: center; }
    .teacher-name { text-align: center; font-size: 0.9rem; color: #485460; margin-bottom: 30px; }

    /* දත්ත කොටු (Metrics) */
    [data-testid="stMetric"] {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #dfe6e9;
    }

    /* විෂය ප්‍රගති කොටු (Subject Cards) */
    .sub-card {
        background: #ffffff;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #eee;
        border-bottom: 5px solid #0984e3;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        text-align: center;
    }
    .sub-h { color: #0984e3; font-size: 2rem; font-weight: 800; }
    
    /* Calendar (Date Input) එකේ පෙනුම */
    .stDateInput div[data-baseweb="input"] {
        background-color: #f1f2f6 !important;
        border: 1px solid #ced4da !important;
    }
    </style>
    """, unsafe_allow_html=True)

SUBJECTS_DATA = {
    "Commerce": ["Accounting", "Business Studies", "Economics", "ICT"],
    "Physical Science (Maths)": ["Combined Maths", "Physics", "Chemistry", "ICT"],
    "Biological Science (Bio)": ["Biology", "Chemistry", "Physics", "Agricultural Science"],
    "Arts": ["Sinhala", "History", "Logic", "Political Science", "Geography", "Economics", "ICT"],
    "Technology": ["SFT", "Engineering Tech", "Bio Systems Tech", "ICT"]
}

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- Sidebar Logic ---
with st.sidebar:
    st.markdown("### 🔐 Access Control")
    if not st.session_state.logged_in:
        u_in = st.text_input("Username")
        p_in = st.text_input("Password", type='password')
        if st.button("Login"):
            with sqlite3.connect('alevel_tracker_final.db') as conn:
                data = conn.execute('SELECT password FROM users WHERE username =?', (u_in,)).fetchone()
                if data and check_hashes(p_in, data[0]):
                    st.session_state.logged_in, st.session_state.username = True, u_in
                    st.rerun()
                else: st.error("වැරදියි!")
    else:
        st.write(f"Logged in as: **{st.session_state.username}**")
        if st.button("Log Out"):
            st.session_state.logged_in = False; st.rerun()

    if st.session_state.logged_in:
        st.divider()
        # --- Calendar Feature ---
        st.markdown("### 📅 දින දර්ශනය")
        selected_date = st.date_input("සටහන් කළ යුතු දිනය තෝරන්න", datetime.now())
        
        st.divider()
        st.markdown("### ⚙️ විෂය සැකසුම්")
        conn = sqlite3.connect('alevel_tracker_final.db')
        pref = conn.execute("SELECT * FROM user_prefs WHERE username=?", (st.session_state.username,)).fetchone()
        
        cur_stream = pref[1] if pref else "Commerce"
        stream = st.selectbox("විෂය ධාරාව", list(SUBJECTS_DATA.keys()), index=list(SUBJECTS_DATA.keys()).index(cur_stream))
        
        subs = []
        for i in range(1, 4):
            def_val = pref[i+1] if pref and pref[i+1] in SUBJECTS_DATA[stream] else SUBJECTS_DATA[stream][i-1]
            s = st.selectbox(f"විෂය {i}", SUBJECTS_DATA[stream], index=SUBJECTS_DATA[stream].index(def_val), key=f"s_{i}")
            subs.append(s)
            
        if st.button("සැකසුම් ස්ථිර කරන්න"):
            conn.execute("INSERT OR REPLACE INTO user_prefs VALUES (?,?,?,?,?)", (st.session_state.username, stream, subs[0], subs[1], subs[2]))
            conn.commit(); st.rerun()

# --- Main Page ---
if st.session_state.logged_in:
    st.markdown('<p class="main-title">🎓 A/L Smart Study Tracker Pro</p>', unsafe_allow_html=True)
    st.markdown('<div class="teacher-name">Concept by: <b>Plan Master Charaka Dhananjaya</b> | Developed by: <span style="color:#27ae60; font-weight:bold;">Hiratrix IT Solutions</span></div>', unsafe_allow_html=True)
    
    # --- Input Section ---
    st.subheader(f"📍 {selected_date} දින දත්ත ඇතුළත් කිරීම")
    c1, c2, c3 = st.columns(3)
    hrs_in = []
    for i in range(3):
        with [c1, c2, c3][i]:
            st.markdown(f"**{subs[i]}**")
            h = st.number_input("පැය", 0, 24, key=f"h_in_{i}")
            m = st.number_input("මිනිත්තු", 0, 59, key=f"m_in_{i}")
            hrs_in.append(h + (m/60))
            
    if st.button("දත්ත සුරකින්න (SAVE DATA)"):
        conn.execute('INSERT INTO study_logs VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(username, date) DO UPDATE SET sub1_h=excluded.sub1_h, sub2_h=excluded.sub2_h, sub3_h=excluded.sub3_h', 
                     (st.session_state.username, str(selected_date), stream, subs[0], hrs_in[0], subs[1], hrs_in[1], subs[2], hrs_in[2]))
        conn.commit(); st.success(f"{selected_date} දත්ත සුරැකුණා!")

    st.divider()

    # --- Weekly Analytics ---
    st.subheader("📊 සතිපතා ප්‍රගති වාර්තාව")
    start_week = selected_date - timedelta(days=selected_date.weekday())
    df = pd.read_sql_query(f"SELECT * FROM study_logs WHERE username='{st.session_state.username}'", conn)
    
    if not df.empty:
        df['date'] = pd.to_datetime(df['date']).dt.date
        week_df = df[(df['date'] >= start_week) & (df['date'] <= start_week + timedelta(days=6))].sort_values('date')
        
        if not week_df.empty:
            total = week_df[['sub1_h', 'sub2_h', 'sub3_h']].sum().sum()
            
            # කොටු 3 (Metrics)
            m1, m2, m3 = st.columns(3)
            m1.metric("📅 සතියේ මුළු පැය", f"{total:.1f} h")
            m2.metric("📊 දිනක සාමාන්‍යය", f"{(total/7):.1f} h")
            m3.metric("✅ වාර්තා කළ දින", f"{len(week_df)}/7")
            
            # විෂය කාඩ්පත්
            st.markdown("### 📚 විෂයන් අනුව ප්‍රගතිය")
            sc1, sc2, sc3 = st.columns(3)
            for i in range(3):
                val = week_df[f'sub{i+1}_h'].sum()
                [sc1, sc2, sc3][i].markdown(f'<div class="sub-card"><p>{subs[i]}</p><p class="sub-h">{val:.1f} h</p></div>', unsafe_allow_html=True)

            # Grouped Bar Chart (දිනකට තීරු 3)
            st.markdown("### 📈 ප්‍රගති ප්‍රස්ථාරය")
            fig, ax = plt.subplots(figsize=(12, 5))
            x_idx = np.arange(len(week_df['date']))
            bar_w = 0.25
            
            ax.bar(x_idx - bar_w, week_df['sub1_h'], bar_w, label=subs[0], color='#2ecc71')
            ax.bar(x_idx, week_df['sub2_h'], bar_w, label=subs[1], color='#3498db')
            ax.bar(x_idx + bar_w, week_df['sub3_h'], bar_w, label=subs[2], color='#f1c40f')
            
            ax.set_xticks(x_idx)
            ax.set_xticklabels(week_df['date'].astype(str), rotation=35)
            ax.legend()
            st.pyplot(fig)
        else: st.info("තෝරාගත් සතියේ දත්ත නොමැත.")
    else: st.warning("දත්ත ඇතුළත් කර නැත.")
    conn.close()