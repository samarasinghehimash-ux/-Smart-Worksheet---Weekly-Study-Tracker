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
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_preferences 
                          (username TEXT PRIMARY KEY, stream TEXT, sub1 TEXT, sub2 TEXT, sub3 TEXT)''')
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
    .main-title { font-size: 3.5rem !important; font-weight: 900 !important; color: #ffffff; text-align: center; text-shadow: 3px 3px 6px #000000; margin-bottom: 5px; }
    [data-testid="stMetricValue"] { color: #000000 !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] p { color: #000000 !important; font-weight: bold !important; font-size: 1.1rem !important; }
    div[data-testid="stMetric"] { background-color: #ffffff !important; padding: 20px; border-radius: 12px; border: 1px solid #dddddd; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .subject-card { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 8px solid #2196f3; color: #000000 !important; margin-bottom: 10px; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .business-name { color: #2ecc71; font-weight: bold; font-size: 1.2rem; }
    .section-head { background-color: #f1f1f1; padding: 5px 15px; border-radius: 5px; color: #333; font-weight: bold; margin: 10px 0; }
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

# --- Sidebar Logic ---
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
                except: st.sidebar.error("මෙම නම දැනටමත් පවතී.")
    else:
        if st.sidebar.button("ඇතුළු වන්න"):
            with sqlite3.connect('alevel_tracker_final.db') as conn:
                data = conn.execute('SELECT password FROM users WHERE username =?', (u_in,)).fetchone()
                if data and check_hashes(p_in, data[0]):
                    st.session_state.logged_in, st.session_state.username = True, u_in
                    st.rerun()
                else: st.sidebar.error("නම හෝ මුරපදය වැරදියි.")
else:
    st.sidebar.success(f"පරිශීලක: {st.session_state.username}")
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

# --- Main App Logic ---
if st.session_state.logged_in:
    st.markdown('<p class="main-title">🎓 A/L Smart Study Tracker Pro</p>', unsafe_allow_html=True)
    st.markdown(f"<div style='text-align: center;'>Concept by: <b>Plan Master Charaka Dhananjaya</b> | Developed by: <span class='business-name'>Hiratrix IT Solutions</span></div>", unsafe_allow_html=True)
    st.divider()

    with sqlite3.connect('alevel_tracker_final.db') as conn:
        pref = conn.execute('SELECT stream, sub1, sub2, sub3 FROM user_preferences WHERE username=?', (st.session_state.username,)).fetchone()

    if not pref:
        st.warning("පළමුව ඔබගේ විෂය ධාරාව සහ විෂයයන් තෝරා සුරකින්න.")
        with st.expander("🎓 විෂයයන් සැකසීම", expanded=True):
            stream = st.selectbox("විෂය ධාරාව", list(SUBJECTS_DATA.keys()))
            c1, c2, c3 = st.columns(3)
            s1 = c1.selectbox("විෂය 1", SUBJECTS_DATA[stream], key="s1")
            s2 = c2.selectbox("විෂය 2", SUBJECTS_DATA[stream], key="s2")
            s3 = c3.selectbox("විෂය 3", SUBJECTS_DATA[stream], key="s3")
            if st.button("විෂයයන් සුරකින්න"):
                with sqlite3.connect('alevel_tracker_final.db') as conn:
                    conn.execute('INSERT INTO user_preferences VALUES (?,?,?,?,?)', (st.session_state.username, stream, s1, s2, s3))
                    conn.commit()
                st.rerun()
    else:
        user_stream, user_sub1, user_sub2, user_sub3 = pref
        
        # Sidebar Data Entry
        st.sidebar.divider()
        st.sidebar.subheader("📝 අද දත්ත ඇතුළත් කිරීම")
        st.sidebar.info(f"විෂය ධාරාව: {user_stream}")
        entry_date = st.sidebar.date_input("දිනය", datetime.now(), key="main_entry_date")
        
        hours_input = []
        for s_name in [user_sub1, user_sub2, user_sub3]:
            st.sidebar.write(f"**{s_name}**")
            ch, cm = st.sidebar.columns(2)
            h = ch.number_input("පැය", 0, 24, key=f"h_{s_name}")
            m = cm.number_input("මිනිත්තු", 0, 59, key=f"m_{s_name}")
            hours_input.append(h + (m/60))

        if st.sidebar.button("දත්ත සුරකින්න (SAVE)", use_container_width=True):
            with sqlite3.connect('alevel_tracker_final.db') as conn:
                conn.execute('''INSERT INTO study_logs VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(username, date) DO UPDATE SET 
                                sub1_h=excluded.sub1_h, sub2_h=excluded.sub2_h, sub3_h=excluded.sub3_h''', 
                             (st.session_state.username, str(entry_date), user_stream, user_sub1, hours_input[0], user_sub2, hours_input[1], user_sub3, hours_input[2]))
            st.rerun()

        # Tabs for Display
        tab1, tab2 = st.tabs(["📊 අද වාර්තාව", "🔍 ඉතිහාසය"])

        with sqlite3.connect('alevel_tracker_final.db') as conn:
            all_data = pd.read_sql_query(f"SELECT * FROM study_logs WHERE username = '{st.session_state.username}'", conn)
        if not all_data.empty:
            all_data['date'] = pd.to_datetime(all_data['date']).dt.date

        def show_stats(start_date):
            if not all_data.empty:
                end_date = start_date + timedelta(days=6)
                mask = (all_data['date'] >= start_date) & (all_data['date'] <= end_date)
                week_df = all_data.loc[mask].sort_values('date')
                if not week_df.empty:
                    st.markdown('<div class="section-head">📅 සතියේ සම්පූර්ණ සාරාංශය</div>', unsafe_allow_html=True)
                    total_h = week_df[['sub1_h', 'sub2_h', 'sub3_h']].sum().sum()
                    m1, m2, m3 = st.columns(3)
                    m1.metric("සතියේ මුළු කාලය", f"{total_h:.1f} h")
                    m2.metric("දෛනික සාමාන්‍යය", f"{(total_h/7):.1f} h")
                    m3.metric("සටහන් කළ දින ගණන", f"{len(week_df)} / 7")
                    
                    st.markdown('<div class="section-head">📚 සතියේ එක් එක් විෂයන්ගේ සාරාංශය</div>', unsafe_allow_html=True)
                    names = [user_sub1, user_sub2, user_sub3]
                    totals = [week_df['sub1_h'].sum(), week_df['sub2_h'].sum(), week_df['sub3_h'].sum()]
                    c1, c2, c3 = st.columns(3)
                    for i, col in enumerate([c1, c2, c3]):
                        col.markdown(f"<div class='subject-card'>{names[i]}<br>මුළු කාලය: {totals[i]:.1f} h</div>", unsafe_allow_html=True)
                    
                    st.subheader("📊 සතිපතා ප්‍රගති ප්‍රස්ථාරය")
                    fig, ax = plt.subplots(figsize=(10, 4))
                    week_df.plot(kind='bar', x='date', ax=ax, color=['#2ecc71', '#3498db', '#e67e22'])
                    ax.legend(names)
                    st.pyplot(fig)
                else: st.warning("මෙම කාලසීමාව සඳහා දත්ත නොමැත.")
            else: st.info("දත්ත ඇතුළත් කළ පසු මෙහි දිස්වනු ඇත.")

        with tab1:
            main_start = st.date_input("ප්‍රස්ථාරය සඳහා ආරම්භක දිනය", datetime.now() - timedelta(days=6), key="tab1_start")
            show_stats(main_start)

        with tab2:
            old_start = st.date_input("පැරණි වාර්තා සඳහා දිනය තෝරන්න", datetime.now() - timedelta(days=14), key="tab2_start")
            show_stats(old_start)

        # --- 🗑️ දත්ත කළමනාකරණය (DELETE BUTTONS) ---
        st.sidebar.divider()
        st.sidebar.subheader("🗑️ දත්ත කළමනාකරණය")
        
        if st.sidebar.button("අද දවසේ දත්ත මකන්න"):
            with sqlite3.connect('alevel_tracker_final.db') as conn:
                conn.execute(f"DELETE FROM study_logs WHERE username='{st.session_state.username}' AND date='{entry_date}'")
            st.sidebar.warning(f"{entry_date} දත්ත මැකුණා!")
            st.rerun()

        if st.sidebar.button("මේ සතියේ දත්ත මකන්න"):
            # Tab 1 හි පෙන්වන සතියේ දත්ත මකයි
            w_start, w_end = str(main_start), str(main_start + timedelta(days=6))
            with sqlite3.connect('alevel_tracker_final.db') as conn:
                conn.execute(f"DELETE FROM study_logs WHERE username='{st.session_state.username}' AND date BETWEEN '{w_start}' AND '{w_end}'")
            st.sidebar.warning("තෝරාගත් සතියේ දත්ත මැකුණා!")
            st.rerun()

        if st.sidebar.button("සියලු දත්ත මකා දමන්න"):
            with sqlite3.connect('alevel_tracker_final.db') as conn:
                conn.execute(f"DELETE FROM study_logs WHERE username='{st.session_state.username}'")
            st.sidebar.error("ඔබගේ සියලු දත්ත මැකී ගියා!")
            st.rerun()

        with st.sidebar.expander("⚙️ විෂයයන් වෙනස් කිරීමට"):
            if st.button("විෂය සැකසුම් Reset කරන්න"):
                with sqlite3.connect('alevel_tracker_final.db') as conn:
                    conn.execute('DELETE FROM user_preferences WHERE username=?', (st.session_state.username,))
                    conn.commit()
                st.rerun()

else:
    st.info("පද්ධතිය භාවිතා කිරීමට කරුණාකර Login වන්න.")