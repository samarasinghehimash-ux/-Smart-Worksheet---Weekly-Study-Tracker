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
                      (user_name TEXT, date TEXT, stream TEXT, sub1_name TEXT, sub1_h REAL, sub2_name TEXT, sub2_h REAL, sub3_name TEXT, sub3_h REAL, 
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
    "Physical Science (Maths)": ["Combined Maths", "Physics", "Chemistry"],
    "Biological Science (Bio)": ["Biology", "Chemistry", "Physics"],
    "Commerce": ["Accounting", "Business Studies", "Economics"],
    "Arts": ["Subject 01", "Subject 02", "Subject 03"],
    "Technology": ["SFT", "ET/BST", "ICT/Agri"]
}

# --- Header ---
st.title("🎓 A/L Smart Study Tracker Pro")
# 1. ගුරුතුමාගේ නම එක් කිරීම
st.markdown("Concept by: **Plan Master Charaka Dhananjaya** | Developed by: **Hiratrix IT Solutions**")
st.divider()

# --- Sidebar: User & Stream Settings ---
st.sidebar.header("👤 User Settings")
# 1. Username පද්ධතිය: පරිශීලකයා හඳුනාගැනීම සඳහා නමක් ඇතුළත් කළ හැකියි.
user_id = st.sidebar.text_input("ඔබේ නම (Username)", "Guest").strip().lower()

if user_id == "guest":
    st.warning("කරුණාකර ඔබව හඳුනාගැනීමට නමක් (Username) ලබා දෙන්න.")

st.sidebar.divider()

# --- Data Entry Section ---
st.sidebar.subheader("📝 Daily Entry")
# දත්ත ඇතුළත් කරන දිනය
entry_date = st.sidebar.date_input("දත්ත ඇතුළත් කරන දිනය", datetime.now())

# 2. විෂය ධාරාව ඇතුළත් කර විෂයන් තෝරාගැනීම
stream_choice = st.sidebar.selectbox("විෂය ධාරාව (Stream)", list(STREAMS.keys()), key="stream_select")
# තෝරාගත් ධාරාව අනුව Default විෂයයන් ලබා ගැනීම
default_subjects = STREAMS[stream_choice]

st.sidebar.subheader("ඔබේ විෂයන් තෝරන්න")
# පරිශීලකයාට තමන්ගේ විෂයන් තෝරා ගැනීමට/වෙනස් කිරීමට ඉඩ ලබා දීම
subject1 = st.sidebar.text_input("1 වෙනි විෂය", default_subjects[0])
subject2 = st.sidebar.text_input("2 වෙනි විෂය", default_subjects[1])
subject3 = st.sidebar.text_input("3 වෙනි විෂය", default_subjects[2])

st.sidebar.divider()

# 2. පැය ගණන සහ මිනිත්තු ගණන එක ලඟට ගැනීම
# Accounting (S1)
st.sidebar.subheader(f"1. {subject1}")
c1_h, c1_m = st.sidebar.columns(2)
h1 = c1_h.number_input("Hours", 0, 24, key="h1")
m1 = c1_m.number_input("Minutes", 0, 59, key="m1")

# Business Studies (S2)
st.sidebar.subheader(f"2. {subject2}")
c2_h, c2_m = st.sidebar.columns(2)
h2 = c2_h.number_input("Hours", 0, 24, key="h2")
m2 = c2_m.number_input("Minutes", 0, 59, key="m2")

# Economics (S3)
st.sidebar.subheader(f"3. {subject3}")
c3_h, c3_m = st.sidebar.columns(2)
h3 = c3_h.number_input("Hours", 0, 24, key="h3")
m3 = c3_m.number_input("Minutes", 0, 59, key="m3")

