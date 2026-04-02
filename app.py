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

# --- UI Styles (කලින් තිබූ සාර්ථක පෙනුම නැවත ලබා ගැනීම) ---
st.markdown("""
    <style>
    /* පිරිසිදු සුදු පසුබිම */
    .stApp { background-color: #FFFFFF !important; }
    
    .main-title { font-size: 2.8rem !important; font-weight: 800 !important; color: #1e272e; text-align: center; margin-bottom: 2px; }
    .teacher-name { text-align: center; font-size: 1rem; color: #485460; margin-bottom: 25px; }
    .business-name { color: #05c46b; font-weight: bold; }
    
    /* Metrics (කොටු 3) */
    [data-testid="stMetric"] {
        background-color: #f1f2f6;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #dfe4ea;
    }
    [data-testid="stMetricValue"] { color: #2f3542 !important; font-size: 1.8rem !important; }
    [data-testid="stMetricLabel"] { color: #57606f !important; font-weight: bold !important; }

    /* විෂය ප්‍රගති කොටු (Compact Subject Cards) */
    .subject-card { 
        background: #ffffff; 
        padding: 15px; 
        border-radius: 12px; 
        border-top: 5px solid #3498db; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
        text-align: center;
        border: 1px solid #eee;
    }
    .sub-label { color: #7f8c8d; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; }
    .sub-name { color: #2c3e50; font-size: 1rem; font-weight: bold; margin: 5px 0; display: block; }
    .sub-value { color: #3498db; font-size: 1.6rem; font-weight: 800; }

    /* Feedback Box */
    .feedback-box { padding: 15px; border-radius: 10px; text-align: center; font-size: 1.1rem; font-weight: bold; margin-bottom: 20px; border: 2px solid; }
    
    /* Tabs & Text Fix */
    .stTabs [data-baseweb="tab"] { font-size: 1rem; font-weight: bold; color: #2f3542; }
    h3 { color: #2f3542 !important; font-size: 1.4rem !important; margin-top: 20px !important; }
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
with st.sidebar:
    st.title("🔐 Access Control")
    if not st.session_state.logged_in:
        auth_mode = st.radio("තෝරන්න", ["Login", "Register"])
        u_in = st.text_input("Username")
        p_in = st.text_input("Password", type='password')
        if st.button("තහවුරු කරන්න"):
            with sqlite3.connect('alevel_tracker_final.db') as conn:
                if auth_mode == "Register":
                    try:
                        conn.execute("INSERT INTO users VALUES (?, ?)", (u_in, make_hashes(p_in)))
                        conn.commit(); st.success("සාර්ථකයි! Login වන්න.")
                    except: st.error("නම දැනටමත් ඇත.")
                else:
                    data = conn.execute('SELECT password FROM users WHERE username =?', (u_in,)).fetchone()
                    if data and check_hashes(p_in, data[0]):
                        st.session_state.logged_in, st.session_state.username = True, u_in
                        st.rerun()
                    else: st.error("දත්ත වැරදියි.")
    else:
        st.success(f"පරිශීලක: {st.session_state.username}")
        if st.button("Log Out"):
            st.session_state.logged_in = False; st.rerun()

# --- Main Interface ---
if st.session_state.logged_in:
    st.markdown('<p class="main-title">🎓 A/L Study Tracker Pro</p>', unsafe_allow_html=True)
    st.markdown('<div class="teacher-name">Concept by: <b>Plan Master Charaka Dhananjaya</b> | Developed by: <span class="business-name">Hiratrix IT Solutions</span></div>', unsafe_allow_html=True)
    
    conn = sqlite3.connect('alevel_tracker_final.db')
    pref = conn.execute("SELECT * FROM user_prefs WHERE username=?", (st.session_state.username,)).fetchone()
    
    with st.sidebar:
        st.subheader("⚙️ විෂය සැකසුම්")
        cur_stream = pref[1] if pref else list(SUBJECTS_DATA.keys())[0]
        stream = st.selectbox("විෂය ධාරාව", list(SUBJECTS_DATA.keys()), index=list(SUBJECTS_DATA.keys()).index(cur_stream))
        
        selected_subs = []
        for i in range(1, 4):
            def_sub = pref[i+1] if pref and pref[i+1] in SUBJECTS_DATA[stream] else SUBJECTS_DATA[stream][i-1]
            s = st.selectbox(f"විෂය {i}", SUBJECTS_DATA[stream], index=SUBJECTS_DATA[stream].index(def_sub), key=f"fixed_sub_{i}")
            selected_subs.append(s)
            
        if st.button("විෂයන් ස්ථිර කරන්න"):
            conn.execute("INSERT OR REPLACE INTO user_prefs VALUES (?,?,?,?,?)", (st.session_state.username, stream, selected_subs[0], selected_subs[1], selected_subs[2]))
            conn.commit(); st.rerun()

        st.divider()
        st.subheader("📝 දත්ත ඇතුළත් කරන්න")
        sel_date = st.date_input("දිනය", datetime.now())
        
        hrs_input = []
        for i in range(1, 4):
            st.write(f"**{selected_subs[i-1]}**")
            c1, c2 = st.columns(2)
            h = c1.number_input("පැය", 0, 24, key=f"h_in_{i}")
            m = c2.number_input("මිනිත්තු", 0, 59, key=f"m_in_{i}")
            hrs_input.append(h + (m/60))

        if st.button("දත්ත සුරකින්න (SAVE)"):
            conn.execute('INSERT INTO study_logs VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(username, date) DO UPDATE SET sub1_h=excluded.sub1_h, sub2_h=excluded.sub2_h, sub3_h=excluded.sub3_h', 
                         (st.session_state.username, str(sel_date), stream, selected_subs[0], hrs_input[0], selected_subs[1], hrs_input[1], selected_subs[2], hrs_input[2]))
            conn.commit(); st.success("දත්ත සුරැකුණා!"); st.rerun()

        st.sidebar.divider()
        st.sidebar.subheader("🗑️ දත්ත කළමනාකරණය")
        if st.sidebar.button("🗑️ අද දත්ත මකන්න"):
            conn.execute(f"DELETE FROM study_logs WHERE username='{st.session_state.username}' AND date='{sel_date}'")
            conn.commit(); st.rerun()
        if st.sidebar.button("🚨 සතියේ දත්ත මකන්න"):
            w_start = sel_date - timedelta(days=sel_date.weekday())
            conn.execute(f"DELETE FROM study_logs WHERE username='{st.session_state.username}' AND date >= '{w_start}'")
            conn.commit(); st.rerun()
        if st.sidebar.button("🔥 සියලුම දත්ත මකන්න"):
            conn.execute(f"DELETE FROM study_logs WHERE username='{st.session_state.username}'")
            conn.commit(); st.rerun()

    # --- Analytics Tabs ---
    tab1, tab2 = st.tabs(["📊 වර්තමාන සතිය", "🔍 පැරණි වාර්තා"])

    def display_analytics(start_date):
        df = pd.read_sql_query(f"SELECT * FROM study_logs WHERE username='{st.session_state.username}'", conn)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date']).dt.date
            week_df = df[(df['date'] >= start_date) & (df['date'] <= start_date + timedelta(days=6))].sort_values('date')
            
            if not week_df.empty:
                total_h = week_df[['sub1_h', 'sub2_h', 'sub3_h']].sum().sum()
                
                # Feedback Box
                f_bg = "#d4edda" if total_h >= 40 else "#f8d7da"
                f_txt = "#155724" if total_h >= 40 else "#721c24"
                msg = "🔥 විශිෂ්ටයි! දිගටම කරගෙන යන්න." if total_h >= 40 else "⚠️ ඔබ තවමත් දුර්වල මට්ටමක සිටින්නේ. තව මහන්සි වෙන්න!"
                st.markdown(f'<div class="feedback-box" style="background-color: {f_bg}; color: {f_txt}; border-color: {f_txt};">{msg} (සතියේ පැය: {total_h:.1f})</div>', unsafe_allow_html=True)
                
                # --- Metrics (අතුරුදහන් වූ කොටු 3) ---
                m1, m2, m3 = st.columns(3)
                m1.metric("📅 සතියේ මුළු පැය", f"{total_h:.1f} h")
                m2.metric("📊 දිනකට සාමාන්‍යය", f"{(total_h/7):.1f} h")
                m3.metric("✅ සටහන් කළ දින", f"{len(week_df)}/7")
                
                # --- විෂය ප්‍රගතිය (කුඩා කොටු) ---
                st.markdown("### 📚 විෂයන් අනුව ප්‍රගතිය")
                cols = st.columns(3)
                for i in range(3):
                    val = week_df[f'sub{i+1}_h'].sum()
                    cols[i].markdown(f"""
                        <div class="subject-card">
                            <div class="sub-label">SUBJECT 0{i+1}</div>
                            <div class="sub-name">{selected_subs[i]}</div>
                            <div class="sub-value">{val:.1f} h</div>
                        </div>
                    """, unsafe_allow_html=True)

                # --- ප්‍රස්ථාරය ---
                st.markdown("### 📈 ප්‍රගති ප්‍රස්ථාරය")
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.bar(week_df['date'].astype(str), week_df['sub1_h'], label=selected_subs[0], color='#2ecc71')
                ax.bar(week_df['date'].astype(str), week_df['sub2_h'], bottom=week_df['sub1_h'], label=selected_subs[1], color='#3498db')
                ax.bar(week_df['date'].astype(str), week_df['sub3_h'], bottom=week_df['sub1_h']+week_df['sub2_h'], label=selected_subs[2], color='#f1c40f')
                plt.xticks(rotation=45)
                ax.legend()
                st.pyplot(fig)
            else: st.info("දත්ත කිසිවක් නැත.")
        else: st.warning("දත්ත ඇතුළත් කර නැත.")

    with tab1:
        cur_w = datetime.now().date() - timedelta(days=datetime.now().weekday())
        display_analytics(cur_w)
    with tab2:
        hist_date = st.date_input("සතිය ආරම්භය තෝරන්න", cur_w - timedelta(days=7))
        display_analytics(hist_date)

    conn.close()