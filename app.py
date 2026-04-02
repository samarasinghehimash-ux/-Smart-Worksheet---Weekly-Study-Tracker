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
        conn.commit()

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return make_hashes(password) == hashed_text

init_db()

# --- Page Config ---
st.set_page_config(page_title="A/L Study Tracker Pro", layout="wide")

# --- UI Styles (Updated for Dark/Light Mode) ---
st.markdown("""
    <style>
    .main-title {
        font-size: 3rem !important;
        font-weight: 900 !important;
        text-align: center;
        margin-bottom: 5px;
    }
    /* Metric Card Styling */
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }
    .subject-card {
        padding: 15px;
        border-radius: 10px;
        border-left: 8px solid #2196f3;
        margin-bottom: 10px;
        font-weight: bold;
        background-color: rgba(33, 150, 243, 0.1);
    }
    .business-name { color: #2ecc71; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

SUBJECTS_DATA = {
    "Physical Science (Maths)": ["Combined Maths", "Physics", "Chemistry", "ICT"],
    "Biological Science (Bio)": ["Biology", "Chemistry", "Physics", "Agricultural Science"],
    "Commerce": ["Accounting", "Business Studies", "Economics", "ICT"],
    "Arts": ["Sinhala", "History", "Logic", "Political Science", "Geography", "Economics", "ICT"],
    "Technology": ["SFT", "Engineering Tech", "Bio Systems Tech", "ICT"]
}

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- Sidebar Login/Sign Up ---
st.sidebar.title("🔐 Access Control")
if not st.session_state.logged_in:
    auth_mode = st.sidebar.selectbox("තෝරන්න", ["Login", "Sign Up"])
    u_in = st.sidebar.text_input("Username")
    p_in = st.sidebar.text_input("Password", type='password')
    
    if auth_mode == "Sign Up":
        if st.sidebar.button("ගිණුම සාදන්න"):
            with sqlite3.connect('alevel_tracker_final.db') as conn:
                try:
                    conn.execute('INSERT INTO users VALUES (?,?)', (u_in, make_hashes(p_in)))
                    conn.commit()
                    st.sidebar.success("සාර්ථකයි! දැන් Login වන්න.")
                except: st.sidebar.error("මෙම නම පද්ධතියේ පවතී.")
    else:
        if st.sidebar.button("ඇතුළු වන්න"):
            with sqlite3.connect('alevel_tracker_final.db') as conn:
                data = conn.execute('SELECT password FROM users WHERE username =?', (u_in,)).fetchone()
                if data and check_hashes(p_in, data[0]):
                    st.session_state.logged_in, st.session_state.username = True, u_in
                    st.rerun()
                else: st.sidebar.error("නම හෝ මුරපදය වැරදියි.")
else:
    st.sidebar.success(f"Logged in as: {st.session_state.username}")
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

# --- Main Logic ---
if st.session_state.logged_in:
    st.markdown('<p class="main-title">🎓 A/L Study Tracker Pro</p>', unsafe_allow_html=True)
    st.markdown(f"<div style='text-align: center; margin-bottom: 20px;'>Concept by: <b>Plan Master Charaka Dhananjaya</b> | Dev: <span class='business-name'>Hiratrix IT Solutions</span></div>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📝 දත්ත ඇතුළත් කිරීම", "📊 ප්‍රගති වාර්තාව"])

    # Load Data
    with sqlite3.connect('alevel_tracker_final.db') as conn:
        all_data = pd.read_sql_query(f"SELECT * FROM study_logs WHERE username = '{st.session_state.username}'", conn)
    if not all_data.empty:
        all_data['date'] = pd.to_datetime(all_data['date']).dt.date

    with tab1:
        # Sidebar Data Entry
        st.sidebar.divider()
        st.sidebar.subheader("📝 අද දත්ත ඇතුළත් කරන්න")
        entry_date = st.sidebar.date_input("දිනය", datetime.now())
        stream_choice = st.sidebar.selectbox("විෂය ධාරාව", list(SUBJECTS_DATA.keys()))
        
        s_names, s_hours = [], []
        for i in range(3):
            st.sidebar.write(f"**විෂය {i+1}**")
            name = st.sidebar.selectbox(f"තෝරන්න", SUBJECTS_DATA[stream_choice], key=f"n{i}", index=i)
            c_h, c_m = st.sidebar.columns(2)
            h = c_h.number_input("පැය", 0, 20, key=f"h{i}")
            m = c_m.number_input("මිනිත්තු", 0, 59, key=f"m{i}")
            s_names.append(name); s_hours.append(h + (m/60))

        if st.sidebar.button("SAVE DATA", use_container_width=True):
            with sqlite3.connect('alevel_tracker_final.db') as conn:
                conn.execute('''INSERT INTO study_logs VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(username, date) DO UPDATE SET 
                                sub1_h=excluded.sub1_h, sub2_h=excluded.sub2_h, sub3_h=excluded.sub3_h''', 
                             (st.session_state.username, str(entry_date), stream_choice, s_names[0], s_hours[0], s_names[1], s_hours[1], s_names[2], s_hours[2]))
            st.success("දත්ත සුරැකුණා!")
            st.rerun()

        # Display Summary for Current Week
        st.markdown("### 📅 මෙම සතියේ සාරාංශය")
        main_start = st.date_input("සතියේ ආරම්භක දිනය තෝරන්න", datetime.now() - timedelta(days=datetime.now().weekday()))

        def show_stats(start_date):
            if not all_data.empty:
                end_date = start_date + timedelta(days=6)
                mask = (all_data['date'] >= start_date) & (all_data['date'] <= end_date)
                week_df = all_data.loc[mask].sort_values('date')
                
                if not week_df.empty:
                    # Metrics
                    total_h = week_df[['sub1_h', 'sub2_h', 'sub3_h']].sum().sum()
                    col1, col2, col3 = st.columns(3)
                    col1.metric("සතියේ මුළු පැය", f"{total_h:.1f} h")
                    col2.metric("දිනක සාමාන්‍යය", f"{(total_sum := total_h/7):.1f} h")
                    col3.metric("සටහන් කළ දින", f"{len(week_df)} / 7")
                    
                    # Subject cards
                    st.write("---")
                    last_row = week_df.iloc[-1]
                    s_titles = [last_row['sub1_name'], last_row['sub2_name'], last_row['sub3_name']]
                    s_totals = [week_df['sub1_h'].sum(), week_df['sub2_h'].sum(), week_df['sub3_h'].sum()]
                    
                    c_cols = st.columns(3)
                    for idx, col in enumerate(c_cols):
                        col.markdown(f"<div class='subject-card'>{s_titles[idx]}<br><span style='font-size:1.5rem;'>{s_totals[idx]:.1f} h</span></div>", unsafe_allow_html=True)

                    # Grouped Bar Chart (Fixed for Themes)
                    st.subheader("📊 දිනපතා ප්‍රගතිය")
                    
                    fig, ax = plt.subplots(figsize=(10, 5))
                    # Background transparency for theme matching
                    fig.patch.set_alpha(0)
                    ax.set_facecolor('none')
                    
                    x = np.arange(len(week_df['date']))
                    width = 0.25
                    
                    ax.bar(x - width, week_df['sub1_h'], width, label=s_titles[0], color='#2ecc71')
                    ax.bar(x, week_df['sub2_h'], width, label=s_titles[1], color='#3498db')
                    ax.bar(x + width, week_df['sub3_h'], width, label=s_titles[2], color='#e67e22')

                    ax.set_xticks(x)
                    ax.set_xticklabels([d.strftime('%m/%d') for d in week_df['date']], color='gray')
                    ax.set_ylabel('පැය (Hours)', color='gray')
                    ax.legend()
                    
                    # Adjust colors based on Streamlit theme automatically is hard in Matplotlib, 
                    # so we use neutral gray for axes.
                    for spine in ax.spines.values(): spine.set_color('gray')
                    
                    st.pyplot(fig)
                else: st.warning("තෝරාගත් කාල සීමාවට දත්ත නැත.")
            else: st.info("ප්‍රගතිය බැලීමට පළමුව දත්ත ඇතුළත් කරන්න.")

        show_stats(main_start)

    with tab2:
        st.header("🔍 ඉතිහාසය පරීක්ෂාව")
        hist_start = st.date_input("සතියේ ආරම්භක දිනය", datetime.now() - timedelta(days=14), key="hist_s")
        st.divider()
        show_stats(hist_start)

    # Sidebar Delete Options
    st.sidebar.divider()
    st.sidebar.subheader("🗑️ දත්ත මකා දැමීම")
    if st.sidebar.button("අද දත්ත මකන්න"):
        with sqlite3.connect('alevel_tracker_final.db') as conn:
            conn.execute(f"DELETE FROM study_logs WHERE username='{st.session_state.username}' AND date='{entry_date}'")
        st.sidebar.warning("අද දත්ත මැකුණා!")
        st.rerun()

    if st.sidebar.button("සියලු දත්ත මකන්න"):
        with sqlite3.connect('alevel_tracker_final.db') as conn:
            conn.execute(f"DELETE FROM study_logs WHERE username='{st.session_state.username}'")
        st.sidebar.error("සියලු දත්ත මැකී ගියා!")
        st.rerun()

else:
    st.info("පද්ධතිය භාවිතා කිරීමට කරුණාකර Login වන්න.")