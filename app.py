import streamlit as st
import google.generativeai as genai
import json
import os
import time
from datetime import date, timedelta
import pandas as pd

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Axiom Academy", page_icon="🦉", layout="wide", initial_sidebar_state="expanded")

# API KEY
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

# --- SISTEM DATABASE LOKAL ---
DB_FILE = 'database_user.json'

def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}}
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

db = load_db()

# --- INISIALISASI SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'current_user' not in st.session_state: st.session_state.current_user = None
if 'q_index' not in st.session_state: st.session_state.q_index = 0
if 'mistakes' not in st.session_state: st.session_state.mistakes = 0
if 'active_lesson' not in st.session_state: st.session_state.active_lesson = None
if 'chat_history' not in st.session_state: 
    st.session_state.chat_history = [{"role": "assistant", "content": "Genie: Halo! Saya Axiom Genie. Ada pertanyaan tentang NLP hari ini?"}]

# --- DATABASE SOAL (CONTENT) ---
MATERI_SOAL = {
    "ch1_p1": [
        {"q": "Apa tujuan utama dari NLP (Natural Language Processing)?", "options": ["Mendinginkan sistem secara otomatis", "Membuat komputer memahami bahasa manusia", "Meningkatkan frekuensi sinyal"], "ans": "Membuat komputer memahami bahasa manusia"},
        {"q": "Dalam NLP, proses memecah kalimat menjadi potongan kata tunggal disebut?", "options": ["Tokenization", "Stemming", "Filtering"], "ans": "Tokenization"},
        {"q": "Manakah yang merupakan contoh implementasi NLP di bidang teknik?", "options": ["Sistem Rem Otomatis", "Voice Control untuk Smart Relay", "Solder Otomatis"], "ans": "Voice Control untuk Smart Relay"},
        {"q": "Mengubah kata 'Berjalan', 'Jalan', 'Menjalankan' ke bentuk dasar 'Jalan' disebut?", "options": ["Lemmatization/Stemming", "Translation", "Parsing"], "ans": "Lemmatization/Stemming"},
        {"q": "Mengapa mikrokontroler tidak bisa langsung membaca input teks dari pengguna?", "options": ["Karena butuh konverter ADC", "Karena mikrokontroler hanya memproses instruksi biner/angka", "Karena RAM selalu penuh"], "ans": "Karena mikrokontroler hanya memproses instruksi biner/angka"}
    ],
    "ch2_p1": [
        {"q": "Teknisi menulis: 'Arus pada motor A tidak stabil dan suhunya 80C'. Teknik NLP apa untuk mengekstrak angka suhu?", "options": ["Named Entity Recognition (NER)", "Stopword Removal", "Text Generation"], "ans": "Named Entity Recognition (NER)"},
        {"q": "Jika kita ingin AI mendeteksi apakah log error bermakna 'Kritis' atau 'Aman', kita menggunakan?", "options": ["Sentiment Analysis / Text Classification", "Image Processing", "Speech to Text"], "ans": "Sentiment Analysis / Text Classification"},
        {"q": "Kata mana yang sebaiknya dihapus (Stopwords) sebelum menganalisis log sistem?", "options": ["Tegangan", "Dan, Di, Ke, Dari", "Resistansi"], "ans": "Dan, Di, Ke, Dari"},
        {"q": "Mengapa analisis log berbasis NLP lebih efisien?", "options": ["Because AI bisa membaca jutaan baris data log dalam hitungan detik", "Because AI tidak butuh listrik", "Because laporan selalu terformat JSON"], "ans": "Karena AI bisa membaca jutaan baris data log dalam hitungan detik"},
        {"q": "Library Python yang sangat populer untuk memproses teks dasar adalah?", "options": ["NLTK / SpaCy", "Matplotlib", "OpenCV"], "ans": "NLTK / SpaCy"}
    ],
    "ch3_p1": [
        {"q": "Setelah NLP memahami perintah 'Nyalakan pompa', langkah selanjutnya di sisi hardware adalah?", "options": ["Mengirim sinyal HIGH ke pin GPIO/Relay", "Menghitung nilai resistor", "Menulis file teks"], "ans": "Mengirim sinyal HIGH ke pin GPIO/Relay"},
        {"q": "Format data apa yang paling umum digunakan untuk mengirim instruksi dari Server NLP ke ESP32?", "options": ["MP4", "JSON", "DOCX"], "ans": "JSON"},
        {"q": "Jika pengguna berkata 'Tolong nyalakan lampu', dan 'Lampu nyala dong', AI memetakannya ke tindakan yang sama. Ini disebut?", "options": ["Intent Classification", "Hardware Interrupt", "Pulse Width Modulation"], "ans": "Intent Classification"},
        {"q": "Di mana model LLM yang berat sebaiknya dijalankan?", "options": ["Di dalam mikrokontroler Arduino Uno", "Di Server/Cloud, lalu hasilnya dikirim ke hardware", "Di dalam sensor tegangan"], "ans": "Di Server/Cloud, lalu hasilnya dikirim ke hardware"},
        {"q": "Tantangan terbesar menggunakan perintah suara (Voice NLP) di lingkungan pabrik adalah?", "options": ["Sistem IoT tidak mendukung suara", "Noise/Kebisingan latar belakang yang mengganggu mikrofon", "Kabel terlalu pendek"], "ans": "Noise/Kebisingan latar belakang yang mengganggu mikrofon"}
    ]
}

