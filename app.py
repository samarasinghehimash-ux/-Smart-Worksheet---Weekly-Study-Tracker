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
    .report-header { background-color: #2c3e50; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 20px; }
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

# --- Login Logic ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

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
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("ඇතුළු වන්න"):
        with sqlite3.connect('alevel_tracker_final.db') as conn:
            data = conn.execute('SELECT password FROM users WHERE username =?', (username,)).fetchone()
            if data and check_hashes(password, data[0]):
                st.session_state.logged_in, st.session_state.username = True, username
                st.rerun()
            else: st.sidebar.error("නම හෝ මුරපදය වැරදියි.")

# --- Main App ---
if st.session_state.logged_in:
    st.sidebar.success(f"User: {st.session_state.username}")
    
    # පටිත්ත (Tabs) මගින් අද දත්ත සහ පැරණි වාර්තා වෙන් කිරීම
    tab1, tab2 = st.tabs(["📝 අද දත්ත ඇතුළත් කිරීම", "📊 පැරණි වාර්තා පරීක්ෂාව"])

    with tab1:
        st.title("🎓 Daily Study Tracker")
        st.markdown("Concept by: **Plan Master Charaka Dhananjaya**")
        
        # දත්ත ඇතුළත් කිරීමේ Sidebar එක
        st.sidebar.subheader("📝 දත්ත ඇතුළත් කරන්න")
        entry_date = st.sidebar.date_input("දිනය", datetime.now(), key="entry_date")
        stream_choice = st.sidebar.selectbox("විෂය ධාරාව", list(SUBJECTS_DATA.keys()))
        available_subjects = SUBJECTS_DATA[stream_choice]

        s_names, s_hours = [], []
        for i in range(3):
            st.sidebar.write(f"--- විෂය {i+1} ---")
            name = st.sidebar.selectbox(f"තෝරන්න {i+1}", available_subjects, key=f"n{i}", index=i if i < len(available_subjects) else 0)
            c_h, c_m = st.sidebar.columns(2)
            h, m = c_h.number_input("Hours", 0, 24, key=f"h{i}"), c_m.number_input("Mins", 0, 59, key=f"m{i}")
            s_names.append(name); s_hours.append(h + (m/60))

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
        st.header("🔍 පැරණි සතිපතා වාර්තා බැලීම")
        st.write("ඔබට අවශ්‍ය සතියේ **ආරම්භක දිනය** පහත කැලැන්ඩරයෙන් තෝරන්න.")
        
        # කැලැන්ඩරය හරහා සතිය තේරීම
        report_start = st.date_input("සතිය ආරම්භ වන දිනය තෝරන්න", datetime.now() - timedelta(days=6), key="report_date")
        report_end = report_start + timedelta(days=6)
        
        st.markdown(f"<div class='report-header'>වාර්තාව: {report_start} සිට {report_end} දක්වා</div>", unsafe_allow_html=True)

        with sqlite3.connect('alevel_tracker_final.db') as conn:
            df = pd.read_sql_query(f"SELECT * FROM study_logs WHERE username = '{st.session_state.username}'", conn)

        if not df.empty:
            df['date'] = pd.to_datetime(df['date']).dt.date
            mask = (df['date'] >= report_start) & (df['date'] <= report_end)
            week_df = df.loc[mask].sort_values('date')

            if not week_df.empty:
                # Summary Metrics
                total_h = week_df[['sub1_h', 'sub2_h', 'sub3_h']].sum().sum()
                m1, m2, m3 = st.columns(3)
                m1.metric("සතියේ මුළු පැය", f"{total_h:.1f} h")
                m2.metric("දිනකට සාමාන්‍යය", f"{(total_h/7):.1f} h")
                m3.metric("දත්ත ඇති දින", f"{len(week_df)} / 7")

                st.divider()
                
                # Subject Totals
                last_entry = week_df.iloc[-1]
                sub_names = [last_entry['sub1_name'], last_entry['sub2_name'], last_entry['sub3_name']]
                sub_totals = [week_df['sub1_h'].sum(), week_df['sub2_h'].sum(), week_df['sub3_h'].sum()]
                
                c1, c2, c3 = st.columns(3)
                for i, col in enumerate([c1, c2, c3]):
                    col.markdown(f"<div class='subject-card'>{sub_names[i]}<br>මුළු කාලය: {sub_totals[i]:.1f} h</div>", unsafe_allow_html=True)

                # Weekly Chart
                st.subheader("📊 සතිපතා ප්‍රස්ථාරය")
                fig, ax = plt.subplots(figsize=(10, 4))
                week_df.plot(kind='bar', x='date', ax=ax, color=['#2ecc71', '#3498db', '#e67e22'])
                ax.legend(sub_names)
                plt.xticks(rotation=45)
                st.pyplot(fig)
                
                # Data Table
                with st.expander("විස්තරාත්මක දත්ත සටහන බලන්න"):
                    st.dataframe(week_df, use_container_width=True)
            else:
                st.warning(f"{report_start} සිට {report_end} දක්වා කාල සීමාව තුළ ඔබ දත්ත ඇතුළත් කර නැත.")
        else:
            st.info("ඔබ තවම දත්ත කිසිවක් ඇතුළත් කර නැත.")

    st.sidebar.divider()
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

else:
    st.title("🎓 A/L Smart Study Tracker Pro")
    st.info("පද්ධතිය භාවිතා කිරීමට කරුණාකර Login වන්න. ඔබට ගිණුමක් නැතිනම් Sign Up වන්න.")