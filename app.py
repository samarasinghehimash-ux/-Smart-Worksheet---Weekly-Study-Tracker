import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# 1. Database Setup
def init_db():
    with sqlite3.connect('alevel_tracker_v5.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS study_logs 
                          (user_name TEXT, date TEXT, stream TEXT, sub1_name TEXT, sub1_h REAL, 
                           sub2_name TEXT, sub2_h REAL, sub3_name TEXT, sub3_h REAL, 
                          UNIQUE(user_name, date))''')
        conn.commit()

init_db()

# --- Page Config ---
st.set_page_config(page_title="A/L Study Tracker Pro", layout="wide")

# --- UI Styles ---
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { color: #1a252f !important; font-weight: bold; }
    div[data-testid="stMetric"] { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #ddd; }
    .stInfo { background-color: #e3f2fd; color: #0d47a1; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- Subject List Configuration ---
SUBJECTS_DATA = {
    "Physical Science (Maths)": ["Combined Maths", "Physics", "Chemistry", "ICT"],
    "Biological Science (Bio)": ["Biology", "Chemistry", "Physics", "Agricultural Science"],
    "Commerce": ["Accounting", "Business Studies", "Economics", "ICT", "Business Statistics"],
    "Arts": ["Sinhala", "History", "Logic", "Political Science", "Geography", "Buddhist Civilization", "Economics", "ICT", "English"],
    "Technology": ["SFT", "Engineering Tech", "Bio Systems Tech", "ICT", "Economics"]
}

# --- Header ---
st.title("🎓 A/L Smart Study Tracker Pro")
st.markdown("Concept by: **Plan Master Charaka Dhananjaya** | Developed by: **Hiratrix IT Solutions**")
st.divider()

# --- Sidebar: User Settings ---
st.sidebar.header("👤 User Settings")
user_id = st.sidebar.text_input("ඔබේ නම (Username)", "Guest").strip().lower()

if user_id == "guest":
    st.sidebar.warning("දත්ත සුරැකීමට නමක් ඇතුළත් කරන්න.")

st.sidebar.divider()

# --- Data Entry Section ---
st.sidebar.subheader("📝 Daily Entry")
entry_date = st.sidebar.date_input("දත්ත ඇතුළත් කරන දිනය", datetime.now())

# 1. විෂය ධාරාව සහ විෂයන් Dropdown හරහා තෝරාගැනීම
stream_choice = st.sidebar.selectbox("විෂය ධාරාව (Stream)", list(SUBJECTS_DATA.keys()))
available_subjects = SUBJECTS_DATA[stream_choice]

st.sidebar.write("---")
sub1_name = st.sidebar.selectbox("1 වෙනි විෂය තෝරන්න", available_subjects, index=0)
c1_h, c1_m = st.sidebar.columns(2)
h1 = c1_h.number_input("Hours", 0, 24, key="h1")
m1 = c1_m.number_input("Minutes", 0, 59, key="m1")

st.sidebar.write("---")
sub2_name = st.sidebar.selectbox("2 වෙනි විෂය තෝරන්න", available_subjects, index=1 if len(available_subjects)>1 else 0)
c2_h, c2_m = st.sidebar.columns(2)
h2 = c2_h.number_input("Hours", 0, 24, key="h2")
m2 = c2_m.number_input("Minutes", 0, 59, key="m2")

st.sidebar.write("---")
sub3_name = st.sidebar.selectbox("3 වෙනි විෂය තෝරන්න", available_subjects, index=2 if len(available_subjects)>2 else 0)
c3_h, c3_m = st.sidebar.columns(2)
h3 = c3_h.number_input("Hours", 0, 24, key="h3")
m3 = c3_m.number_input("Minutes", 0, 59, key="m3")

if st.sidebar.button("SAVE DATA", use_container_width=True):
    if user_id != "guest":
        s1, s2, s3 = h1+(m1/60), h2+(m2/60), h3+(m3/60)
        with sqlite3.connect('alevel_tracker_v5.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO study_logs VALUES(?,?,?,?,?,?,?,?,?) 
                              ON CONFLICT(user_name, date) DO UPDATE SET 
                              stream=excluded.stream, sub1_name=excluded.sub1_name, sub1_h=excluded.sub1_h,
                              sub2_name=excluded.sub2_name, sub2_h=excluded.sub2_h,
                              sub3_name=excluded.sub3_name, sub3_h=excluded.sub3_h''', 
                           (user_id, str(entry_date), stream_choice, sub1_name, s1, sub2_name, s2, sub3_name, s3))
            conn.commit()
        st.sidebar.success("දත්ත සාර්ථකව සුරැකුණා!")
        st.rerun()
    else:
        st.sidebar.error("නමක් ඇතුළත් කර නොමැත!")

# --- Main Dashboard ---
st.subheader("⚙️ Analysis Settings")
start_date = st.date_input("සතිය ආරම්භ වන දිනය", datetime.now() - timedelta(days=6))
end_date = start_date + timedelta(days=6)
st.info(f"පෙන්වන කාල සීමාව: {start_date} සිට {end_date} දක්වා")
st.divider()

with sqlite3.connect('alevel_tracker_v5.db') as conn:
    df_all = pd.read_sql_query(f"SELECT * FROM study_logs WHERE user_name = '{user_id}'", conn)

st.subheader(f"👋 සාදරයෙන් පිළිගනිමු, {user_id.capitalize()}!")

if not df_all.empty:
    df_all['date'] = pd.to_datetime(df_all['date']).dt.date
    mask = (df_all['date'] >= start_date) & (df_all['date'] <= end_date)
    df = df_all.loc[mask].sort_values('date')

    if not df.empty:
        total_h = df[['sub1_h', 'sub2_h', 'sub3_h']].sum().sum()
        col1, col2, col3 = st.columns(3)
        col1.metric("සතියේ මුළු පැය", f"{total_h:.1f} h")
        col2.metric("දිනකට සාමාන්‍යය", f"{(total_h/7):.1f} h")
        col3.metric("සටහන් කළ දින", f"{len(df)} / 7")

        st.divider()
        
        st.subheader("විෂය අනුව එකතුව")
        last_names = [df.iloc[-1]['sub1_name'], df.iloc[-1]['sub2_name'], df.iloc[-1]['sub3_name']]
        s1_t, s2_t, s3_t = df['sub1_h'].sum(), df['sub2_h'].sum(), df['sub3_h'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.info(f"**{last_names[0]}**\n\n{s1_t:.1f} h")
        c2.info(f"**{last_names[1]}**\n\n{s2_t:.1f} h")
        c3.info(f"**{last_names[2]}**\n\n{s3_t:.1f} h")

        st.subheader("සතිපතා විශ්ලේෂණය")
        fig, ax = plt.subplots(figsize=(12, 5))
        df.plot(kind='bar', x='date', ax=ax, color=['#2ecc71', '#3498db', '#e67e22'])
        ax.legend(last_names)
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.warning("තෝරාගත් කාල සීමාව සඳහා දත්ත නැත.")
else:
    st.info("පසෙකින් ඇති පුවරුවෙන් අද දින දත්ත ඇතුළත් කරන්න.")

# --- Reset Button (නිවැරදි කරන ලද කොටස) ---
st.sidebar.divider()
if st.sidebar.button("🗑️ DELETE ALL DATA"):
    with sqlite3.connect('alevel_tracker_v5.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM study_logs")
        conn.commit()
    st.sidebar.success("සියලු දත්ත මකා දමන ලදී!")
    st.rerun()