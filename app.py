import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# 1. Database Setup with User Support
def init_db():
    conn = sqlite3.connect('alevel_tracker_pro.db')
    cursor = conn.cursor()
    # මෙහිදී user_name නමින් අලුත් column එකක් එක් කර ඇත
    cursor.execute('''CREATE TABLE IF NOT EXISTS study_logs 
                      (user_name TEXT, date TEXT, stream TEXT, sub1_h REAL, sub2_h REAL, sub3_h REAL, 
                      UNIQUE(user_name, date))''')
    conn.commit()
    conn.close()

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

# --- Stream Configuration ---
STREAMS = {
    "Commerce": ["Accounting", "Business Studies", "Economics"],
    "Physical Science (Maths)": ["Combined Maths", "Physics", "Chemistry"],
    "Biological Science (Bio)": ["Biology", "Chemistry", "Physics"],
    "Arts": ["Subject 01", "Subject 02", "Subject 03"],
    "Technology": ["SFT", "ET/BST", "ICT/Agri"]
}

# --- Header ---
st.title("🎓 A/L Smart Study Tracker")
st.markdown("Developed for all Sri Lankan A/L Students | **Hiratrix IT Solutions**")

# --- Sidebar: User & Stream Settings ---
st.sidebar.header("👤 User Settings")
user_id = st.sidebar.text_input("ඔබේ නම (Username)", "Guest").strip().lower()

if user_id == "guest":
    st.warning("කරුණාකර ඔබව හඳුනාගැනීමට නමක් (Username) ලබා දෙන්න.")

stream_choice = st.sidebar.selectbox("විෂය ධාරාව (Stream)", list(STREAMS.keys()))
subjects = STREAMS[stream_choice]

# සතියේ ආරම්භක දිනය
start_date = st.sidebar.date_input("සතිය ආරම්භ වන දිනය", datetime.now() - timedelta(days=6))
end_date = start_date + timedelta(days=6)

st.sidebar.divider()

# --- Data Entry Section ---
st.sidebar.subheader("📝 Daily Entry")
entry_date = st.sidebar.date_input("දත්ත ඇතුළත් කරන දිනය", datetime.now())

h1 = st.sidebar.number_input(f"{subjects[0]} (h)", 0, 24, key="h1")
m1 = st.sidebar.number_input(f"{subjects[0]} (m)", 0, 59, key="m1")
h2 = st.sidebar.number_input(f"{subjects[1]} (h)", 0, 24, key="h2")
m2 = st.sidebar.number_input(f"{subjects[1]} (m)", 0, 59, key="m2")
h3 = st.sidebar.number_input(f"{subjects[2]} (h)", 0, 24, key="h3")
m3 = st.sidebar.number_input(f"{subjects[2]} (m)", 0, 59, key="m3")

if st.sidebar.button("SAVE DATA", use_container_width=True):
    if user_id != "guest":
        s1 = h1 + (m1/60)
        s2 = h2 + (m2/60)
        s3 = h3 + (m3/60)
        
        conn = sqlite3.connect('alevel_tracker_pro.db')
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO study_logs VALUES(?,?,?,?,?,?) 
                          ON CONFLICT(user_name, date) DO UPDATE SET 
                          stream=excluded.stream, sub1_h=excluded.sub1_h, 
                          sub2_h=excluded.sub2_h, sub3_h=excluded.sub3_h''', 
                       (user_id, str(entry_date), stream_choice, s1, s2, s3))
        conn.commit(); conn.close()
        st.sidebar.success("දත්ත සුරැකිනු ලැබුවා!")
        st.rerun()
    else:
        st.sidebar.error("දත්ත සුරැකීමට කරුණාකර නමක් ඇතුළත් කරන්න.")

# --- Main Dashboard Logic ---
conn = sqlite3.connect('alevel_tracker_pro.db')
# දැන් query කරන්නේ අදාළ පරිශීලකයාගේ (user_id) දත්ත පමණයි
query = f"SELECT * FROM study_logs WHERE user_name = '{user_id}'"
all_df = pd.read_sql_query(query, conn)
conn.close()

st.subheader(f"👋 සාදරයෙන් පිළිගනිමු, {user_id.capitalize()}!")

if not all_df.empty:
    all_df['date'] = pd.to_datetime(all_df['date']).dt.date
    mask = (all_df['date'] >= start_date) & (all_df['date'] <= end_date)
    df = all_df.loc[mask].sort_values('date')

    # Metrics
    total_h = df[['sub1_h', 'sub2_h', 'sub3_h']].sum().sum()
    m1, m2, m3 = st.columns(3)
    m1.metric("සතියේ මුළු පැය", f"{total_h:.1f} h")
    m2.metric("දිනකට සාමාන්‍යය", f"{(total_h/7):.1f} h")
    m3.metric("දත්ත ඇති දින", f"{len(df)} / 7")

    st.divider()

    # Subject Totals
    s1_t, s2_t, s3_t = df['sub1_h'].sum(), df['sub2_h'].sum(), df['sub3_h'].sum()
    c1, c2, c3 = st.columns(3)
    c1.info(f"**{subjects[0]}**\n\n{s1_t:.1f} h")
    c2.info(f"**{subjects[1]}**\n\n{s2_t:.1f} h")
    c3.info(f"**{subjects[2]}**\n\n{s3_t:.1f} h")

    # Chart
    st.subheader(f"සතිපතා ප්‍රස්ථාරය ({stream_choice})")
    if not df.empty:
        fig, ax = plt.subplots(figsize=(10, 4))
        df.plot(kind='bar', x='date', ax=ax, color=['#2ecc71', '#3498db', '#e67e22'])
        ax.legend(subjects)
        st.pyplot(fig)
else:
    st.info("ඔබේ නමින් තවම දත්ත ඇතුළත් කර නැත. පසෙකින් ඇති පුවරුවෙන් ආරම්භ කරන්න.")