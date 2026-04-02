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
        # විෂයන් ස්ථිරව තබා ගැනීමට නව වගුවක්
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

# --- UI Styles (CSS) ---
st.markdown("""
    <style>
    .main-title { font-size: 2.8rem !important; font-weight: 900 !important; color: #ffffff; text-align: center; margin-bottom: 10px; }
    div[data-testid="stMetric"] { background-color: #ffffff !important; padding: 15px; border-radius: 12px; border: 1px solid #ddd; }
    .subject-card { background-color: #ffffff; padding: 15px; border-radius: 12px; border-left: 10px solid #2ecc71; color: #000; text-align: center; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .feedback-box { padding: 18px; border-radius: 12px; text-align: center; font-size: 1.2rem; font-weight: bold; margin: 20px 0; border: 2px solid; }
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

# --- Access Control ---
st.sidebar.title("🔐 Access Control")
if not st.session_state.logged_in:
    auth_mode = st.sidebar.radio("තෝරන්න", ["Login", "Register"])
    u_in = st.sidebar.text_input("Username")
    p_in = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("තහවුරු කරන්න"):
        with sqlite3.connect('alevel_tracker_final.db') as conn:
            if auth_mode == "Register":
                try:
                    conn.execute("INSERT INTO users VALUES (?, ?)", (u_in, make_hashes(p_in)))
                    conn.commit(); st.sidebar.success("දැන් Login වන්න.")
                except: st.sidebar.error("නම දැනටමත් ඇත.")
            else:
                data = conn.execute('SELECT password FROM users WHERE username =?', (u_in,)).fetchone()
                if data and check_hashes(p_in, data[0]):
                    st.session_state.logged_in, st.session_state.username = True, u_in
                    st.rerun()
                else: st.sidebar.error("දත්ත වැරදියි.")
else:
    st.sidebar.success(f"පරිශීලක: {st.session_state.username}")
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False; st.rerun()

# --- Main App ---
if st.session_state.logged_in:
    st.markdown('<p class="main-title">🎓 A/L Smart Study Tracker Pro</p>', unsafe_allow_html=True)
    st.markdown("<div style='text-align: center;'>Developed by: <b style='color: #2ecc71;'>Hiratrix IT Solutions</b></div>", unsafe_allow_html=True)
    st.divider()

    conn = sqlite3.connect('alevel_tracker_final.db')
    
    # 1. පෙර තේරූ විෂයන් දත්ත ගබඩාවෙන් ලබා ගැනීම
    pref = conn.execute("SELECT * FROM user_prefs WHERE username=?", (st.session_state.username,)).fetchone()
    
    with st.sidebar:
        st.subheader("⚙️ විෂය සැකසුම්")
        # විෂය ධාරාව එකවරක් ඇතුළත් කළ පසු වෙනස් කිරීමට අවශ්‍ය නම් පමණක් පෙන්වයි
        current_stream = pref[1] if pref else list(SUBJECTS_DATA.keys())[0]
        stream = st.selectbox("විෂය ධාරාව", list(SUBJECTS_DATA.keys()), index=list(SUBJECTS_DATA.keys()).index(current_stream))
        
        selected_subs = []
        for i in range(1, 4):
            default_sub = pref[i+1] if pref and pref[i+1] in SUBJECTS_DATA[stream] else SUBJECTS_DATA[stream][i-1]
            s = st.selectbox(f"විෂය {i}", SUBJECTS_DATA[stream], index=SUBJECTS_DATA[stream].index(default_sub), key=f"sel_sub_{i}")
            selected_subs.append(s)
            
        if st.button("විෂයන් ස්ථිර කරන්න (Fix Subjects)"):
            conn.execute("INSERT OR REPLACE INTO user_prefs VALUES (?,?,?,?,?)", 
                         (st.session_state.username, stream, selected_subs[0], selected_subs[1], selected_subs[2]))
            conn.commit(); st.success("සැකසුම් සුරැකුණා!"); st.rerun()

        st.divider()
        st.subheader("📝 අද දින දත්ත")
        sel_date = st.date_input("දිනය", datetime.now())
        
        hrs_input = []
        for i in range(1, 4):
            st.write(f"**{selected_subs[i-1]}**")
            c1, c2 = st.columns(2)
            # Reset වීමේදී Error එක මගහැරීමට value එක කෙලින්ම ලබා නොදී key භාවිතා කරයි
            h = c1.number_input("පැය", 0, 24, key=f"h_in_{i}")
            m = c2.number_input("මිනිත්තු", 0, 59, key=f"m_in_{i}")
            hrs_input.append(h + (m/60))

        if st.button("දත්ත සුරකින්න (SAVE)"):
            conn.execute('INSERT INTO study_logs VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(username, date) DO UPDATE SET sub1_h=excluded.sub1_h, sub2_h=excluded.sub2_h, sub3_h=excluded.sub3_h', 
                         (st.session_state.username, str(sel_date), stream, selected_subs[0], hrs_input[0], selected_subs[1], hrs_input[1], selected_subs[2], hrs_input[2]))
            conn.commit()
            # Input Reset කිරීම (Session state හරහා බිංදු කිරීම)
            for i in range(1, 4):
                st.session_state[f"h_in_{i}"] = 0
                st.session_state[f"m_in_{i}"] = 0
            st.rerun()

        st.sidebar.subheader("🗑️ දත්ත මකන්න")
        if st.sidebar.button("සියලුම දත්ත මකන්න"):
            conn.execute(f"DELETE FROM study_logs WHERE username='{st.session_state.username}'")
            conn.commit(); st.rerun()

    # --- Display Area ---
    tab1, tab2 = st.tabs(["📊 වර්තමාන ප්‍රගතිය", "🔍 පැරණි වාර්තා"])
    
    def render_stats(start_date):
        end_date = start_date + timedelta(days=6)
        df = pd.read_sql_query(f"SELECT * FROM study_logs WHERE username='{st.session_state.username}'", conn)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date']).dt.date
            week_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)].sort_values('date')
            
            if not week_df.empty:
                total_h = week_df[['sub1_h', 'sub2_h', 'sub3_h']].sum().sum()
                # Feedback
                color = "#e8f5e9" if total_h >= 40 else "#ffebee"
                text_color = "#2e7d32" if total_h >= 40 else "#c62828"
                msg = "🎉 නියමයි! හොඳ ප්‍රගතියක්." if total_h >= 40 else "😟 තව මහන්සි වෙන්න!"
                st.markdown(f'<div class="feedback-box" style="background-color: {color}; color: {text_color}; border-color: {text_color};">{msg} (සතියේ පැය: {total_h:.1f})</div>', unsafe_allow_html=True)
                
                # Metrics
                m1, m2, m3 = st.columns(3)
                m1.metric("📅 මුළු පැය", f"{total_h:.1f} h")
                m2.metric("📊 සාමාන්‍යය", f"{(total_h/7):.1f} h")
                m3.metric("✅ දින", f"{len(week_df)} / 7")
                
                # Subject Cards
                st.markdown("### 📚 විෂයන් අනුව පැය")
                sc = st.columns(3)
                for i in range(3):
                    val = week_df[f'sub{i+1}_h'].sum()
                    sc[i].markdown(f"<div class='subject-card'><small>{selected_subs[i]}</small><br><span style='font-size: 1.5rem;'>{val:.1f} h</span></div>", unsafe_allow_html=True)
                
                # Graph
                st.markdown("### 📈 ප්‍රස්ථාරය")
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.bar(week_df['date'].astype(str), week_df['sub1_h'], label=selected_subs[0])
                ax.bar(week_df['date'].astype(str), week_df['sub2_h'], bottom=week_df['sub1_h'], label=selected_subs[1])
                ax.bar(week_df['date'].astype(str), week_df['sub3_h'], bottom=week_df['sub1_h']+week_df['sub2_h'], label=selected_subs[2])
                plt.xticks(rotation=45); ax.legend(); st.pyplot(fig)
            else: st.info("දත්ත නැත.")

    with tab1:
        w_start = datetime.now().date() - timedelta(days=datetime.now().weekday())
        render_stats(w_start)
        
    with tab2:
        h_date = st.date_input("සතියේ ආරම්භය", w_start - timedelta(days=7))
        render_stats(h_date)

    conn.close()