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

# --- UI Styles (එකම පසුබිම් වර්ණය සහ පැහැදිලි අකුරු) ---
st.markdown("""
    <style>
    /* මුළු පිටුවම සහ Sidebar එකම සුදු පැහැයට */
    .stApp, [data-testid="stSidebar"] { background-color: #FFFFFF !important; }
    
    /* Sidebar අකුරු කළු පැහැයට */
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label { color: #2d3436 !important; font-weight: bold; }
    
    .main-title { font-size: 2.8rem !important; font-weight: 800 !important; color: #2d3436; text-align: center; margin-bottom: 5px; }
    .teacher-name { text-align: center; font-size: 1rem; color: #636e72; margin-bottom: 25px; }
    
    /* Metrics Styles */
    [data-testid="stMetric"] {
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #dfe6e9;
    }

    /* විෂය කොටු (Cards) */
    .subject-card { 
        background: #ffffff; 
        padding: 20px; 
        border-radius: 15px; 
        border: 1px solid #eee;
        border-bottom: 6px solid #0984e3; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); 
        text-align: center;
    }
    .sub-name { color: #2d3436; font-size: 1.1rem; font-weight: bold; margin-bottom: 5px; }
    .sub-value { color: #0984e3; font-size: 2.2rem; font-weight: 800; }
    
    /* Feedback Box */
    .feedback-box { padding: 15px; border-radius: 12px; text-align: center; font-size: 1.2rem; font-weight: bold; margin-bottom: 25px; border: 2px solid; }
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

# --- Sidebar Logic ---
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

# --- Main Page Content ---
if st.session_state.logged_in:
    st.markdown('<p class="main-title">🎓 A/L Study Tracker Pro</p>', unsafe_allow_html=True)
    st.markdown('<div class="teacher-name">Concept by: <b>Plan Master Charaka Dhananjaya</b> | Developed by: <span style="color:#00b894; font-weight:bold;">Hiratrix IT Solutions</span></div>', unsafe_allow_html=True)
    
    conn = sqlite3.connect('alevel_tracker_final.db')
    pref = conn.execute("SELECT * FROM user_prefs WHERE username=?", (st.session_state.username,)).fetchone()
    
    with st.sidebar:
        st.divider()
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
                f_bg = "#e8f5e9" if total_h >= 40 else "#ffebee"
                f_txt = "#2e7d32" if total_h >= 40 else "#c62828"
                msg = "🔥 විශිෂ්ටයි! දිගටම කරගෙන යන්න." if total_h >= 40 else "⚠️ ඔබ තවමත් දුර්වල මට්ටමක සිටින්නේ. තව මහන්සි වෙන්න!"
                st.markdown(f'<div class="feedback-box" style="background-color: {f_bg}; color: {f_txt}; border-color: {f_txt};">{msg} (සතියේ පැය: {total_h:.1f})</div>', unsafe_allow_html=True)
                
                # --- Metrics Section (කොටු 3) ---
                m1, m2, m3 = st.columns(3)
                m1.metric("📅 සතියේ මුළු පැය", f"{total_h:.1f} h")
                m2.metric("📊 දිනකට සාමාන්‍යය", f"{(total_h/7):.1f} h")
                m3.metric("✅ සටහන් කළ දින", f"{len(week_df)}/7")
                
                # --- විෂය ප්‍රගතිය ---
                st.markdown("### 📚 විෂයන් අනුව ප්‍රගතිය")
                cols = st.columns(3)
                for i in range(3):
                    val = week_df[f'sub{i+1}_h'].sum()
                    cols[i].markdown(f"""
                        <div class="subject-card">
                            <div class="sub-name">{selected_subs[i]}</div>
                            <div class="sub-value">{val:.1f} h</div>
                        </div>
                    """, unsafe_allow_html=True)

                # --- Grouped Bar Chart (විෂයන් 3ට තීරු 3ක්) ---
                st.markdown("### 📈 ප්‍රගති ප්‍රස්ථාරය")
                fig, ax = plt.subplots(figsize=(12, 5))
                
                x = np.arange(len(week_df['date']))
                width = 0.25  # තීරු වල පළල
                
                # විෂයන් 3 සඳහා වෙන් වෙන්ව තීරු ඇඳීම
                ax.bar(x - width, week_df['sub1_h'], width, label=selected_subs[0], color='#00b894')
                ax.bar(x, week_df['sub2_h'], width, label=selected_subs[1], color='#0984e3')
                ax.bar(x + width, week_df['sub3_h'], width, label=selected_subs[2], color='#fdcb6e')
                
                ax.set_xticks(x)
                ax.set_xticklabels(week_df['date'].astype(str), rotation=45)
                ax.set_ylabel("පැය ගණන")
                ax.legend()
                ax.grid(axis='y', linestyle='--', alpha=0.7)
                
                st.pyplot(fig)
            else: st.info("මෙම සතිය සඳහා දත්ත කිසිවක් නැත.")
        else: st.warning("දත්ත ඇතුළත් කර නැත.")

    with tab1:
        cur_w = datetime.now().date() - timedelta(days=datetime.now().weekday())
        display_analytics(cur_w)
    with tab2:
        hist_date = st.date_input("සතිය ආරම්භය තෝරන්න", cur_w - timedelta(days=7))
        display_analytics(hist_date)

    conn.close()