# --- PENGATURAN TEMA (CSS) ---
st.markdown("""
<style>
    .stApp { background-color: #131F24; color: #FFFFFF; font-family: 'Nunito', sans-serif; }
    .stMarkdown, p, h1, h2, h3, h4, h5, h6, label, span { color: #FFFFFF !important; }
    
    [data-testid="stSidebarCollapseButton"] { display: none !important; }
    section[data-testid="stSidebar"] { background-color: #0A1014; border-right: 2px solid #202F36; min-width: 250px !important; }
    
    .sidebar-logo { font-size: 2.2rem; font-weight: 900; color: #1CB0F6; text-align: center; margin-bottom: 20px; letter-spacing: 2px;}
    
    .header-banner { 
        background: linear-gradient(90deg, #CE82FF 0%, #1CB0F6 100%); 
        padding: 25px; border-radius: 15px; margin-bottom: 20px; text-align: center; 
    }
    .header-banner h2 { font-size: 1.8rem; margin: 0 0 10px 0; padding: 0; line-height: 1.3;}
    
    .metric-box { 
        font-size: 1.2rem; font-weight: bold; padding: 8px 15px; 
        background-color: #202F36; border-radius: 12px; border: 2px solid #37464F; 
        display: flex; align-items: center; justify-content: center;
        white-space: nowrap;
    }
    
    .course-card { background-color: #202F36; padding: 20px; border-radius: 15px; border: 2px solid #37464F; margin-bottom: 15px; }
    .locked-card { opacity: 0.4; pointer-events: none; }
    
    @keyframes pulseGlow {
        0% { box-shadow: 0 0 0 0 rgba(255, 0, 122, 0.7); }
        70% { box-shadow: 0 0 0 15px rgba(255, 0, 122, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 0, 122, 0); }
    }
    div[data-testid="stPopover"] {
        position: fixed !important; bottom: 30px !important; right: 30px !important; width: fit-content !important; z-index: 99999;
    }
    div[data-testid="stPopover"] > button {
        border-radius: 50px !important; padding: 12px 30px !important;
        background: linear-gradient(135deg, #FF007A, #7A00FF) !important;
        color: white !important; border: 2px solid #FFFFFF !important;
        font-weight: 900; font-size: 1.1rem; animation: pulseGlow 2s infinite; width: fit-content !important;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNGSI UPDATE STREAK ---
def check_and_update_streak(username):
    user = db["users"][username]
    today = str(date.today())
    last_played = user.get("last_played", "")
    
    if last_played != today:
        yesterday = str(date.today() - timedelta(days=1))
        if last_played == yesterday:
            user["streak"] += 1
        else:
            user["streak"] = 1
        user["last_played"] = today
        save_db(db)

# --- FUNGSI AXIOM GENIE ---
def render_genie():
    with st.popover("静态 Tanya Genie"):
        st.markdown("**Asisten AI & NLP**")
        chat_container = st.container(height=350)
        with chat_container:
            for msg in st.session_state.chat_history:
                st.markdown(f"**{'Anda' if msg['role']=='user' else 'Genie'}:** {msg['content']}")

        if prompt := st.chat_input("Ketik pertanyaan..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            try:
                model = genai.GenerativeModel("gemini-2.5-flash", system_instruction="Anda Axiom Genie, tutor teknik elektro yang cerdas.")
                history_gemini = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in st.session_state.chat_history[:-1]]
                response = model.start_chat(history=history_gemini).send_message(prompt)
                st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                st.rerun()
            except Exception:
                st.error("API Error.")

# --- HALAMAN AUTENTIKASI ---
def auth_page():
    st.markdown("<br><br><h1 style='text-align: center; color: #1CB0F6;'>🦉 Axiom Academy</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Ubah ide rekayasa Anda menjadi purwarupa nyata.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔑 Masuk", "📝 Daftar Baru"])
        with tab1:
            log_user = st.text_input("Username", key="log_u")
            log_pass = st.text_input("Password", type="password", key="log_p")
            if st.button("Masuk", use_container_width=True, type="primary"):
                if log_user in db["users"] and db["users"][log_user]["password"] == log_pass:
                    if "join_date" not in db["users"][log_user]: db["users"][log_user]["join_date"] = str(date.today())
                    save_db(db)
                    st.session_state.current_user = log_user
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Username atau Password salah!")
        with tab2:
            reg_user = st.text_input("Buat Username", key="reg_u")
            reg_pass = st.text_input("Buat Password", type="password", key="reg_p")
            if st.button("Daftar", use_container_width=True):
                if reg_user in db["users"]:
                    st.warning("Username sudah terpakai!")
                else:
                    db["users"][reg_user] = {
                        "password": reg_pass, "xp": 0, "gems": 100, "streak": 0, "progress": 0, "join_date": str(date.today())
                    }
                    save_db(db)
                    st.success("Pendaftaran berhasil! Silakan Masuk.")

# --- HALAMAN MATERI (KUIS) ---
def lesson_page():
    st.markdown("""<style>section[data-testid="stSidebar"] { display: none !important; }</style>""", unsafe_allow_html=True)
    
    user = db["users"][st.session_state.current_user]
    soal_list = MATERI_SOAL[st.session_state.active_lesson]
    total_q = len(soal_list)
    
    c1, c2 = st.columns([1, 10])
    with c1:
        if st.button("✖️ Batal"): 
            st.session_state.q_index = 0
            st.session_state.mistakes = 0
            st.session_state.active_lesson = None
            st.rerun()
    with c2: st.progress((st.session_state.q_index) / total_q)
    st.divider()
    
    if st.session_state.q_index >= total_q:
        st.balloons()
        earned_xp = max(10, 50 - (st.session_state.mistakes * 10))
        st.markdown("<h2 style='text-align: center; color: #58CC02;'>Luar Biasa! Sesi Selesai! 🎉</h2>", unsafe_allow_html=True)
        st.write(f"XP Diperoleh: **{earned_xp} XP**")
        if st.button(f"Klaim Hadiah", type="primary"):
            user["xp"] += earned_xp
            user["gems"] += 20
            if st.session_state.active_lesson == "ch1_p1" and user["progress"] == 0: user["progress"] = 1
            if st.session_state.active_lesson == "ch2_p1" and user["progress"] == 1: user["progress"] = 2
            
            check_and_update_streak(st.session_state.current_user)
            st.session_state.q_index = 0
            st.session_state.mistakes = 0
            st.session_state.active_lesson = None
            save_db(db)
            st.rerun()
        return

    q_data = soal_list[st.session_state.q_index]
    st.header(f"Tantangan {st.session_state.q_index + 1}")
    st.markdown(f"### {q_data['q']}")
    jawaban = st.radio("Pilih jawaban:", q_data['options'], index=None)
    st.write("<br><br>", unsafe_allow_html=True)
    
    if st.button("PERIKSA", type="primary", use_container_width=True):
        if jawaban == None: st.warning("Pilih jawaban terlebih dahulu!")
        elif jawaban == q_data['ans']:
            st.success("Benar Sekali!")
            st.session_state.q_index += 1
            time.sleep(1); st.rerun()
        else:
            st.error("Jawaban salah! (Mempengaruhi perolehan XP akhir)")
            st.session_state.mistakes += 1

# --- HALAMAN DASHBOARD UTAMA ---
def main_dashboard():
    user = db["users"][st.session_state.current_user]
    
    # TOP METRICS (Hati dirubah menjadi ∞ Super Axiom)
    c_empty, c_streak, c_gems, c_hearts = st.columns([4, 1.5, 1.5, 1.8])
    with c_streak: st.markdown(f"<div class='metric-box'>🔥 {user['streak']} Hari</div>", unsafe_allow_html=True)
    with c_gems: st.markdown(f"<div class='metric-box' style='color:#1CB0F6;'>💎 {user['gems']}</div>", unsafe_allow_html=True)
    with c_hearts: st.markdown(f"<div class='metric-box' style='color:#FF4B4B; border-color:#CE82FF;'>💖 Hati: ∞</div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="header-banner">
        <h2>Siap mengubah ide rekayasa elektro Anda menjadi nyata, {st.session_state.current_user}? 🚀</h2>
        <p style="margin:0;">Fitur Super Axiom Aktif: Belajar tanpa batas tanpa takut kehabisan nyawa!</p>
    </div>
    """, unsafe_allow_html=True)

    # --- BAB 1 ---
    st.markdown("### Bab 1: Fondasi AI di Industri")
    with st.container():
        st.markdown("<div class='course-card'>", unsafe_allow_html=True)
        c1, c2 = st.columns([7, 2])
        with c1:
            st.markdown("#### 🟢 Bagian 1: Pengenalan NLP")
            st.write("Apa itu NLP dan kenapa sistem kontrol membutuhkannya?")
        with c2:
            st.write("<br>", unsafe_allow_html=True)
            if st.button("MULAI MATERI 🎯", key="b1", use_container_width=True):
                st.session_state.active_lesson = "ch1_p1"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # --- BAB 2 ---
    st.markdown("### Bab 2: Pemrosesan Data Sensor (Log Analisis)")
    with st.container():
        css_class = "" if user["progress"] >= 1 else "locked-card"
        st.markdown(f"<div class='course-card {css_class}'>", unsafe_allow_html=True)
        c1, c2 = st.columns([7, 2])
        with c1:
            st.markdown(f"#### {'🟡' if user['progress'] >= 1 else '🔒'} Bagian 1: Ekstraksi Laporan Sistem")
            st.write("Mengekstrak angka suhu dan sentimen kerusakan dari teks bebas.")
        with c2:
            st.write("<br>", unsafe_allow_html=True)
            if user["progress"] >= 1:
                if st.button("MULAI MATERI 🎯", key="b2", use_container_width=True):
                    st.session_state.active_lesson = "ch2_p1"
                    st.rerun()
            else:
                st.button("Terkunci 🔒", key="b2_lock", disabled=True, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- BAB 3 ---
    st.markdown("### Bab 3: Sistem Kontrol Cerdas (IoT)")
    with st.container():
        css_class = "" if user["progress"] >= 2 else "locked-card"
        st.markdown(f"<div class='course-card {css_class}'>", unsafe_allow_html=True)
        c1, c2 = st.columns([7, 2])
        with c1:
            st.markdown(f"#### {'🔴' if user['progress'] >= 2 else '🔒'} Bagian 1: Integrasi Hardware")
            st.write("Menghubungkan perintah NLP dari Server ke Relay/Aktuator.")
        with c2:
            st.write("<br>", unsafe_allow_html=True)
            if user["progress"] >= 2:
                if st.button("MULAI MATERI 🎯", key="b3", use_container_width=True):
                    st.session_state.active_lesson = "ch3_p1"
                    st.rerun()
            else:
                st.button("Terkunci 🔒", key="b3_lock", disabled=True, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- HALAMAN PAPAN SKOR ---
def leaderboard_page():
    st.title("🏆 Papan Skor Global")
    leaderboard = []
    for u, data in db["users"].items(): 
        leaderboard.append({"Pengguna": u, "Total XP": data["xp"], "Streak 🔥": data["streak"]})
    df = pd.DataFrame(leaderboard).sort_values(by="Total XP", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    st.dataframe(df, use_container_width=True)

# --- HALAMAN TOKO ---
def shop_page():
    user = db["users"][st.session_state.current_user]
    st.title("🛒 Toko Item Premium")
    st.markdown(f"### Saldo Anda: 💎 {user['gems']} Permata")
    st.divider()
    
    st.info("✨ **Status Akun:** Anda berada dalam Mode Pengembang / Super Axiom. Akses Hati Tidak Terbatas (∞) telah aktif otomatis secara gratis!")

# --- HALAMAN PROFIL ---
def profile_page():
    user = db["users"][st.session_state.current_user]
    st.title("👤 Profil Pengguna")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("🔥 Total Streak", f"{user['streak']} Hari")
    c2.metric("⚡ Total XP", f"{user['xp']} XP")
    c3.metric("📅 Bergabung Sejak", user.get("join_date", "Tidak diketahui"))
    
    st.divider()
    st.subheader("⚙️ Pengaturan Akun")
    new_pass = st.text_input("Ganti Password Baru", type="password")
    if st.button("Simpan Password"):
        if len(new_pass) > 2:
            user['password'] = new_pass
            save_db(db)
            st.success("Password berhasil diubah!")
        else:
            st.error("Password minimal 3 karakter.")

# --- ROUTER & SIDEBAR ---
if not st.session_state.logged_in:
    auth_page()
else:
    with st.sidebar:
        st.markdown("<div class='sidebar-logo'>🦉 AXIOM</div>", unsafe_allow_html=True)
        menu = st.radio("Navigasi", ["🏠 Belajar", "🏆 Papan Skor", "🛒 Toko", "👤 Profil"], label_visibility="hidden")
        st.write("<br><br><br><br>", unsafe_allow_html=True)
        if st.button("🚪 Keluar Akun", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.rerun()
            
    if st.session_state.active_lesson:
        lesson_page()
    else:
        if menu == "🏠 Belajar": main_dashboard()
        elif menu == "🏆 Papan Skor": leaderboard_page()
        elif menu == "🛒 Toko": shop_page()
        elif menu == "👤 Profil": profile_page()
        
        render_genie()