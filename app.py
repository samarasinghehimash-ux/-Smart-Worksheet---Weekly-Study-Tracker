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

# --- Page Config ---
st.set_page_config(page_title="A/L Study Tracker Pro", layout="wide")

# --- UI Styles (එකම වර්ණය සහ පිරිසිදු පෙනුම) ---
st.markdown("""
    <style>
    /* Dark/Light දෙකටම ගැලපෙන සේ පසුබිම සහ අකුරු පාලනය */
    .main-title { font-size: 2.5rem !important; font-weight: 800 !important; text-align: center; margin-bottom: 5px; }
    .teacher-name { text-align: center; font-size: 1rem; margin-bottom: 25px; opacity: 0.8; }
    
    /* විෂය ප්‍රගති කොටු (Subject Cards) */
    .subject-card { 
        padding: 15px; 
        border-radius: 12px; 
        border: 1px solid #ddd;
        border-top: 5px solid #3498db; 
        text-align: center;
        margin-bottom: 10px;
    }
    .sub-value { font-size: 1.8rem; font-weight: 800; color: #3498db; }
    
    /* Metrics Fix */
    [data-testid="stMetric"] { border: 1px solid #ddd; padding: 10px; border-radius: 10px; }
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

# --- Sidebar (Settings & Calendar) ---
with st.sidebar:
    st.header("🔐 Access Control")
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
        st.write(f"User: **{st.session_state.username}**")
        if st.button("Log Out"):
            st.session_state.logged_in = False; st.rerun()
        
        st.divider()
        st.subheader("📅 දින දර්ශනය (Calendar)")
        # දින දර්ශනය මෙතැනින් තෝරන්න
        selected_date = st.date_input("සටහන් කිරීමට හෝ බැලීමට දිනය තෝරන්න", datetime.now())
        
        st.divider()
        st.subheader("⚙️ විෂය සැකසුම්")
        conn = sqlite3.connect('alevel_tracker_final.db')
        pref = conn.execute("SELECT * FROM user_prefs WHERE username=?", (st.session_state.username,)).fetchone()
        
        cur_stream = pref[1] if pref else "Commerce"
        stream = st.selectbox("විෂය ධාරාව", list(SUBJECTS_DATA.keys()), index=list(SUBJECTS_DATA.keys()).index(cur_stream))
        
        subs = []
        for i in range(1, 4):
            def_v = pref[i+1] if pref and pref[i+1] in SUBJECTS_DATA[stream] else SUBJECTS_DATA[stream][i-1]
            s = st.selectbox(f"විෂය {i}", SUBJECTS_DATA[stream], index=SUBJECTS_DATA[stream].index(def_v), key=f"cfg_{i}")
            subs.append(s)
            
        if st.button("Settings Save"):
            conn.execute("INSERT OR REPLACE INTO user_prefs VALUES (?,?,?,?,?)", (st.session_state.username, stream, subs[0], subs[1], subs[2]))
            conn.commit(); st.rerun()

# --- Main Page ---
if st.session_state.logged_in:
    st.markdown('<p class="main-title">🎓 A/L Study Tracker Pro</p>', unsafe_allow_html=True)
    st.markdown('<div class="teacher-name">Concept by: <b>Plan Master Charaka Dhananjaya</b> | Dev: Hiratrix IT Solutions</div>', unsafe_allow_html=True)
    
    # 1. Input Section
    st.subheader(f"📝 {selected_date} දත්ත ඇතුළත් කිරීම")
    cols = st.columns(3)
    hrs_in = []
    for i in range(3):
        with cols[i]:
            st.markdown(f"**{subs[i]}**")
            h = st.number_input("පැය", 0, 24, key=f"h_{i}")
            m = st.number_input("මිනිත්තු", 0, 59, key=f"m_{i}")
            hrs_in.append(h + (m/60))
            
    if st.button("දත්ත සුරකින්න (SAVE)"):
        conn.execute('INSERT INTO study_logs VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(username, date) DO UPDATE SET sub1_h=excluded.sub1_h, sub2_h=excluded.sub2_h, sub3_h=excluded.sub3_h', 
                     (st.session_state.username, str(selected_date), stream, subs[0], hrs_in[0], subs[1], hrs_in[1], subs[2], hrs_in[2]))
        conn.commit(); st.success(f"{selected_date} දත්ත සුරැකුණා!"); st.rerun()

    st.divider()

    # 2. Analytics Tabs (වර්තමාන සතිය සහ පැරණි දත්ත බැලීම)
    tab1, tab2 = st.tabs(["📊 තෝරාගත් සතියේ වාර්තාව", "🔍 ඉතිහාසය (History)"])

    def show_report(start_dt):
        df = pd.read_sql_query(f"SELECT * FROM study_logs WHERE username='{st.session_state.username}'", conn)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date']).dt.date
            week_df = df[(df['date'] >= start_dt) & (df['date'] <= start_dt + timedelta(days=6))].sort_values('date')
            
            if not week_df.empty:
                total_h = week_df[['sub1_h', 'sub2_h', 'sub3_h']].sum().sum()
                
                # Metrics
                m1, m2, m3 = st.columns(3)
                m1.metric("සතියේ මුළු පැය", f"{total_h:.1f} h")
                m2.metric("දිනක සාමාන්‍යය", f"{(total_h/7):.1f} h")
                m3.metric("සටහන් කළ දින", f"{len(week_df)}/7")
                
                # Subject Cards
                st.write("")
                sc = st.columns(3)
                for i in range(3):
                    val = week_df[f'sub{i+1}_h'].sum()
                    sc[i].markdown(f'<div class="subject-card"><p>{subs[i]}</p><p class="sub-value">{val:.1f} h</p></div>', unsafe_allow_html=True)

                # Grouped Bar Chart
                st.markdown("### 📈 ප්‍රගති ප්‍රස්ථාරය")
                fig, ax = plt.subplots(figsize=(12, 5))
                x = np.arange(len(week_df['date']))
                width = 0.25
                ax.bar(x - width, week_df['sub1_h'], width, label=subs[0], color='#2ecc71')
                ax.bar(x, week_df['sub2_h'], width, label=subs[1], color='#3498db')
                ax.bar(x + width, week_df['sub3_h'], width, label=subs[2], color='#f1c40f')
                ax.set_xticks(x)
                ax.set_xticklabels(week_df['date'].astype(str), rotation=30)
                ax.legend(); st.pyplot(fig)
            else: st.info("මෙම කාලසීමාවට දත්ත නොමැත.")
        else: st.warning("දත්ත කිසිවක් නැත.")

    with tab1:
        # තෝරාගත් දිනට අදාළ සතියේ ආරම්භය (සදුදා)
        monday = selected_date - timedelta(days=selected_date.weekday())
        st.info(f"ප්‍රගතිය පෙන්වන්නේ: {monday} සිට {monday + timedelta(days=6)} දක්වා")
        show_report(monday)

    with tab2:
        st.subheader("🔍 පැරණි වාර්තා පරීක්ෂා කිරීම")
        h_date = st.date_input("ආරම්භක දිනය තෝරන්න", monday - timedelta(days=7), key="history_cal")
        if st.button("වාර්තාව පෙන්වන්න"):
            show_report(h_date)

    conn.close()