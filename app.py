import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import hashlib

# 1. Database Setup with Password Support
def init_db():
    with sqlite3.connect('alevel_tracker_final.db') as conn:
        cursor = conn.cursor()
        # පරිශීලක තොරතුරු සඳහා table එක
        cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                          (username TEXT PRIMARY KEY, password TEXT)''')
        # පාඩම් දත්ත සඳහා table එක
        cursor.execute('''CREATE TABLE IF NOT EXISTS study_logs 
                          (username TEXT, date TEXT, stream TEXT, 
                           sub1_name TEXT, sub1_h REAL, 
                           sub2_name TEXT, sub2_h REAL, 
                           sub3_name TEXT, sub3_h REAL, 
                           UNIQUE(username, date))''')
        conn.commit()

# Password එක ආරක්ෂිතව ගබඩා කිරීමට (Hashing)
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

init_db()

# --- Page Config ---
st.set_page_config(page_title="A/L Study Tracker Pro", layout="wide")

# --- UI Styles (වර්ණ සහ අකුරු පැහැදිලි කිරීමට) ---
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { color: #1a252f !important; font-weight: bold; }
    div[data-testid="stMetric"] { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #eeeeee; }
    /* විෂය එකතුව පෙන්වන කොටු වල අකුරු තද කළු පැහැයට */
    .subject-card {
        background-color: #f0f7ff;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #2196f3;
        color: #000000 !important;
        margin-bottom: 10px;
    }
    .subject-card b, .subject-card span { color: #000000 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- Subject Configuration ---
SUBJECTS_DATA = {
    "Physical Science (Maths)": ["Combined Maths", "Physics", "Chemistry", "ICT"],
    "Biological Science (Bio)": ["Biology", "Chemistry", "Physics", "Agricultural Science"],
    "Commerce": ["Accounting", "Business Studies", "Economics", "ICT", "Business Statistics"],
    "Arts": ["Sinhala", "History", "Logic", "Political Science", "Geography", "Buddhist Civilization", "Economics", "ICT"],
    "Technology": ["SFT", "Engineering Tech", "Bio Systems Tech", "ICT", "Economics"]
}

# --- Login / Signup Logic ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

st.sidebar.title("🔐 Login / Signup")
choice = st.sidebar.selectbox("තෝරන්න", ["Login", "Sign Up"])

if choice == "Sign Up":
    new_user = st.sidebar.text_input("අලුත් නමක් (Username)")
    new_password = st.sidebar.text_input("මුරපදයක් (Password)", type='password')
    if st.sidebar.button("ගිණුම සාදන්න"):
        with sqlite3.connect('alevel_tracker_final.db') as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO users(username, password) VALUES (?,?)', (new_user, make_hashes(new_password)))
                conn.commit()
                st.sidebar.success("ගිණුම සාර්ථකව සැදුණා! දැන් Login වන්න.")
            except:
                st.sidebar.error("මෙම නම දැනටමත් පවතී.")

elif choice == "Login":
    username = st.sidebar.text_input("නම (Username)")
    password = st.sidebar.text_input("මුරපදය (Password)", type='password')
    if st.sidebar.button("ඇතුළු වන්න"):
        with sqlite3.connect('alevel_tracker_final.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT password FROM users WHERE username =?', (username,))
            data = cursor.fetchone()
            if data and check_hashes(password, data[0]):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.sidebar.error("නම හෝ මුරපදය වැරදියි.")

# --- Main App (Logged In) ---
if st.session_state.logged_in:
    st.sidebar.success(f"Logged in as: {st.session_state.username}")
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    st.title("🎓 A/L Smart Study Tracker Pro")
    st.markdown("Concept by: **Plan Master Charaka Dhananjaya** | Developed by: **Hiratrix IT Solutions**")
    st.divider()

    # --- Data Entry ---
    st.sidebar.subheader("📝 Daily Entry")
    entry_date = st.sidebar.date_input("දිනය", datetime.now())
    stream_choice = st.sidebar.selectbox("විෂය ධාරාව", list(SUBJECTS_DATA.keys()))
    available_subjects = SUBJECTS_DATA[stream_choice]

    s_names = []
    s_hours = []
    for i in range(3):
        st.sidebar.write(f"--- විෂය {i+1} ---")
        name = st.sidebar.selectbox(f"විෂය තෝරන්න", available_subjects, key=f"n{i}", index=i if i < len(available_subjects) else 0)
        c_h, c_m = st.sidebar.columns(2)
        h = c_h.number_input("Hours", 0, 24, key=f"h{i}")
        m = c_m.number_input("Mins", 0, 59, key=f"m{i}")
        s_names.append(name)
        s_hours.append(h + (m/60))

    if st.sidebar.button("SAVE DATA", use_container_width=True):
        with sqlite3.connect('alevel_tracker_final.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO study_logs VALUES(?,?,?,?,?,?,?,?,?) 
                              ON CONFLICT(username, date) DO UPDATE SET 
                              stream=excluded.stream, sub1_name=excluded.sub1_name, sub1_h=excluded.sub1_h,
                              sub2_name=excluded.sub2_name, sub2_h=excluded.sub2_h,
                              sub3_name=excluded.sub3_name, sub3_h=excluded.sub3_h''', 
                           (st.session_state.username, str(entry_date), stream_choice, s_names[0], s_hours[0], s_names[1], s_hours[1], s_names[2], s_hours[2]))
            conn.commit()
        st.sidebar.success("දත්ත සුරැකුණා!")
        st.rerun()

    # --- Dashboard Analysis ---
    start_date = st.date_input("සතිය ආරම්භ වන දිනය", datetime.now() - timedelta(days=6))
    end_date = start_date + timedelta(days=6)

    with sqlite3.connect('alevel_tracker_final.db') as conn:
        df = pd.read_sql_query(f"SELECT * FROM study_logs WHERE username = '{st.session_state.username}'", conn)

    if not df.empty:
        df['date'] = pd.to_datetime(df['date']).dt.date
        mask = (df['date'] >= start_date) & (df['date'] <= end_date)
        week_df = df.loc[mask].sort_values('date')

        if not week_df.empty:
            total_h = week_df[['sub1_h', 'sub2_h', 'sub3_h']].sum().sum()
            m1, m2, m3 = st.columns(3)
            m1.metric("සතියේ මුළු පැය", f"{total_h:.1f} h")
            m2.metric("දිනකට සාමාන්‍යය", f"{(total_h/7):.1f} h")
            m3.metric("සටහන් කළ දින", f"{len(week_df)} / 7")

            st.divider()
            st.subheader("විෂය අනුව එකතුව (Subject Totals)")
            last = week_df.iloc[-1]
            names = [last['sub1_name'], last['sub2_name'], last['sub3_name']]
            totals = [week_df['sub1_h'].sum(), week_df['sub2_h'].sum(), week_df['sub3_h'].sum()]
            
            c1, c2, c3 = st.columns(3)
            for i, col in enumerate([c1, c2, c3]):
                col.markdown(f"""<div class='subject-card'><b>{names[i]}</b><br><span>Total: {totals[i]:.1f} h</span></div>""", unsafe_allow_html=True)

            st.subheader("Weekly Chart")
            fig, ax = plt.subplots(figsize=(10, 4))
            week_df.plot(kind='bar', x='date', ax=ax, color=['#2ecc71', '#3498db', '#e67e22'])
            ax.legend(names)
            st.pyplot(fig)
        else:
            st.warning("තෝරාගත් කාල සීමාව සඳහා දත්ත නැත.")
    else:
        st.info("දත්ත ඇතුළත් කිරීම ආරම්භ කරන්න.")

    if st.sidebar.button("🗑️ පෞද්ගලික දත්ත මකන්න"):
        with sqlite3.connect('alevel_tracker_final.db') as conn:
            conn.execute(f"DELETE FROM study_logs WHERE username='{st.session_state.username}'")
        st.rerun()

else:
    st.info("ඉදිරියට යාමට කරුණාකර Sidebar එකෙන් Login වන්න හෝ Sign Up වන්න.")