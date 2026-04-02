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
                          (username TEXT, date TEXT, stream TEXT, 
                           sub1_name TEXT, sub1_h REAL, 
                           sub2_name TEXT, sub2_h REAL, 
                           sub3_name TEXT, sub3_h REAL, UNIQUE(username, date))''')
        # Admin account
        admin_pass = hashlib.sha256(str.encode("admin123")).hexdigest()
        cursor.execute("INSERT OR IGNORE INTO users VALUES (?, ?)", ("admin", admin_pass))
        conn.commit()

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return make_hashes(password) == hashed_text

init_db()

# --- Page Config ---
st.set_page_config(page_title="A/L Smart Study Tracker Pro", layout="wide")

# --- UI Styles (CSS) ---
st.markdown("""
    <style>
    .main-title { font-size: 3rem !important; font-weight: 900 !important; color: #ffffff; text-align: center; text-shadow: 2px 2px 4px #000; margin-bottom: 10px; }
    [data-testid="stMetricLabel"] p { color: #000000 !important; font-weight: 900 !important; font-size: 1.2rem !important; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-weight: bold !important; }
    div[data-testid="stMetric"] { background-color: #ffffff !important; padding: 15px; border-radius: 12px; border: 1px solid #ddd; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .business-name { color: #2ecc71 !important; font-weight: bold; font-size: 1.2rem; }
    .feedback-box { padding: 15px; border-radius: 12px; text-align: center; font-size: 1.3rem; font-weight: bold; margin-top: 20px; margin-bottom: 50px; border: 2px solid; }
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

# --- Sidebar Login/Register ---
st.sidebar.title("🔐 Access Control")
if not st.session_state.logged_in:
    auth_mode = st.sidebar.radio("තෝරන්න", ["Login", "Register"])
    u_in = st.sidebar.text_input("Username")
    p_in = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("ඇතුළු වන්න"):
        with sqlite3.connect('alevel_tracker_final.db') as conn:
            if auth_mode == "Register":
                try:
                    conn.execute("INSERT INTO users VALUES (?, ?)", (u_in, make_hashes(p_in)))
                    conn.commit(); st.sidebar.success("දැන් Login වන්න.")
                except: st.sidebar.error("නම දැනටමත් ඇත.")
            else:
                data = conn.execute('SELECT password FROM users WHERE username =?', (u_in,)).fetchone()
                if data and check_hashes(p_in, data[0]):
                    st.session_state.logged_in, st.session_state.username = True, u_in
                    st.rerun()
                else: st.sidebar.error("දත්ත වැරදියි.")
else:
    st.sidebar.success(f"පරිශීලක: {st.session_state.username}")
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False; st.rerun()

# --- Analytics & Graph Function ---
def display_full_analytics(df, start_date):
    end_date = start_date + timedelta(days=6)
    # දින වකවානු හරියටම Filter කිරීම
    df['date'] = pd.to_datetime(df['date']).dt.date
    week_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)].sort_values('date')
    
    if not week_df.empty:
        total_h = week_df[['sub1_h', 'sub2_h', 'sub3_h']].sum().sum()
        
        # Feedback Box with spacing
        if total_h < 40:
            st.markdown(f'<div class="feedback-box" style="background-color: #ffebee; color: #c62828; border-color: #ef9a9a;">😟 ඔබ තවමත් දුර්වල මට්ටමක සිටින්නේ. තව ගොඩක් මහන්සි වෙන්න! (සතිපතා පැය: {total_h:.1f})</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="feedback-box" style="background-color: #e8f5e9; color: #2e7d32; border-color: #a5d6a7;">🎉 නියමයි! හොඳ ප්‍රගතියක් පවතිනවා. (සතිපතා පැය: {total_h:.1f})</div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("📅 සතියේ මුළු පැය", f"{total_h:.1f} h")
        c2.metric("📊 දිනකට සාමාන්‍යය", f"{(total_h/7):.1f} h")
        c3.metric("✅ සටහන් කළ දින", f"{len(week_df)} / 7")
        
        st.markdown("### 📈 ප්‍රගති ප්‍රස්ථාරය")
        fig, ax = plt.subplots(figsize=(12, 5))
        dates_str = [d.strftime('%m/%d') for d in week_df['date']]
        x = np.arange(len(dates_str))
        width = 0.25
        
        ax.bar(x - width, week_df['sub1_h'], width, label=week_df['sub1_name'].iloc[0], color='#2ecc71')
        ax.bar(x, week_df['sub2_h'], width, label=week_df['sub2_name'].iloc[0], color='#3498db')
        ax.bar(x + width, week_df['sub3_h'], width, label=week_df['sub3_name'].iloc[0], color='#e67e22')
        
        ax.set_xticks(x); ax.set_xticklabels(dates_str); ax.legend(); st.pyplot(fig)
    else:
        st.info("මෙම සතිය සඳහා දත්ත ඇතුළත් කර නැත.")

# --- Main App ---
if st.session_state.logged_in:
    st.markdown('<p class="main-title">🎓 A/L Smart Study Tracker Pro</p>', unsafe_allow_html=True)
    st.markdown("<div style='text-align: center;'>Concept by: <b>Plan Master Charaka Dhananjaya</b> | Developed by: <span class='business-name'>Hiratrix IT Solutions</span></div>", unsafe_allow_html=True)
    st.divider()

    conn = sqlite3.connect('alevel_tracker_final.db')
    tab1, tab2 = st.tabs(["📝 දත්ත ඇතුළත් කිරීම", "📊 පැරණි වාර්තා පරීක්ෂාව"])

    with tab1:
        st.sidebar.subheader("📝 දත්ත සටහන")
        sel_date = st.sidebar.date_input("දිනය", datetime.now())
        # විෂය ධාරාව ස්ථිරව තබා ගැනීම
        u_stream = st.sidebar.selectbox("විෂය ධාරාව", list(SUBJECTS_DATA.keys()), key="persist_stream")
        
        names, hrs = [], []
        for i in range(1, 4):
            st.sidebar.write(f"--- විෂය {i} ---")
            sn = st.sidebar.selectbox(f"විෂය {i}", SUBJECTS_DATA[u_stream], key=f"persist_sub_{i}")
            col1, col2 = st.sidebar.columns(2)
            # පැය/මිනිත්තු Reset කිරීමට key අත්‍යවශ්‍යයි
            hh = col1.number_input("පැය", 0, 24, key=f"reset_h_{i}")
            mm = col2.number_input("මිනිත්තු", 0, 59, key=f"reset_m_{i}")
            names.append(sn); hrs.append(hh + (mm/60))
        
        if st.sidebar.button("දත්ත සුරකින්න (SAVE)"):
            with sqlite3.connect('alevel_tracker_final.db') as db:
                db.execute('INSERT INTO study_logs VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(username, date) DO UPDATE SET sub1_h=excluded.sub1_h, sub2_h=excluded.sub2_h, sub3_h=excluded.sub3_h', 
                           (st.session_state.username, str(sel_date), u_stream, names[0], hrs[0], names[1], hrs[1], names[2], hrs[2]))
                db.commit()
            # Reset inputs logic
            for i in range(1, 4):
                st.session_state[f"reset_h_{i}"] = 0
                st.session_state[f"reset_m_{i}"] = 0
            st.rerun()

        # අදාල සතියේ සාරාංශය පෙන්වීම
        st.subheader("📅 මෙම සතියේ ප්‍රගතිය")
        week_start = st.date_input("සතිය ආරම්භ වන දිනය", datetime.now() - timedelta(days=datetime.now().weekday()), key="current_week_picker")
        all_data = pd.read_sql_query(f"SELECT * FROM study_logs WHERE username='{st.session_state.username}'", conn)
        display_full_analytics(all_data, week_start)

        st.sidebar.divider()
        st.sidebar.subheader("🗑️ දත්ත කළමනාකරණය")
        if st.sidebar.button("අද දත්ත මකන්න"):
            conn.execute(f"DELETE FROM study_logs WHERE username='{st.session_state.username}' AND date='{sel_date}'")
            conn.commit(); st.rerun()
        if st.sidebar.button("සතියේ දත්ත මකන්න"):
            d2 = week_start + timedelta(days=6)
            conn.execute(f"DELETE FROM study_logs WHERE username='{st.session_state.username}' AND date BETWEEN '{week_start}' AND '{d2}'")
            conn.commit(); st.rerun()

    with tab2:
        st.subheader("🔍 පැරණි වාර්තා සෙවීම")
        search_date = st.date_input("සතියේ ආරම්භය තෝරන්න", datetime.now() - timedelta(days=7), key="history_picker")
        if not all_data.empty:
            display_full_analytics(all_data, search_date)
        else:
            st.warning("තවමත් කිසිදු දත්තයක් පද්ධතියට ඇතුළත් කර නැත.")

    conn.close()
else:
    st.info("Sidebar එක භාවිතා කර Login වන්න.")