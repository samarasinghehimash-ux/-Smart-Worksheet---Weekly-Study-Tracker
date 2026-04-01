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
        conn.commit()

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return make_hashes(password) == hashed_text

init_db()

# --- Page Config ---
st.set_page_config(page_title="A/L Study Tracker Pro", layout="wide")

# --- UI Styles ---
st.markdown("""
    <style>
    /* මාතෘකාව කැපී පෙනෙන ලෙස සැකසීම */
    .main-title {
        font-size: 3rem !important;
        font-weight: 800 !important;
        color: #ffffff;
        text-align: center;
        text-shadow: 2px 2px 4px #000000;
        margin-bottom: 5px;
    }
    /* Metrics වර්ණ ගැන්වීම */
    [data-testid="stMetricValue"] { color: #000000 !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] p { color: #000000 !important; font-weight: bold !important; font-size: 1.1rem !important; }
    div[data-testid="stMetric"] { background-color: #ffffff !important; padding: 20px; border-radius: 12px; border: 1px solid #dddddd; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    /* විෂය කාඩ්පත් */
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

# --- Sidebar Login ---
st.sidebar.title("🔐 Access Control")
auth_mode = st.sidebar.selectbox("තෝරන්න", ["Login", "Sign Up"])

if auth_mode == "Sign Up":
    new_user = st.sidebar.text_input("Username")
    new_password = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("ගිණුම සාදන්න"):
        with sqlite3.connect('alevel_tracker_final.db') as conn:
            try:
                conn.execute('INSERT INTO users VALUES (?,?)', (new_user, make_hashes(new_password)))
                conn.commit()
                st.sidebar.success("සාර්ථකයි! දැන් Login වන්න.")
            except: st.sidebar.error("මෙම නම දැනටමත් පවතී.")
elif auth_mode == "Login":
    u_in = st.sidebar.text_input("Username")
    p_in = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("ඇතුළු වන්න"):
        with sqlite3.connect('alevel_tracker_final.db') as conn:
            data = conn.execute('SELECT password FROM users WHERE username =?', (u_in,)).fetchone()
            if data and check_hashes(p_in, data[0]):
                st.session_state.logged_in, st.session_state.username = True, u_in
                st.rerun()
            else: st.sidebar.error("නම හෝ මුරපදය වැරදියි.")

# --- UI Functions ---
def display_report(df, start_date):
    end_date = start_date + timedelta(days=6)
    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
    week_df = df.loc[mask].sort_values('date')

    if not week_df.empty:
        # 1. Metrics Boxes
        total_h = week_df[['sub1_h', 'sub2_h', 'sub3_h']].sum().sum()
        m1, m2, m3 = st.columns(3)
        m1.metric("සතියේ මුළු පැය", f"{total_h:.1f} h")
        m2.metric("දිනකට සාමාන්‍යය", f"{(total_h/7):.1f} h")
        m3.metric("සටහන් කළ දින", f"{len(week_df)} / 7")

        st.write("---")
        
        # 2. Subject Cards
        last_entry = week_df.iloc[-1]
        names = [last_entry['sub1_name'], last_entry['sub2_name'], last_entry['sub3_name']]
        totals = [week_df['sub1_h'].sum(), week_df['sub2_h'].sum(), week_df['sub3_h'].sum()]
        
        c1, c2, c3 = st.columns(3)
        for i, col in enumerate([c1, c2, c3]):
            col.markdown(f"<div class='subject-card'>{names[i]}<br>මුළු කාලය: {totals[i]:.1f} h</div>", unsafe_allow_html=True)

        # 3. Graph
        st.markdown("### 📊 සතිපතා ප්‍රස්ථාරය")
        fig, ax = plt.subplots(figsize=(10, 4))
        week_df.plot(kind='bar', x='date', ax=ax, color=['#2ecc71', '#3498db', '#e67e22'])
        ax.legend(names)
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.warning(f"{start_date} සිට {end_date} දක්වා කාලයට දත්ත හමු නොවීය.")

# --- Main Logic ---
if st.session_state.logged_in:
    st.markdown('<p class="main-title">🎓 A/L Smart Study Tracker Pro</p>', unsafe_allow_html=True)
    st.markdown(f"<div style='text-align: center;'>Concept by: <b>Plan Master Charaka Dhananjaya</b> | Developed by: <span class='business-name'>Hiratrix IT Solutions</span></div>", unsafe_allow_html=True)
    st.divider()

    tab1, tab2 = st.tabs(["📝 අද දත්ත ඇතුළත් කිරීම", "📊 පැරණි වාර්තා පරීක්ෂාව"])

    with sqlite3.connect('alevel_tracker_final.db') as conn:
        all_data = pd.read_sql_query(f"SELECT * FROM study_logs WHERE username = '{st.session_state.username}'", conn)
    if not all_data.empty:
        all_data['date'] = pd.to_datetime(all_data['date']).dt.date

    with tab1:
        st.subheader(f"👋 සාදරයෙන් පිළිගනිමු, {st.session_state.username.capitalize()}!")
        
        # Sidebar Entry
        st.sidebar.subheader("📝 දත්ත ඇතුළත් කරන්න")
        entry_date = st.sidebar.date_input("අද දිනය", datetime.now(), key="entry_d")
        stream_choice = st.sidebar.selectbox("විෂය ධාරාව", list(SUBJECTS_DATA.keys()))
        
        s_names, s_hours = [], []
        for i in range(3):
            st.sidebar.write(f"--- විෂය {i+1} ---")
            name = st.sidebar.selectbox(f"තෝරන්න {i+1}", SUBJECTS_DATA[stream_choice], key=f"n{i}", index=i)
            c_h, c_m = st.sidebar.columns(2)
            h = c_h.number_input("Hours", 0, 20, key=f"h{i}") # Max 20 hours limit
            m = c_m.number_input("Mins", 0, 59, key=f"m{i}")
            s_names.append(name); s_hours.append(h + (m/60))

        if st.sidebar.button("SAVE DATA", use_container_width=True):
            with sqlite3.connect('alevel_tracker_final.db') as conn:
                conn.execute('''INSERT INTO study_logs VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(username, date) DO UPDATE SET 
                              sub1_h=excluded.sub1_h, sub2_h=excluded.sub2_h, sub3_h=excluded.sub3_h''', 
                           (st.session_state.username, str(entry_date), stream_choice, s_names[0], s_hours[0], s_names[1], s_hours[1], s_names[2], s_hours[2]))
            st.success("දත්ත සුරැකුණා! ප්‍රස්ථාරය බැලීමට පිටුව Refresh කරන්න.")
            st.rerun()

        st.markdown("### 📅 මෙම සතියේ සාරාංශය")
        main_start = st.date_input("මෙම සතිය ආරම්භය", datetime.now() - timedelta(days=6), key="main_c")
        if not all_data.empty:
            display_report(all_data, main_start)

    with tab2:
        st.header("🔍 පැරණි වාර්තා පරීක්ෂාව")
        st.write("පැරණි දත්ත බැලීමට සතියේ ආරම්භක දිනය තෝරන්න.")
        old_start = st.date_input("වාර්තාව අවශ්‍ය දිනය", datetime.now() - timedelta(days=14), key="old_c")
        st.divider()
        if not all_data.empty:
            display_report(all_data, old_start)
        else:
            st.info("දත්ත කිසිවක් නැත.")

    st.sidebar.divider()
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()
else:
    st.info("ඉදිරියට යාමට Login වන්න.")