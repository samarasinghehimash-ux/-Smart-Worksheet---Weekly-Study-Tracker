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
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_prefs 
                          (username TEXT PRIMARY KEY, stream TEXT, sub1 TEXT, sub2 TEXT, sub3 TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS study_logs 
                          (username TEXT, date TEXT, stream TEXT, 
                           sub1_name TEXT, sub1_h REAL, 
                           sub2_name TEXT, sub2_h REAL, 
                           sub3_name TEXT, sub3_h REAL, UNIQUE(username, date))''')
        conn.commit()

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return make_hashes(password) == hashed_text

init_db()

# --- Page Config ---
st.set_page_config(page_title="A/L Study Tracker Pro", layout="wide")

# --- UI Styles ---
st.markdown("""
    <style>
    .main-title { font-size: 2.5rem !important; font-weight: 800 !important; text-align: center; color: #2d3436; }
    .teacher-name { text-align: center; font-size: 1rem; color: #636e72; margin-bottom: 25px; }
    .subject-card { 
        padding: 20px; border-radius: 15px; border: 1px solid #eee;
        border-top: 6px solid #0984e3; text-align: center; background: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .sub-value { font-size: 2rem; font-weight: 800; color: #0984e3; }
    [data-testid="stMetric"] { background-color: #f8f9fa; border: 1px solid #dfe6e9; padding: 15px; border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

SUBJECTS_DATA = {
    "Commerce": ["Accounting", "Business Studies", "Economics", "ICT"],
    "Physical Science (Maths)": ["Combined Maths", "Physics", "Chemistry", "ICT"],
    "Biological Science (Bio)": ["Biology", "Chemistry", "Physics", "Agricultural Science"],
    "Arts": ["Sinhala", "History", "Logic", "Political Science", "Geography", "Economics", "ICT"],
    "Technology": ["SFT", "Engineering Tech", "Bio Systems Tech", "ICT"]
}

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- Sidebar (Access, Calendar & Data Entry) ---
with st.sidebar:
    st.header("🔐 ගිණුම")
    if not st.session_state.logged_in:
        auth_mode = st.radio("තෝරන්න", ["Login", "Register"])
        u_in = st.text_input("පරිශීලක නාමය")
        p_in = st.text_input("මුරපදය", type='password')
        
        if st.button("තහවුරු කරන්න"):
            with sqlite3.connect('alevel_tracker_final.db') as conn:
                if auth_mode == "Register":
                    try:
                        conn.execute("INSERT INTO users VALUES (?, ?)", (u_in, make_hashes(p_in)))
                        conn.commit()
                        st.success("රෙජිස්ටර් වීම සාර්ථකයි! දැන් Login වන්න.")
                    except: st.error("මෙම නම පද්ධතියේ ඇත.")
                else:
                    data = conn.execute('SELECT password FROM users WHERE username =?', (u_in,)).fetchone()
                    if data and check_hashes(p_in, data[0]):
                        st.session_state.logged_in, st.session_state.username = True, u_in
                        st.rerun()
                    else: st.error("වැරදි දත්තයකි.")
    else:
        st.success(f"පරිශීලක: {st.session_state.username}")
        if st.button("Log Out"):
            st.session_state.logged_in = False; st.rerun()
        
        st.divider()
        # --- Calendar & Entry Form ---
        st.subheader("📝 දත්ත ඇතුළත් කිරීම")
        entry_date = st.date_input("දිනය තෝරන්න", datetime.now())
        
        conn = sqlite3.connect('alevel_tracker_final.db')
        pref = conn.execute("SELECT * FROM user_prefs WHERE username=?", (st.session_state.username,)).fetchone()
        
        cur_stream = pref[1] if pref else "Commerce"
        stream = st.selectbox("විෂය ධාරාව", list(SUBJECTS_DATA.keys()), index=list(SUBJECTS_DATA.keys()).index(cur_stream))
        
        subs = []
        for i in range(1, 4):
            def_v = pref[i+1] if pref and pref[i+1] in SUBJECTS_DATA[stream] else SUBJECTS_DATA[stream][i-1]
            s = st.selectbox(f"විෂය {i}", SUBJECTS_DATA[stream], index=SUBJECTS_DATA[stream].index(def_v), key=f"side_s_{i}")
            subs.append(s)
            
        st.write("---")
        hrs_input = []
        for i in range(3):
            st.write(f"**{subs[i]}**")
            c1, c2 = st.columns(2)
            h = c1.number_input("පැය", 0, 24, key=f"side_h_{i}")
            m = c2.number_input("මිනි", 0, 59, key=f"side_m_{i}")
            hrs_input.append(h + (m/60))
            
        if st.button("දත්ත සුරකින්න (SAVE)"):
            conn.execute("INSERT OR REPLACE INTO user_prefs VALUES (?,?,?,?,?)", (st.session_state.username, stream, subs[0], subs[1], subs[2]))
            conn.execute('INSERT INTO study_logs VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(username, date) DO UPDATE SET sub1_h=excluded.sub1_h, sub2_h=excluded.sub2_h, sub3_h=excluded.sub3_h', 
                         (st.session_state.username, str(entry_date), stream, subs[0], hrs_input[0], subs[1], hrs_input[1], subs[2], hrs_input[2]))
            conn.commit()
            st.success(f"{entry_date} දත්ත සුරැකුණා!")
            st.rerun()

# --- Main Analytics Page ---
if st.session_state.logged_in:
    st.markdown('<p class="main-title">🎓 A/L Study Tracker Pro</p>', unsafe_allow_html=True)
    st.markdown('<div class="teacher-name">Concept by: <b>Plan Master Charaka Dhananjaya</b> | Dev: Hiratrix IT Solutions</div>', unsafe_allow_html=True)
    
    # සතියේ ආරම්භය (ඔබ Sidebar එකේ තෝරාගත් දින සිට දින 7ක්)
    st.subheader(f"📊 සතිපතා සාරාංශය ({entry_date} සිට ඉදිරියට දින 7ක්)")
    
    conn = sqlite3.connect('alevel_tracker_final.db')
    df = pd.read_sql_query(f"SELECT * FROM study_logs WHERE username='{st.session_state.username}'", conn)
    
    if not df.empty:
        df['date'] = pd.to_datetime(df['date']).dt.date
        # තෝරාගත් දිනය සහ එතැන් සිට දින 6ක් (මුළු දින 7)
        end_date = entry_date + timedelta(days=6)
        week_df = df[(df['date'] >= entry_date) & (df['date'] <= end_date)].sort_values('date')
        
        if not week_df.empty:
            total_h = week_df[['sub1_h', 'sub2_h', 'sub3_h']].sum().sum()
            
            # 1. Metrics (කොටු 3)
            m1, m2, m3 = st.columns(3)
            m1.metric("සතියේ මුළු පැය", f"{total_h:.1f} h")
            m2.metric("දිනක සාමාන්‍යය", f"{(total_h/7):.1f} h")
            m3.metric("සටහන් කළ දින", f"{len(week_df)}/7")
            
            # 2. Subject Summary Cards
            st.write("---")
            sc = st.columns(3)
            for i in range(3):
                v = week_df[f'sub{i+1}_h'].sum()
                sc[i].markdown(f'<div class="subject-card"><p><b>{subs[i]}</b></p><p class="sub-value">{v:.1f} h</p></div>', unsafe_allow_html=True)

            # 3. Grouped Bar Chart
            st.markdown("### 📈 ප්‍රගති ප්‍රස්ථාරය")
            fig, ax = plt.subplots(figsize=(12, 5))
            x = np.arange(len(week_df['date']))
            width = 0.25
            
            ax.bar(x - width, week_df['sub1_h'], width, label=subs[0], color='#2ecc71')
            ax.bar(x, week_df['sub2_h'], width, label=subs[1], color='#3498db')
            ax.bar(x + width, week_df['sub3_h'], width, label=subs[2], color='#f1c40f')
            
            ax.set_xticks(x)
            ax.set_xticklabels(week_df['date'].astype(str), rotation=30)
            ax.set_ylabel("පැය ගණන")
            ax.legend()
            st.pyplot(fig)
        else:
            st.info(f"{entry_date} සිට ඉදිරි සතිය සඳහා තවමත් දත්ත ඇතුළත් කර නැත.")
    else:
        st.warning("පද්ධතියේ දත්ත කිසිවක් නැත. Sidebar එකෙන් දත්ත ඇතුළත් කරන්න.")

    conn.close()