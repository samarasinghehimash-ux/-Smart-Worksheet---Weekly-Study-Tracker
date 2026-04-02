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
        # Admin account
        admin_pass = hashlib.sha256(str.encode("admin123")).hexdigest()
        cursor.execute("INSERT OR IGNORE INTO users VALUES (?, ?)", ("admin", admin_pass))
        conn.commit()

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return make_hashes(password) == hashed_text

init_db()

# --- Page Config ---
st.set_page_config(page_title="A/L Study Tracker Pro", layout="wide")

# --- UI Styles (CSS) ---
st.markdown("""
    <style>
    .main-title { font-size: 3rem !important; font-weight: 900 !important; color: #ffffff; text-align: center; text-shadow: 2px 2px 4px #000; margin-bottom: 10px; }
    [data-testid="stMetricLabel"] p { color: #000000 !important; font-weight: 900 !important; font-size: 1.2rem !important; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-weight: bold !important; }
    div[data-testid="stMetric"] { background-color: #ffffff !important; padding: 15px; border-radius: 12px; border: 1px solid #ddd; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .subject-card { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 8px solid #2196f3; color: #000000 !important; margin-bottom: 10px; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .business-name { color: #2ecc71 !important; font-weight: bold; font-size: 1.2rem; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
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

# --- Sidebar: Login & Registration ---
st.sidebar.title("🔐 Access Control")
if not st.session_state.logged_in:
    auth_mode = st.sidebar.radio("තෝරන්න", ["Login (ඇතුළු වන්න)", "Register (අලුතින් එක්වන්න)"])
    
    u_in = st.sidebar.text_input("Username")
    p_in = st.sidebar.text_input("Password", type='password')
    
    if auth_mode == "Register (අලුතින් එක්වන්න)":
        if st.sidebar.button("ගිණුම සාදන්න"):
            if u_in and p_in:
                try:
                    with sqlite3.connect('alevel_tracker_final.db') as conn:
                        conn.execute("INSERT INTO users VALUES (?, ?)", (u_in, make_hashes(p_in)))
                        conn.commit()
                    st.sidebar.success("ගිණුම සාදා අවසන්! දැන් Login වන්න.")
                except sqlite3.IntegrityError:
                    st.sidebar.error("මෙම නම දැනටමත් පද්ධතියේ ඇත.")
            else: st.sidebar.warning("කරුණාකර විස්තර ඇතුළත් කරන්න.")
            
    else: # Login mode
        if st.sidebar.button("ඇතුළු වන්න"):
            with sqlite3.connect('alevel_tracker_final.db') as conn:
                data = conn.execute('SELECT password FROM users WHERE username =?', (u_in,)).fetchone()
                if data and check_hashes(p_in, data[0]):
                    st.session_state.logged_in, st.session_state.username = True, u_in
                    st.rerun()
                else: st.sidebar.error("Username හෝ Password වැරදියි.")
else:
    st.sidebar.success(f"පරිශීලක: {st.session_state.username}")
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

# --- Analytics Function ---
def display_full_analytics(df, start_date):
    end_date = start_date + timedelta(days=6)
    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
    week_df = df.loc[mask].sort_values('date')
    
    if not week_df.empty:
        total_h = week_df[['sub1_h', 'sub2_h', 'sub3_h']].sum().sum()
        
        if total_h < 40:
            st.markdown(f'<div style="background-color: #ffebee; color: #c62828; padding: 15px; border-radius: 12px; text-align: center; font-weight: bold; border: 2px solid #ef9a9a;">😟 ඔබ තවමත් දුර්වල මට්ටමක සිටින්නේ. තව ගොඩක් මහන්සි වෙන්න! (මුළු පැය: {total_h:.1f})</div>', unsafe_allow_html=True)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("📅 සතියේ මුළු පැය", f"{total_h:.1f} h")
        m2.metric("📊 දිනකට සාමාන්‍යය", f"{(total_h/7):.1f} h")
        m3.metric("✅ සටහන් කළ දින", f"{len(week_df)} / 7")
        
        st.divider()
        last_entry = week_df.iloc[-1]
        sub_names = [last_entry['sub1_name'], last_entry['sub2_name'], last_entry['sub3_name']]
        sub_totals = [week_df['sub1_h'].sum(), week_df['sub2_h'].sum(), week_df['sub3_h'].sum()]
        
        cols = st.columns(3)
        for i in range(3):
            cols[i].markdown(f"<div class='subject-card'><span style='color: #000;'>විෂය: {sub_names[i]}</span><br><span style='font-size: 1.5rem; color: #2196f3;'>{sub_totals[i]:.1f} h</span></div>", unsafe_allow_html=True)
        
        st.markdown(f"### 📈 ප්‍රගති ප්‍රස්ථාරය ({start_date} සිට {end_date} දක්වා)")
        fig, ax = plt.subplots(figsize=(12, 5))
        dates = week_df['date'].astype(str).tolist()
        x = np.arange(len(dates))
        width = 0.25
        ax.bar(x - width, week_df['sub1_h'], width, label=sub_names[0], color='#2ecc71')
        ax.bar(x, week_df['sub2_h'], width, label=sub_names[1], color='#3498db')
        ax.bar(x + width, week_df['sub3_h'], width, label=sub_names[2], color='#e67e22')
        ax.set_xticks(x); ax.set_xticklabels(dates, rotation=45); ax.legend()
        st.pyplot(fig)
    else: st.warning("දත්ත නැත.")

# --- Main App ---
if st.session_state.logged_in:
    st.markdown('<p class="main-title">🎓 A/L Smart Study Tracker Pro</p>', unsafe_allow_html=True)
    st.markdown("<div style='text-align: center;'>Concept by: <b>Plan Master Charaka Dhananjaya</b> | Developed by: <span class='business-name'>Hiratrix IT Solutions</span></div>", unsafe_allow_html=True)
    st.divider()

    conn = sqlite3.connect('alevel_tracker_final.db')

    if st.session_state.username == "admin":
        st.header("👨‍🏫 ගුරු මණ්ඩල පුවරුව")
        all_logs = pd.read_sql_query("SELECT * FROM study_logs", conn)
        if not all_logs.empty:
            all_logs['date'] = pd.to_datetime(all_logs['date']).dt.date
            sel_u = st.selectbox("ශිෂ්‍යයා තෝරන්න", all_logs['username'].unique())
            adm_d = st.date_input("සතියේ ආරම්භය", datetime.now() - timedelta(days=6))
            display_full_analytics(all_logs[all_logs['username'] == sel_u], adm_d)
    else:
        tab1, tab2 = st.tabs(["📝 දත්ත ඇතුළත් කිරීම", "📊 පැරණි වාර්තා"])
        my_data = pd.read_sql_query(f"SELECT * FROM study_logs WHERE username='{st.session_state.username}'", conn)
        if not my_data.empty: my_data['date'] = pd.to_datetime(my_data['date']).dt.date

        with tab1:
            st.sidebar.subheader("📝 දත්ත සටහන් කරන්න")
            e_date = st.sidebar.date_input("දිනය", datetime.now())
            stream = st.sidebar.selectbox("විෂය ධාරාව", list(SUBJECTS_DATA.keys()))
            names, hrs = [], []
            for i in range(3):
                st.sidebar.write(f"--- විෂය {i+1} ---")
                n = st.sidebar.selectbox(f"විෂය {i+1}", SUBJECTS_DATA[stream], key=f"n{i}", index=i)
                c1, c2 = st.sidebar.columns(2)
                h = c1.number_input("පැය", 0, 24, key=f"h{i}")
                m = c2.number_input("මිනිත්තු", 0, 59, key=f"m{i}")
                names.append(n); hrs.append(h + (m/60))
            
            if st.sidebar.button("දත්ත සුරකින්න (SAVE)"):
                conn.execute('INSERT INTO study_logs VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(username, date) DO UPDATE SET sub1_h=excluded.sub1_h, sub2_h=excluded.sub2_h, sub3_h=excluded.sub3_h', 
                             (st.session_state.username, str(e_date), stream, names[0], hrs[0], names[1], hrs[1], names[2], hrs[2]))
                conn.commit(); st.rerun()

            st.sidebar.divider()
            st.sidebar.subheader("🗑️ දත්ත කළමනාකරණය")
            if st.sidebar.button("🗑️ අද දත්ත මකන්න"):
                conn.execute(f"DELETE FROM study_logs WHERE username='{st.session_state.username}' AND date='{e_date}'")
                conn.commit(); st.rerun()
            if st.sidebar.button("🚨 සතියේ දත්ත මකන්න"):
                e_range = e_date + timedelta(days=6)
                conn.execute(f"DELETE FROM study_logs WHERE username='{st.session_state.username}' AND date BETWEEN '{e_date}' AND '{e_range}'")
                conn.commit(); st.rerun()
            if st.sidebar.button("🔥 සියලුම දත්ත මකන්න"):
                conn.execute(f"DELETE FROM study_logs WHERE username='{st.session_state.username}'")
                conn.commit(); st.rerun()

            st.markdown("### 📅 මෙම සතියේ සාරාංශය")
            m_date = st.date_input("සතිය ආරම්භ වන දිනය", datetime.now() - timedelta(days=6), key="m")
            if not my_data.empty: display_full_analytics(my_data, m_date)

        with tab2:
            st.header("🔍 පැරණි වාර්තා පරීක්ෂාව")
            o_date = st.date_input("සතිය ආරම්භ වන දිනය", datetime.now() - timedelta(days=14), key="o")
            if not my_data.empty: display_full_analytics(my_data, o_date)

    conn.close()
else:
    st.warning("⚠️ පද්ධතිය භාවිතා කිරීමට කරුණාකර Sidebar එක හරහා Login හෝ Register වන්න.")