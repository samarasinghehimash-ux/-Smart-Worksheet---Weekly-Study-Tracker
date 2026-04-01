import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# 1. Database Setup
def init_db():
    conn = sqlite3.connect('study_tracker_v4.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS study_logs 
                      (date TEXT UNIQUE, sub1_h REAL, sub2_h REAL, sub3_h REAL)''')
    conn.commit()
    conn.close()

init_db()

# --- Page Config ---
st.set_page_config(page_title="Smart Worksheet Pro", layout="wide")

# --- UI Styles (කොටු සහ අකුරු පැහැදිලිව පෙනෙන ලෙස) ---
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { color: #1a252f !important; font-weight: bold; }
    [data-testid="stMetricLabel"] { color: #555555 !important; }
    div[data-testid="stMetric"] {
        background-color: #ffffff; padding: 15px; border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1); border: 1px solid #ddd;
    }
    .stInfo { background-color: #e3f2fd; border-left: 5px solid #2196f3; color: #0d47a1; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- Header ---
st.title("📊 Smart Worksheet - Weekly Study Tracker")
st.markdown("Concept by: **Plan Master Charaka Dhananjaya** | Developed by: **Hiratrix IT Solutions**")
st.divider()

# --- Sidebar: Settings & Entry ---
st.sidebar.header("⚙️ Settings & Daily Entry")

# සතිය ආරම්භ වන දිනය තෝරා ගැනීම
start_date = st.sidebar.date_input("සතිය ආරම්භ වන දිනය (Week Start)", datetime.now() - timedelta(days=6))
end_date = start_date + timedelta(days=6)
st.sidebar.info(f"පෙන්වන සතිය: \n{start_date} සිට {end_date} දක්වා")

st.sidebar.divider()
sub3_name = st.sidebar.selectbox("3 වෙනි විෂය තෝරන්න", ["Economics", "ICT", "Logic", "C.Maths", "Other"])

# දත්ත ඇතුළත් කිරීම (Data Entry)
st.sidebar.subheader("අද දින දත්ත ඇතුළත් කරන්න")
entry_date = st.sidebar.date_input("දිනය (Entry Date)", datetime.now())

col_h, col_m = st.sidebar.columns(2)
# Accounting
s1 = col_h.number_input("Acc (h)", 0, 24, key="s1h") + (col_m.number_input("Acc (m)", 0, 59, key="s1m") / 60)
# BS
s2 = col_h.number_input("BS (h)", 0, 24, key="s2h") + (col_m.number_input("BS (m)", 0, 59, key="s2m") / 60)
# Sub 3
s3 = col_h.number_input(f"{sub3_name} (h)", 0, 24, key="s3h") + (col_m.number_input(f"{sub3_name} (m)", 0, 59, key="s3m") / 60)

if st.sidebar.button("SAVE DAILY DATA", use_container_width=True):
    if (s1 + s2 + s3) > 0:
        conn = sqlite3.connect('study_tracker_v4.db')
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO study_logs (date, sub1_h, sub2_h, sub3_h) 
                          VALUES(?, ?, ?, ?) 
                          ON CONFLICT(date) DO UPDATE SET 
                          sub1_h=excluded.sub1_h, sub2_h=excluded.sub2_h, sub3_h=excluded.sub3_h''', 
                       (str(entry_date), s1, s2, s3))
        conn.commit(); conn.close()
        st.sidebar.success(f"{entry_date} දත්ත සුරැකිනු ලැබුවා!")
        st.rerun()
    else:
        st.sidebar.warning("කරුණාකර අවම වශයෙන් විෂයයකට කාලය ඇතුළත් කරන්න.")

# --- Main Dashboard Logic ---
conn = sqlite3.connect('study_tracker_v4.db')
all_df = pd.read_sql_query("SELECT * FROM study_logs", conn)
conn.close()

if not all_df.empty:
    # Date column එක date object එකක් බවට හැරවීම
    all_df['date'] = pd.to_datetime(all_df['date']).dt.date
    
    # තෝරාගත් දින 7 පරාසය තුළ ඇති දත්ත පමණක් පෙරීම (Filtering)
    mask = (all_df['date'] >= start_date) & (all_df['date'] <= end_date)
    df = all_df.loc[mask].sort_values('date')

    # 1. Top Metrics (මුළු සතියේ සාරාංශය)
    total_hours = df[['sub1_h', 'sub2_h', 'sub3_h']].sum().sum()
    avg_per_day = total_hours / 7  # සතියකට දින 7ක් ඇති බැවින්

    m1, m2, m3 = st.columns(3)
    m1.metric("සතියේ මුළු පැය (Total)", f"{total_hours:.1f} h")
    m2.metric("දිනකට සාමාන්‍යය (Avg)", f"{avg_per_day:.1f} h")
    m3.metric("දත්ත ඇති දින ගණන", f"{len(df)} / 7")

    st.divider()

    # 2. Subject-wise Totals (විෂය අනුව එකතුව)
    st.subheader("විෂය අනුව සතිපතා එකතුව (Subject Totals)")
    s1_t, s2_t, s3_t = df['sub1_h'].sum(), df['sub2_h'].sum(), df['sub3_h'].sum()
    
    c1, c2, c3 = st.columns(3)
    c1.info(f"**Accounting**\n\nTotal: {s1_t:.1f} h")
    c2.info(f"**Business Studies**\n\nTotal: {s2_t:.1f} h")
    c3.info(f"**{sub3_name}**\n\nTotal: {s3_t:.1f} h")

    st.divider()

    # 3. Weekly Chart (ප්‍රස්ථාරය)
    st.subheader(f"විශ්ලේෂණය: {start_date} සිට {end_date}")
    if not df.empty:
        fig, ax = plt.subplots(figsize=(12, 5))
        df.plot(kind='bar', x='date', ax=ax, color=['#2ecc71', '#3498db', '#e67e22'], width=0.8)
        ax.set_ylabel("Hours")
        ax.legend(["Accounting", "Business Studies", sub3_name])
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.warning("තෝරාගත් කාල සීමාව සඳහා දත්ත කිසිවක් නැත.")

    # 4. Weekly Feedback (ප්‍රතිචාර)
    if len(df) >= 1: # දත්ත එකක් හෝ තිබේ නම් පෙන්වයි
        st.subheader("ප්‍රගතිය (Weekly Progress)")
        if total_hours < 40:
            st.error(f"ඔබේ සතියේ එකතුව {total_hours:.1f}h කි. ඉලක්කය සපුරා ගැනීමට තව මහන්සි වන්න! 😟")
        elif total_hours <= 60:
            st.success(f"ඔබේ සතියේ එකතුව {total_hours:.1f}h කි. ඉතා හොඳයි, දිගටම කරගෙන යන්න! 👍")
        else:
            st.warning(f"ඔබේ සතියේ එකතුව {total_hours:.1f}h කි. සුපිරි වැඩක්! 🔥🚀")
else:
    st.info("පද්ධතියේ දත්ත කිසිවක් නැත. පසෙකින් ඇති පුවරුවෙන් අද දින දත්ත ඇතුළත් කරන්න.")

# Reset Button
st.sidebar.divider()
if st.sidebar.button("🗑️ DELETE ALL DATA"):
    conn = sqlite3.connect('study_tracker_v4.db')
    conn.execute("DELETE FROM study_logs")
    conn.commit(); conn.close()
    st.rerun()