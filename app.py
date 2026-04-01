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
    [data-testid="stMetricValue"] { color: #000000 !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] p { color: #000000 !important; font-weight: bold !important; font-size: 1.1rem !important; }
    div[data-testid="stMetric"] { background-color: #ffffff !important; padding: 20px; border-radius: 12px; border: 1px solid #dddddd; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .subject-card { background-color: #f0f7ff; padding: 15px; border-radius: 10px; border-left: 5px solid #2196f3; color: #000000 !important; margin-bottom: 10px; font-weight: bold; }
    .business-name { color: #2ecc71; font-weight: bold; font-size: 1.2rem; }
    .welcome-header { font-size: 1.8rem; font-weight: bold; color: #2c3e50; }
    </style>
    """, unsafe_allow_html=True)

# --- Subject Configuration ---
SUBJECTS_DATA = {
    "Physical Science (Maths)": ["Combined Maths", "Physics", "Chemistry", "ICT"],
    "Biological Science (Bio)": ["Biology", "Chemistry", "Physics", "Agricultural Science"],
    "Commerce": ["Accounting", "Business Studies", "Economics", "ICT"],
    "Arts": ["Sinhala", "History", "Logic", "Political Science", "Geography", "Economics", "ICT"],
    "Technology": ["SFT", "Engineering Tech", "Bio Systems Tech", "ICT"]
}

# --- Session State for Login ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- Sidebar Access Control ---
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

# --- Main App ---
if st.session_state.logged_in:
    # Header Section
    st.markdown(f"<div class='welcome-header'>🎓 A/L Smart Study Tracker Pro</div>", unsafe_allow_html=True)
    st.markdown(f"Concept by: **Plan Master Charaka Dhananjaya** | Developed by: <span class='business-name'>Hiratrix IT Solutions</span>", unsafe_allow_html=True)
    st.divider()

    tab1, tab2 = st.tabs(["📝 අද දත්ත ඇතුළත් කිරීම", "📊 පැරණි වාර්තා පරීක්ෂාව"])

    with tab1:
        st.subheader(f"👋 සාදරයෙන් පිළිගනිමු, {st.session_state.username.capitalize()}!")
        
        # Sidebar Data Entry
        st.sidebar.subheader("📝 දත්ත ඇතුළත් කරන්න")
        entry_date = st.sidebar.date_input("දත්ත ඇතුළත් කරන දිනය", datetime.now())
        stream_choice = st.sidebar.selectbox("විෂය ධාරාව", list(SUBJECTS_DATA.keys()))
        available_subjects = SUBJECTS_DATA[stream_choice]

        s_names, s_hours = [], []
        for i in range(3):
            st.sidebar.write(f"--- විෂය {i+1} ---")
            name = st.sidebar.selectbox(f"තෝරන්න {i+1}", available_subjects, key=f"n{i}", index=i if i < len(available_subjects) else 0)
            c_h, c_m = st.sidebar.columns(2)
            h = c_h.number_input("Hours", 0, 24, key=f"h{i}")
            m = c_m.number_input("Mins", 0, 59, key=f"m{i}")
            s_names.append(name)
            s_hours.append(h + (m/60))

        if st.sidebar.button("SAVE DATA", use_container_width=True):
            with sqlite3.connect('alevel_tracker_final.db') as conn:
                conn.execute('''INSERT INTO study_logs VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(username, date) DO UPDATE SET 
                              stream=excluded.stream, sub1_name=excluded.sub1_name, sub1_h=excluded.sub1_h,
                              sub2_name=excluded.sub2_name, sub2_h=excluded.sub2_h,
                              sub3_name=excluded.sub3_name, sub3_h=excluded.sub3_h''', 
                           (st.session_state.username, str(entry_date), stream_choice, s_names[0], s_hours[0], s_names[1], s_hours[1], s_names[2], s_hours[2]))
                conn.commit()
            st.success(f"{entry_date} දත්ත සුරැකුණා!")

    with tab2:
        st.header("🔍 සතිපතා වාර්තා පරීක්ෂාව")
        # මෙන්න ඔබ ඉල්ලූ සතිය තෝරන කැලැන්ඩරය (Calendar)
        report_start = st.date_input("සතිය ආරම්භ වන දිනය තෝරන්න (Select Week Start Date)", datetime.now() - timedelta(days=6), key="rep_cal")
        report_end = report_start + timedelta(days=6)
        
        st.info(f"පෙන්වන කාල සීමාව: {report_start} සිට {report_end} දක්වා")

        with sqlite3.connect('alevel_tracker_final.db') as conn:
            df = pd.read_sql_query(f"SELECT * FROM study_logs WHERE username = '{st.session_state.username}'", conn)

        if not df.empty:
            df['date'] = pd.to_datetime(df['date']).dt.date
            mask = (df['date'] >= report_start) & (df['date'] <= report_end)
            week_df = df.loc[mask].sort_values('date')

            if not week_df.empty:
                total_h = week_df[['sub1_h', 'sub2_h', 'sub3_h']].sum().sum()
                m1, m2, m3 = st.columns(3)
                m1.metric("සතියේ මුළු පැය", f"{total_h:.1f} h")
                m2.metric("දිනකට සාමාන්‍යය", f"{(total_h/7):.1f} h")
                m3.metric("සටහන් කළ දින", f"{len(week_df)} / 7")

                st.divider()
                last_entry = week_df.iloc[-1]
                names = [last_entry['sub1_name'], last_entry['sub2_name'], last_entry['sub3_name']]
                totals = [week_df['sub1_h'].sum(), week_df['sub2_h'].sum(), week_df['sub3_h'].sum()]
                
                c1, c2, c3 = st.columns(3)
                for i, col in enumerate([c1, c2, c3]):
                    col.markdown(f"<div class='subject-card'>{names[i]}<br>මුළු කාලය: {totals[i]:.1f} h</div>", unsafe_allow_html=True)

                st.subheader("📊 සතිපතා ප්‍රස්ථාරය")
                fig, ax = plt.subplots(figsize=(10, 4))
                week_df.plot(kind='bar', x='date', ax=ax, color=['#2ecc71', '#3498db', '#e67e22'])
                ax.legend(names)
                st.pyplot(fig)
            else:
                st.warning("තෝරාගත් කාල සීමාව සඳහා දත්ත නැත.")
        else:
            st.info("පැරණි දත්ත බැලීමට ප්‍රථමයෙන් දත්ත ඇතුළත් කරන්න.")

    st.sidebar.divider()
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

else:
    st.title("🎓 A/L Smart Study Tracker Pro")
    st.info("පද්ධතිය භාවිතා කිරීමට කරුණාකර Login වන්න.")