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

# --- UI Styles (CSS) ---
st.markdown("""
    <style>
    .main-title { font-size: 3rem !important; font-weight: 900 !important; color: #ffffff; text-align: center; text-shadow: 2px 2px 4px #000; margin-bottom: 10px; }
    [data-testid="stMetricLabel"] p { color: #000000 !important; font-weight: 900 !important; font-size: 1.2rem !important; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-weight: bold !important; }
    div[data-testid="stMetric"] { background-color: #ffffff !important; padding: 15px; border-radius: 12px; border: 1px solid #ddd; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .business-name { color: #2ecc71 !important; font-weight: bold; font-size: 1.2rem; }
    .feedback-box { padding: 15px; border-radius: 12px; text-align: center; font-size: 1.2rem; font-weight: bold; margin-bottom: 35px; border: 2px solid; }
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

# --- Access Control ---
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
                    conn.commit()
                    st.sidebar.success("සාර්ථකයි! දැන් Login වන්න.")
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
        st.session_state.logged_in = False
        st.rerun()

# --- Analytics Function (Including Graph) ---
def display_full_analytics(df, start_date):
    end_date = start_date + timedelta(days=6)
    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
    week_df = df.loc[mask].sort_values('date')
    
    if not week_df.empty:
        total_h = week_df[['sub1_h', 'sub2_h', 'sub3_h']].sum().sum()
        
        # Feedback Box
        if total_h < 40:
            st.markdown(f'<div class="feedback-box" style="background-color: #ffebee; color: #c62828; border-color: #ef9a9a;">😟 ඔබ තවමත් දුර්වල මට්ටමක සිටින්නේ. තව ගොඩක් මහන්සි වෙන්න! (මුළු පැය: {total_h:.1f})</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="feedback-box" style="background-color: #e8f5e9; color: #2e7d32; border-color: #a5d6a7;">🎉 නියමයි! හොඳ ප්‍රගතියක් පවතිනවා. (මුළු පැය: {total_h:.1f})</div>', unsafe_allow_html=True)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("📅 සතියේ මුළු පැය", f"{total_h:.1f} h")
        m2.metric("📊 දිනකට සාමාන්‍යය", f"{(total_h/7):.1f} h")
        m3.metric("✅ සටහන් කළ දින", f"{len(week_df)} / 7")
        
        # ප්‍රස්ථාරය ඇඳීම (The Graph)
        st.markdown(f"### 📈 ප්‍රගති ප්‍රස්ථාරය ({start_date} සිට {end_date} දක්වා)")
        fig, ax = plt.subplots(figsize=(12, 5))
        dates = week_df['date'].astype(str).tolist()
        x = np.arange(len(dates))
        width = 0.25
        
        ax.bar(x - width, week_df['sub1_h'], width, label=week_df['sub1_name'].iloc[0], color='#2ecc71')
        ax.bar(x, week_df['sub2_h'], width, label=week_df['sub2_name'].iloc[0], color='#3498db')
        ax.bar(x + width, week_df['sub3_h'], width, label=week_df['sub3_name'].iloc[0], color='#e67e22')
        
        ax.set_ylabel('පැය ගණන'); ax.set_xticks(x); ax.set_xticklabels(dates, rotation=45); ax.legend()
        st.pyplot(fig)
    else:
        st.info("තෝරාගත් කාලසීමාව සඳහා දත්ත ඇතුළත් කර නැත.")

# --- Main App ---
if st.session_state.logged_in:
    st.markdown('<p class="main-title">🎓 A/L Smart Study Tracker Pro</p>', unsafe_allow_html=True)
    st.markdown("<div style='text-align: center;'>Concept by: <b>Plan Master Charaka Dhananjaya</b> | Developed by: <span class='business-name'>Hiratrix IT Solutions</span></div>", unsafe_allow_html=True)
    st.divider()

    conn = sqlite3.connect('alevel_tracker_final.db')
    tab1, tab2 = st.tabs(["📝 දත්ත ඇතුළත් කිරීම", "📊 පැරණි වාර්තා"])

    with tab1:
        st.sidebar.subheader("📝 අද දින දත්ත")
        e_date = st.sidebar.date_input("දිනය", datetime.now())
        stream = st.sidebar.selectbox("විෂය ධාරාව", list(SUBJECTS_DATA.keys()), key="user_stream_fix")
        
        names, hrs = [], []
        for i in range(1, 4):
            st.sidebar.write(f"--- විෂය {i} ---")
            n = st.sidebar.selectbox(f"තෝරන්න {i}", SUBJECTS_DATA[stream], key=f"sub_fix_{i}")
            c1, c2 = st.sidebar.columns(2)
            h = c1.number_input("පැය", 0, 24, key=f"h_fix_{i}")
            m = c2.number_input("මිනිත්තු", 0, 59, key=f"m_fix_{i}")
            names.append(n); hrs.append(h + (m/60))

        if st.sidebar.button("දත්ත සුරකින්න (SAVE)"):
            with sqlite3.connect('alevel_tracker_final.db') as db_conn:
                db_conn.execute('INSERT INTO study_logs VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(username, date) DO UPDATE SET sub1_h=excluded.sub1_h, sub2_h=excluded.sub2_h, sub3_h=excluded.sub3_h', 
                             (st.session_state.username, str(e_date), stream, names[0], hrs[0], names[1], hrs[1], names[2], hrs[2]))
                db_conn.commit()
            
            # Reset only hours and minutes
            for i in range(1, 4):
                st.session_state[f"h_fix_{i}"] = 0
                st.session_state[f"m_fix_{i}"] = 0
            st.rerun()

        # Display Analytics and Graph
        my_data = pd.read_sql_query(f"SELECT * FROM study_logs WHERE username='{st.session_state.username}'", conn)
        if not my_data.empty:
            my_data['date'] = pd.to_datetime(my_data['date']).dt.date
            m_date = st.date_input("සතිය ආරම්භ වන දිනය", datetime.now() - timedelta(days=6), key="week_start_fix")
            display_full_analytics(my_data, m_date)

    conn.close()
else:
    st.warning("Sidebar එකෙන් Login වන්න.")