if st.sidebar.button("SAVE DAILY DATA", use_container_width=True):
    if user_id != "guest":
        s1 = h1 + (m1/60)
        s2 = h2 + (m2/60)
        s3 = h3 + (m3/60)
        
        conn = sqlite3.connect('alevel_tracker_pro.db')
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO study_logs VALUES(?,?,?,?,?,?,?,?,?) 
                          ON CONFLICT(user_name, date) DO UPDATE SET 
                          stream=excluded.stream, 
                          sub1_name=excluded.sub1_name, sub1_h=excluded.sub1_h, 
                          sub2_name=excluded.sub2_name, sub2_h=excluded.sub2_h, 
                          sub3_name=excluded.sub3_name, sub3_h=excluded.sub3_h''', 
                       (user_id, str(entry_date), stream_choice, subject1, s1, subject2, s2, subject3, s3))
        conn.commit(); conn.close()
        st.sidebar.success("දත්ත සුරැකිනු ලැබුවා!")
        st.rerun()
    else:
        st.sidebar.error("දත්ත සුරැකීමට කරුණාකර නමක් ඇතුළත් කරන්න.")

# --- Main Dashboard Logic ---
# සතියේ ආරම්භක දිනය තෝරා ගැනීම
st.subheader("⚙️ Settings")
start_date = st.date_input("සතිය ආරම්භ වන දිනය", datetime.now() - timedelta(days=6))
end_date = start_date + timedelta(days=6)
st.info(f"පෙන්වන කාල සීමාව: {start_date} සිට {end_date} දක්වා")
st.divider()

conn = sqlite3.connect('alevel_tracker_pro.db')
# දැන් query කරන්නේ අදාළ පරිශීලකයාගේ (user_id) දත්ත පමණයි
query = f"SELECT * FROM study_logs WHERE user_name = '{user_id}'"
all_df = pd.read_sql_query(query, conn)
conn.close()

st.subheader(f"👋 සාදරයෙන් පිළිගනිමු, {user_id.capitalize()}!")

if not all_df.empty:
    # Date column එක date object එකක් බවට හැරවීම
    all_df['date'] = pd.to_datetime(all_df['date']).dt.date
    
    # තෝරාගත් දින 7 පරාසය තුළ ඇති දත්ත පමණක් පෙරීම (Filtering)
    mask = (all_df['date'] >= start_date) & (all_df['date'] <= end_date)
    df = all_df.loc[mask].sort_values('date')

    # Metrics
    total_h = df[['sub1_h', 'sub2_h', 'sub3_h']].sum().sum()
    m1, m2, m3 = st.columns(3)
    m1.metric("සතියේ මුළු පැය (Total)", f"{total_h:.1f} h")
    m2.metric("දිනකට සාමාන්‍යය (Average)", f"{(total_h/7):.1f} h")
    m3.metric("දත්ත ඇති දින", f"{len(df)} / 7")

    st.divider()

    # Subject Totals (විෂය අනුව එකතුව)
    # දත්ත ඇති අවසන් දිනයේ විෂයයන්ගේ නම් ලබා ගැනීම
    if not df.empty:
        last_row = df.iloc[-1]
        subjects = [last_row['sub1_name'], last_row['sub2_name'], last_row['sub3_name']]
    else:
        subjects = ["Subject 1", "Subject 2", "Subject 3"]

    s1_t, s2_t, s3_t = df['sub1_h'].sum(), df['sub2_h'].sum(), df['sub3_h'].sum()
    
    c1, c2, c3 = st.columns(3)
    c1.info(f"**{subjects[0]}**\n\nTotal: {s1_t:.1f} h")
    c2.info(f"**{subjects[1]}**\n\nTotal: {s2_t:.1f} h")
    c3.info(f"**{subjects[2]}**\n\nTotal: {s3_t:.1f} h")

    st.divider()

    # Chart (සතිපතා ප්‍රස්ථාරය)
    st.subheader(f"සතිපතා ප්‍රස්ථාරය ({start_date} - {end_date})")
    if not df.empty:
        fig, ax = plt.subplots(figsize=(12, 5))
        df.plot(kind='bar', x='date', ax=ax, color=['#2ecc71', '#3498db', '#e67e22'])
        ax.legend(subjects)
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.warning("තෝරාගත් කාල සීමාව සඳහා දත්ත කිසිවක් නැත.")

    # Weekly Feedback (ප්‍රතිචාර)
    if not df.empty:
        st.subheader("ප්‍රගතිය (Weekly Progress)")
        if total_hours < 40:
            st.error(f"ඔබේ සතියේ එකතුව {total_hours:.1f}h කි. ඉලක්කය සපුරා ගැනීමට තව මහන්සි වන්න! 😟")
        elif total_hours <= 60:
            st.success(f"ඔබේ සතියේ එකතුව {total_hours:.1f}h කි. ඉතා හොඳයි, දිගටම කරගෙන යන්න! 👍")
        else:
            st.warning(f"ඔබේ සතියේ එකතුව {total_hours:.1f}h කි. සුපිරි වැඩක්! 🔥🚀")
else:
    st.info("ඔබේ නමින් තවම දත්ත ඇතුළත් කර නැත. පසෙකින් ඇති පුවරුවෙන් ආරම්භ කරන්න.")

# Reset Button
st.sidebar.divider()
if st.sidebar.button("🗑️ DELETE ALL DATA"):
    conn = sqlite3.connect('alevel_tracker_pro.db')
    conn.execute("DELETE FROM study_logs")
    conn.commit(); conn.close()
    st.rerun()