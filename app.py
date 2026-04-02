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

# --- UI Styles (එකම සුදු පසුබිම සහ දින දර්ශන විලාසිතා) ---
st.markdown("""
    <style>
    /* මුළු පිටුවම සහ Sidebar එකම සුදු පැහැයට */
    .stApp, [data-testid="stSidebar"] { background-color: #FFFFFF !important; }
    
    /* අකුරු වල වර්ණ පාලනය */
    h1, h2, h3, p, label, .stMarkdown { color: #2d3436 !important; }
    
    .main-title { font-size: 2.5rem !important; font-weight: 800 !important; color: #2d3436; text-align: center; }
    .teacher-name { text-align: center; font-size: 1rem; color: #636e72; margin-bottom: 20px; }

    /* Metrics & Cards */
    [data-testid="stMetric"] {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #dfe6e9;
    }
    .subject-card { 
        background: #ffffff; 
        padding: 15px; 
        border-radius: 12px; 
        border: 1px solid #eee;
        border-top: 5px solid #0984e3; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); 
        text-align: center;
    }
    .sub-value { color: #0984e3; font-size: 2rem; font-weight: 800; }
    
    /* Calendar widget style */
    .stDateInput div[data-baseweb="input"] { background-color: #f1f2f6 !important; border-radius: 10px; }
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

# --- Sidebar Logic ---
with st.sidebar:
    st.header("🔐 ගිණුමට පිවිසෙන්න")
    if not st.session_state.logged_in:
        u_in = st.text_input("පරිශීලක නාමය")
        p_in = st.text_input("මුරපදය", type='password')
        if st.button("Login"):
            with sqlite3.connect('alevel_tracker_final.db') as conn:
                data = conn.execute('SELECT password FROM users WHERE username =?', (u_in,)).fetchone()
                if data and check_hashes(p_in, data[0]):
                    st.session_state.logged_in, st.session_state.username = True, u_in
                    st.rerun()
                else: st.error("වැරදියි. නැවත උත්සාහ කරන්න.")
    else:
        st.success(f"පිවිසී ඇත: {st.session_state.username}")
        if st.button("Log Out"):
            st.session_state.logged_in = False; st.rerun()

# --- Main Page Content ---
if st.session_state.logged_in:
    st.markdown('<p class="main-title">🎓 A/L Smart Study Tracker Pro</p>', unsafe_allow_html=True)
    st.markdown('<div class="teacher-name">Concept by: <b>Plan Master Charaka Dhananjaya</b> | Developed by: <span style="color:#00b894; font-weight:bold;">Hiratrix IT Solutions</span></div>', unsafe_allow_html=True)
    
    conn = sqlite3.connect('alevel_tracker_final.db')
    pref = conn.execute("SELECT * FROM user_prefs WHERE username=?", (st.session_state.username,)).fetchone()
    
    with st.sidebar:
        st.divider()
        st.subheader("📅 දින දර්ශනය (Calendar)")
        target_date = st.date_input("දිනය තෝරන්න", datetime.now())
        
        st.divider()
        st.subheader("⚙️ විෂය සැකසුම්")
        cur_stream = pref[1] if pref else "Commerce"
        stream = st.selectbox("විෂය ධාරාව", list(SUBJECTS_DATA.keys()), index=list(SUBJECTS_DATA.keys()).index(cur_stream))
        
        selected_subs = []
        for i in range(1, 4):
            def_sub = pref[i+1] if pref and pref[i+1] in SUBJECTS_DATA[stream] else SUBJECTS_DATA[stream][i-1]
            s = st.selectbox(f"විෂය {i}", SUBJECTS_DATA[stream], index=SUBJECTS_DATA[stream].index(def_sub), key=f"sub_cfg_{i}")
            selected_subs.append(s)
            
        if st.button("සැකසුම් සුරකින්න"):
            conn.execute("INSERT OR REPLACE INTO user_prefs VALUES (?,?,?,?,?)", (st.session_state.username, stream, selected_subs[0], selected_subs[1], selected_subs[2]))
            conn.commit(); st.rerun()

    # --- Content Tabs ---
    tab1, tab2 = st.tabs(["📝 අද දින සටහන", "📊 ප්‍රගති වාර්තාව"])

    with tab1:
        st.subheader(f"📍 {target_date} දින අධ්‍යයන කාලය ඇතුළත් කරන්න")
        col_inputs = st.columns(3)
        hrs_data = []
        for i in range(3):
            with col_inputs[i]:
                st.markdown(f"**{selected_subs[i]}**")
                h = st.number_input("පැය", 0, 24, key=f"h_{i}")
                m = st.number_input("මිනිත්තු", 0, 59, key=f"m_{i}")
                hrs_data.append(h + (m/60))
        
        if st.button("දත්ත සුරකින්න (SAVE)"):
            conn.execute('INSERT INTO study_logs VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(username, date) DO UPDATE SET sub1_h=excluded.sub1_h, sub2_h=excluded.sub2_h, sub3_h=excluded.sub3_h', 
                         (st.session_state.username, str(target_date), stream, selected_subs[0], hrs_data[0], selected_subs[1], hrs_data[1], selected_subs[2], hrs_data[2]))
            conn.commit(); st.success(f"{target_date} දත්ත සාර්ථකව සුරැකුණා!")

    with tab2:
        # සතිපතා දත්ත ගණනය
        start_w = target_date - timedelta(days=target_date.weekday())
        df = pd.read_sql_query(f"SELECT * FROM study_logs WHERE username='{st.session_state.username}'", conn)
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date']).dt.date
            week_df = df[(df['date'] >= start_w) & (df['date'] <= start_w + timedelta(days=6))].sort_values('date')
            
            if not week_df.empty:
                total_h = week_df[['sub1_h', 'sub2_h', 'sub3_h']].sum().sum()
                
                # Metrics (කොටු 3)
                m1, m2, m3 = st.columns(3)
                m1.metric("📅 සතියේ මුළු පැය", f"{total_h:.1f} h")
                m2.metric("📊 දිනක සාමාන්‍යය", f"{(total_h/7):.1f} h")
                m3.metric("✅ වාර්තා කළ දින", f"{len(week_df)}/7")
                
                # විෂය අනුව ප්‍රගතිය (Cards)
                st.markdown("---")
                cols = st.columns(3)
                for i in range(3):
                    v = week_df[f'sub{i+1}_h'].sum()
                    cols[i].markdown(f'<div class="subject-card"><p class="sub-name">{selected_subs[i]}</p><p class="sub-value">{v:.1f} h</p></div>', unsafe_allow_html=True)

                # Grouped Bar Chart (තීරු 3 බැගින්)
                st.markdown("### 📈 සතිපතා ප්‍රගති ප්‍රස්ථාරය")
                fig, ax = plt.subplots(figsize=(12, 5))
                x = np.arange(len(week_df['date']))
                w = 0.25
                
                ax.bar(x - w, week_df['sub1_h'], w, label=selected_subs[0], color='#00b894')
                ax.bar(x, week_df['sub2_h'], w, label=selected_subs[1], color='#0984e3')
                ax.bar(x + w, week_df['sub3_h'], w, label=selected_subs[2], color='#fdcb6e')
                
                ax.set_xticks(x)
                ax.set_xticklabels(week_df['date'].astype(str), rotation=30)
                ax.legend()
                st.pyplot(fig)
            else: st.info("මෙම සතිය සඳහා තවමත් දත්ත ඇතුළත් කර නැත.")
        else: st.warning("දත්ත කිසිවක් සොයාගත නොහැක.")

    conn.close()