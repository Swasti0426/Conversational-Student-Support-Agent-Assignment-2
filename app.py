import html
import json
from pathlib import Path

import streamlit as st

from auth_db import (
    authenticate_user,
    create_conversation,
    list_conversations,
    get_messages,
    add_message,
    rename_conversation,
    delete_conversation,
)

try:
    from streamlit_mic_recorder import speech_to_text
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False


# =========================================================
# PAGE CONFIGURATION & SESSION STATE
# =========================================================
st.set_page_config(
    page_title="Campus Companion | AI Student Support",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
STUDENTS_FILE = BASE_DIR / "data" / "students.json"

DEFAULTS = {
    "user": None,
    "active_conversation_id": None,
    "pending_question": None,
    "composer_input": "",
    "last_voice_text": "",
    "dark_mode": False,
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# PROFESSIONAL DESIGN SYSTEM
# =========================================================
COLORS = {
    "bg": "#0B1120",
    "surface": "#111B2E",
    "surface_alt": "#17243A",
    "text": "#F3F6FC",
    "muted": "#A5B2C7",
    "border": "#26354D",
    "input_bg": "#0E1728",
    "input_text": "#F3F6FC",
}

PRIMARY = "#2563F5"
PRIMARY_DARK = "#1748D8"
ACCENT = "#16A6A1"

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
    :root {{
        --bg: {COLORS['bg']};
        --surface: {COLORS['surface']};
        --surface-alt: {COLORS['surface_alt']};
        --text: {COLORS['text']};
        --muted: {COLORS['muted']};
        --border: {COLORS['border']};
        --primary: {PRIMARY};
        --primary-dark: {PRIMARY_DARK};
        --accent: {ACCENT};
    }}

    html, body, .stApp, [data-testid="stAppViewContainer"],
    [data-testid="stMain"], [data-testid="stMainBlockContainer"] {{
        background: var(--bg) !important;
        color: var(--text) !important;
        font-family: 'DM Sans', sans-serif !important;
    }}
    .block-container {{
        max-width: 1360px;
        padding-top: 1.45rem;
        padding-bottom: 2.2rem;
    }}
    h1, h2, h3, h4 {{
        color: var(--text) !important;
        font-family: 'Manrope', sans-serif !important;
        letter-spacing: -0.035em;
    }}
    p, li, label, [data-testid="stMarkdownContainer"] {{ color: var(--text); }}
    [data-testid="stCaptionContainer"], .muted {{ color: var(--muted) !important; }}
    [data-testid="stHeader"] {{ background: transparent !important; }}
    #MainMenu, footer {{ visibility: hidden; }}

    /* Sidebar */
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div {{
        background: var(--surface) !important;
        border-right: 1px solid var(--border);
    }}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {{ color: var(--text) !important; }}
    [data-testid="stSidebar"] .block-container {{ padding-top: 1.2rem; }}

    .brand-row {{ display:flex; align-items:center; gap:11px; margin: 3px 0 24px; }}
    .brand-mark {{
        width:44px; height:44px; flex:0 0 44px; border-radius:14px;
        display:flex; align-items:center; justify-content:center;
        color:#fff; font-size:21px; font-weight:800;
        background:linear-gradient(140deg, #3157D5 0%, #16A6A1 100%);
        box-shadow:0 8px 22px rgba(49,87,213,.22);
    }}
    .brand-name {{ font-family:'Manrope',sans-serif; font-weight:800; font-size:17px; letter-spacing:-.5px; color:var(--text); line-height:1.25; }}
    .brand-subtitle {{ color:var(--muted); font-size:11px; margin-top:3px; }}
    .sidebar-label {{ font-size:10px; text-transform:uppercase; letter-spacing:1.5px; font-weight:800; color:var(--muted); margin:18px 0 9px; }}
    .profile-card {{
        display:flex; align-items:center; gap:11px; padding:13px;
        background:var(--surface-alt); border:1px solid var(--border); border-radius:15px;
        margin: 4px 0 15px;
    }}
    .avatar {{
        display:flex; align-items:center; justify-content:center; flex:0 0 38px;
        width:38px; height:38px; border-radius:12px; background:#DDE7FF; color:#2446B7;
        font-weight:800; font-size:15px;
    }}
    .profile-name {{ font-weight:700; font-size:13px; color:var(--text); line-height:1.35; }}
    .profile-role {{ color:var(--muted); font-size:11px; margin-top:3px; }}

    /* Main page heading */
    .topline {{ display:flex; justify-content:space-between; align-items:center; gap:12px; margin:0 0 18px; }}
    .eyebrow {{ color:var(--primary); font-size:10px; font-weight:800; letter-spacing:1.8px; text-transform:uppercase; margin-bottom:9px; }}
    .page-title {{ color:var(--text); font-family:'Manrope',sans-serif; font-weight:800; font-size:clamp(27px,3vw,38px); letter-spacing:-1.4px; line-height:1.16; margin:0; }}
    .page-subtitle {{ color:var(--muted); font-size:14px; line-height:1.7; margin-top:10px; max-width:760px; }}
    .status-pill {{ display:inline-flex; align-items:center; gap:7px; border:1px solid var(--border); border-radius:99px; padding:8px 12px; color:var(--muted); font-size:11px; font-weight:700; background:var(--surface); white-space:nowrap; }}
    .status-dot {{ width:7px; height:7px; border-radius:50%; background:#19A974; display:inline-block; }}
    .hero-chips {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:16px; }}
    .hero-chips span {{ display:inline-flex; align-items:center; border:1px solid rgba(91,128,190,.14); background:rgba(255,255,255,.65); border-radius:99px; padding:7px 10px; font-size:10px; color:#31527F; font-weight:700; }}

    /* Prompt cards */
    .section-heading {{ display:flex; align-items:center; justify-content:space-between; gap:10px; margin:25px 0 12px; }}
    .section-heading-title {{ color:var(--text); font-family:'Manrope',sans-serif; font-size:15px; font-weight:800; }}
    .section-heading-note {{ color:var(--muted); font-size:11px; }}
    .prompt-card {{
        background:#131F33 !important; color:#EEF3FF !important;
        border:1px solid #2B3D59 !important; border-radius:17px;
        padding:17px 16px 14px; min-height:127px; box-shadow:0 5px 18px rgba(22,39,74,.025);
        transition:transform .15s ease, border-color .15s ease, box-shadow .15s ease;
    }}
    .prompt-icon {{ width:37px; height:37px; display:flex; align-items:center; justify-content:center; border-radius:12px; background:#EEF2FF; font-size:18px; margin-bottom:13px; }}
    .prompt-title {{ color:#F3F6FF !important; font-size:13px; font-weight:800; margin-bottom:5px; }}
    .prompt-desc {{ color:#B1C0D8 !important; font-size:11px; line-height:1.5; }}

    /* Chat area */
    .chat-shell {{ background:var(--surface); border:1px solid var(--border); border-radius:20px; padding:18px 18px 4px; box-shadow:0 7px 24px rgba(22,39,74,.035); }}
    .chat-heading {{ display:flex; align-items:center; gap:10px; padding-bottom:14px; margin-bottom:12px; border-bottom:1px solid var(--border); }}
    .chat-heading-icon {{ width:38px; height:38px; display:flex; align-items:center; justify-content:center; border-radius:13px; background:#E6F7F5; color:#087F79; font-size:18px; }}
    .chat-heading-title {{ font-size:14px; font-weight:800; color:var(--text); }}
    .chat-heading-subtitle {{ font-size:11px; color:var(--muted); margin-top:3px; }}
    [data-testid="stChatMessage"] {{
        background:var(--surface-alt) !important; border:1px solid var(--border) !important;
        border-radius:16px !important; padding:13px 15px !important; margin-bottom:12px !important;
    }}
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {{ color:var(--text) !important; line-height:1.72; font-size:14px; }}
    [data-testid="stChatMessageAvatarIcon-user"], [data-testid="stChatMessageAvatarIcon-assistant"] {{ border-radius:12px; }}

    /* Inputs and buttons */
    div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea,
    div[data-testid="stNumberInput"] input {{
        background:{COLORS['input_bg']} !important; color:{COLORS['input_text']} !important;
        -webkit-text-fill-color:{COLORS['input_text']} !important;
        border:1px solid var(--border) !important; border-radius:12px !important;
        box-shadow:none !important; caret-color:var(--primary) !important; min-height:44px;
    }}
    div[data-testid="stTextInput"] input:focus, div[data-testid="stTextArea"] textarea:focus {{
        border-color:var(--primary) !important; box-shadow:0 0 0 3px rgba(49,87,213,.12) !important;
    }}
    div[data-testid="stTextInput"] input::placeholder, div[data-testid="stTextArea"] textarea::placeholder {{
        color:#8491A6 !important; -webkit-text-fill-color:#8491A6 !important; opacity:1 !important;
    }}
    div[data-testid="stTextInput"] label, div[data-testid="stTextArea"] label {{ color:var(--text) !important; font-weight:600 !important; }}
    .stButton > button, div[data-testid="stFormSubmitButton"] button, .stDownloadButton > button {{
        border-radius:12px !important; min-height:42px; font-weight:700 !important;
        transition:all .16s ease; border:1px solid var(--border) !important;
    }}
    .stButton > button[kind="primary"], div[data-testid="stFormSubmitButton"] button[kind="primary"] {{
        background:var(--primary) !important; color:#fff !important; border-color:var(--primary) !important;
    }}
    .stButton > button[kind="primary"]:hover, div[data-testid="stFormSubmitButton"] button[kind="primary"]:hover {{
        background:var(--primary-dark) !important; border-color:var(--primary-dark) !important;
    }}
    .stButton > button[kind="secondary"] {{ background:var(--surface) !important; color:var(--text) !important; }}
    .stButton > button[kind="secondary"]:hover {{ border-color:var(--primary) !important; color:var(--primary) !important; }}
    .stButton > button *, div[data-testid="stFormSubmitButton"] button * {{ font-weight:700 !important; }}
    [data-testid="stToggle"] label, [data-testid="stCheckbox"] label {{ color:var(--text) !important; }}
    hr {{ border-color:var(--border) !important; }}
    .footer-note {{ text-align:center; color:var(--muted) !important; font-size:11px; line-height:1.7; padding:22px 0 4px; }}

    /* Login screen */
    .login-wrap {{ padding:8px 0 22px; }}
    .login-visual {{
        min-height:565px; height:100%; position:relative; overflow:hidden;
        padding:42px 38px; border-radius:26px; color:#fff;
        background:radial-gradient(circle at 88% 8%, rgba(41,211,194,.28), transparent 28%),
                   radial-gradient(circle at 8% 95%, rgba(94,130,255,.28), transparent 34%),
                   linear-gradient(145deg,#101B36 0%,#1B3471 58%,#146D78 100%);
        box-shadow:0 20px 55px rgba(24,47,102,.18);
    }}
    .login-visual * {{ color:#fff; }}
    .login-logo {{ display:flex; align-items:center; gap:12px; margin-bottom:66px; }}
    .login-logo-mark {{ width:45px; height:45px; border:1px solid rgba(255,255,255,.24); border-radius:14px; display:flex; align-items:center; justify-content:center; background:rgba(255,255,255,.12); font-size:22px; }}
    .login-logo-title {{ font-family:'Manrope',sans-serif; font-size:17px; font-weight:800; }}
    .login-logo-sub {{ color:#C7D5F5; font-size:11px; margin-top:3px; }}
    .login-kicker {{ color:#9DE5E0 !important; font-size:10px; font-weight:800; letter-spacing:2px; text-transform:uppercase; margin-bottom:15px; }}
    .login-headline {{ color:#fff !important; font-family:'Manrope',sans-serif; font-size:clamp(32px,3vw,43px); font-weight:800; letter-spacing:-1.6px; line-height:1.12; margin:0 0 18px; }}
    .login-copy {{ color:#DCE6FA !important; font-size:14px; line-height:1.85; max-width:420px; }}
    .login-feature-row {{ display:flex; align-items:center; gap:12px; margin-top:19px; color:#F4F7FF; font-size:13px; }}
    .login-feature-check {{ width:25px; height:25px; border-radius:8px; display:flex; align-items:center; justify-content:center; background:rgba(255,255,255,.13); border:1px solid rgba(255,255,255,.16); color:#9DE5E0; font-size:13px; }}
    .login-bottom {{ position:absolute; bottom:25px; left:38px; right:38px; border-top:1px solid rgba(255,255,255,.16); padding-top:14px; color:#BFCDF0 !important; font-size:10px; }}
    .login-form-panel {{ padding:35px 34px; background:var(--surface); border:1px solid var(--border); border-radius:24px; box-shadow:0 15px 45px rgba(22,39,74,.05); }}
    .login-form-eyebrow {{ color:var(--primary); font-size:10px; font-weight:800; letter-spacing:1.7px; text-transform:uppercase; margin-bottom:10px; }}
    .login-form-title {{ font-family:'Manrope',sans-serif; color:var(--text); font-size:29px; font-weight:800; letter-spacing:-1px; margin-bottom:8px; }}
    .login-form-copy {{ color:var(--muted); font-size:13px; line-height:1.7; margin-bottom:25px; }}

    @media(max-width:850px) {{
        .block-container {{ padding-top:1rem; }}
        .login-visual {{ min-height:430px; padding:28px 25px; }}
        .login-logo {{ margin-bottom:42px; }}
        .login-bottom {{ left:25px; right:25px; }}
        .login-form-panel {{ padding:27px 22px; }}
    }}

    /* =====================================================
       CAMPUS COMPANION — polished dashboard refinements
       ===================================================== */
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div {{
        background: linear-gradient(180deg, #101D3B 0%, #14264B 58%, #101B35 100%) !important;
        border-right: 1px solid #253A66 !important;
    }}
    [data-testid="stSidebar"] .brand-name,
    [data-testid="stSidebar"] .brand-subtitle,
    [data-testid="stSidebar"] .sidebar-label,
    [data-testid="stSidebar"] .profile-name,
    [data-testid="stSidebar"] .profile-role,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{
        color: #EAF0FF !important;
    }}
    [data-testid="stSidebar"] .brand-mark {{
        background: linear-gradient(140deg, #3478FF, #1BC5C0) !important;
        box-shadow: 0 8px 26px rgba(38, 111, 255, .28) !important;
    }}
    [data-testid="stSidebar"] .profile-card {{
        background: rgba(255,255,255,.07) !important;
        border: 1px solid rgba(165,190,255,.20) !important;
    }}
    [data-testid="stSidebar"] .avatar {{
        background: linear-gradient(145deg, #8E8BFF, #5B6EF5) !important;
        color: #FFFFFF !important;
        border-radius: 50% !important;
    }}
    [data-testid="stSidebar"] .stButton > button {{
        background: rgba(255,255,255,.07) !important;
        color: #F5F7FF !important;
        border: 1px solid rgba(190,205,255,.16) !important;
        text-align: left !important;
    }}
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {{
        background: linear-gradient(100deg,#3478FF,#2357E8) !important;
        color: #FFFFFF !important;
        border-color: transparent !important;
        box-shadow: 0 7px 18px rgba(31,86,230,.24) !important;
    }}
    [data-testid="stSidebar"] [data-testid="stToggle"] label {{
        color: #F5F7FF !important;
    }}
    [data-testid="stSidebar"] hr {{
        border-color: rgba(190,205,255,.18) !important;
    }}
    .block-container {{
        max-width: 1500px !important;
        padding-top: 1.15rem !important;
        padding-left: clamp(1.2rem, 2.2vw, 2.5rem) !important;
        padding-right: clamp(1.2rem, 2.2vw, 2.5rem) !important;
    }}
    .topline {{
        padding: 27px 30px !important;
        border: 1px solid #D8E8FF !important;
        border-radius: 23px !important;
        background:
            radial-gradient(circle at 84% 18%, rgba(255,255,255,.94) 0 3%, transparent 3.3%),
            radial-gradient(circle at 90% 60%, rgba(107,205,255,.35), transparent 23%),
            linear-gradient(112deg, #E7F0FF 0%, #F1F4FF 54%, #DDF8FA 100%) !important;
        box-shadow: 0 12px 34px rgba(48,91,160,.07) !important;
        margin-bottom: 25px !important;
        min-height: 150px;
    }}
    .page-title {{
        font-size: clamp(29px, 3vw, 42px) !important;
        color: #112B57 !important;
        letter-spacing: -1.5px !important;
    }}
    .page-subtitle {{ color: #3D5C89 !important; max-width: 850px !important; }}
    .eyebrow {{ color: #2865DB !important; }}
    .status-pill {{
        background: rgba(255,255,255,.82) !important;
        border-color: #D6E4F7 !important;
        color: #27446D !important;
        padding: 10px 14px !important;
        box-shadow: 0 4px 14px rgba(48,91,160,.06);
    }}
    .section-heading {{ margin-top: 27px !important; margin-bottom: 14px !important; }}
    .section-heading-title {{ font-size: 17px !important; color: #102B57 !important; }}
    .prompt-card {{
        min-height: 142px !important;
        padding: 18px !important;
        border-radius: 19px !important;
        box-shadow: 0 8px 24px rgba(33,68,128,.055) !important;
        transition: transform .16s ease, box-shadow .16s ease !important;
    }}
    .prompt-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 13px 28px rgba(33,68,128,.10) !important;
    }}
    .prompt-icon {{ width: 43px !important; height: 43px !important; font-size: 21px !important; }}
    .prompt-title {{ font-size: 14px !important; }}
    .prompt-desc {{ font-size: 12px !important; }}
    .chat-heading {{
        border-bottom-color: #DCE7F7 !important;
        padding-bottom: 16px !important;
        margin-top: 4px !important;
    }}
    [data-testid="stChatMessage"] {{
        border-radius: 18px !important;
        padding: 16px 18px !important;
        box-shadow: 0 4px 15px rgba(30,65,120,.035) !important;
    }}
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarIcon-assistant"]) {{
        background: linear-gradient(110deg,#F0F5FF,#EAF2FF) !important;
    }}
    div[data-testid="stForm"] {{
        background: #FFFFFF !important;
        border: 1px solid #DCE7F7 !important;
        border-radius: 18px !important;
        padding: 12px 14px 5px !important;
        box-shadow: 0 8px 24px rgba(33,68,128,.055) !important;
    }}
    div[data-testid="stTextInput"] input {{
        min-height: 48px !important;
        border-radius: 13px !important;
        background: #F9FBFF !important;
        border-color: #D5E2F4 !important;
        font-size: 14px !important;
    }}
    div[data-testid="stFormSubmitButton"] button[kind="primary"] {{
        background: linear-gradient(100deg,#3478FF,#2158E9) !important;
        color: #FFFFFF !important;
        border: 0 !important;
        box-shadow: 0 6px 16px rgba(37,99,245,.22) !important;
    }}
    div[data-testid="stFormSubmitButton"] button[kind="primary"] * {{ color:#FFFFFF !important; }}
    .footer-note {{ color: #6A7D99 !important; }}

    /* Permanent dark theme: high contrast across every workspace section */
    .topline {{
        border: 1px solid #263D62 !important;
        background:
            radial-gradient(circle at 88% 18%, rgba(31,199,190,.16), transparent 25%),
            linear-gradient(112deg, #111D35 0%, #15294B 58%, #103B48 100%) !important;
        box-shadow: 0 14px 36px rgba(0,0,0,.18) !important;
    }}
    .page-title {{ color: #F4F7FF !important; }}
    .page-subtitle {{ color: #B9C8E2 !important; }}
    .eyebrow {{ color: #7FE3DC !important; }}
    .hero-chips span {{
        background: rgba(255,255,255,.07) !important;
        border-color: rgba(170,195,240,.18) !important;
        color: #DDE9FF !important;
    }}
    .status-pill {{
        background: #172943 !important;
        border-color: #2D4568 !important;
        color: #DCE8FA !important;
    }}
    .section-heading-title {{ color: #F0F5FF !important; }}
    .section-heading-note {{ color: #9EADC6 !important; }}
    .prompt-card {{
        background: linear-gradient(145deg,#141F34,#17253D) !important;
        border-color: #2A3B56 !important;
        box-shadow: 0 8px 24px rgba(0,0,0,.15) !important;
    }}
    .prompt-card:hover {{
        background: linear-gradient(145deg,#192944,#1A2C48) !important;
        border-color: #3D5B85 !important;
        box-shadow: 0 13px 28px rgba(0,0,0,.22) !important;
    }}
    .prompt-title {{ color: #F1F5FF !important; }}
    .prompt-desc {{ color: #AEBED6 !important; }}
    .prompt-icon {{ background: #22385A !important; }}
    .chat-heading {{ border-bottom-color: #2A3A54 !important; }}
    .chat-heading-title {{ color: #F1F5FF !important; }}
    .chat-heading-subtitle {{ color: #A5B5CD !important; }}
    [data-testid="stChatMessage"] {{
        background: #131F33 !important;
        border: 1px solid #2B3B55 !important;
        color: #F3F6FC !important;
        box-shadow: 0 5px 18px rgba(0,0,0,.13) !important;
    }}
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] span {{
        color: #EAF0FB !important;
    }}
    div[data-testid="stForm"] {{
        background: #111B2E !important;
        border: 1px solid #2A3A54 !important;
        box-shadow: 0 8px 24px rgba(0,0,0,.16) !important;
    }}
    div[data-testid="stTextInput"] input {{
        background: #0D1728 !important;
        color: #F3F6FC !important;
        -webkit-text-fill-color: #F3F6FC !important;
        border: 1px solid #354966 !important;
    }}
    div[data-testid="stTextInput"] input::placeholder {{
        color: #93A4BE !important;
        -webkit-text-fill-color: #93A4BE !important;
    }}
    div[data-testid="stFormSubmitButton"] button[kind="primary"] {{
        background: linear-gradient(100deg,#3478FF,#2158E9) !important;
        color: #FFFFFF !important;
        border: 0 !important;
        box-shadow: 0 6px 16px rgba(37,99,245,.22) !important;
    }}
    div[data-testid="stFormSubmitButton"] button[kind="primary"] * {{ color:#FFFFFF !important; }}
    .footer-note {{ color: #8D9DB7 !important; }}
    [data-testid="stSidebar"] [data-testid="stToggle"] {{ display:none !important; }}

    @media (max-width: 900px) {{
        .topline {{ padding: 22px !important; align-items: flex-start !important; }}
        .status-pill {{ display: none !important; }}
        .prompt-card {{ min-height: 125px !important; }}
    }}

    
    /* FINAL HIGH-CONTRAST DARK UI OVERRIDES */
    html, body, .stApp, [data-testid="stAppViewContainer"],
    [data-testid="stMain"], [data-testid="stMainBlockContainer"],
    section[data-testid="stMain"] > div {{
        background: #0A1020 !important;
        color: #EAF0FF !important;
    }}
    [data-testid="stHeader"] {{ background: #0A1020 !important; }}
    [data-testid="stMain"] .stMarkdown,
    [data-testid="stMain"] [data-testid="stMarkdownContainer"],
    [data-testid="stMain"] p,
    [data-testid="stMain"] span,
    [data-testid="stMain"] label,
    [data-testid="stMain"] li,
    [data-testid="stMain"] h1,
    [data-testid="stMain"] h2,
    [data-testid="stMain"] h3,
    [data-testid="stMain"] h4 {{
        color: #EAF0FF !important;
    }}
    [data-testid="stMain"] [data-testid="stCaptionContainer"],
    [data-testid="stMain"] .page-subtitle,
    [data-testid="stMain"] .prompt-desc,
    [data-testid="stMain"] .section-heading-note,
    [data-testid="stMain"] .chat-heading-subtitle {{
        color: #A8B7D0 !important;
    }}
    .block-container {{ max-width: 1480px !important; padding-top: 1.4rem !important; }}
    .topline {{
        background:
            radial-gradient(circle at 88% 15%, rgba(20,184,166,.18), transparent 26%),
            linear-gradient(115deg,#111D35 0%,#172A4B 58%,#103B43 100%) !important;
        border: 1px solid #2A3D5D !important;
        border-radius: 24px !important;
        box-shadow: 0 18px 45px rgba(0,0,0,.22) !important;
        padding: 30px !important;
        min-height: 170px !important;
    }}
    .topline .page-title {{ color: #F6F8FF !important; }}
    .topline .page-subtitle {{ color: #BDCAE0 !important; }}
    .topline .eyebrow {{ color: #77E1D8 !important; }}
    .hero-chips span {{
        color: #E2EDFF !important;
        background: rgba(255,255,255,.07) !important;
        border: 1px solid rgba(191,211,255,.17) !important;
    }}
    .status-pill {{
        color: #E6F0FF !important;
        background: #172640 !important;
        border: 1px solid #334967 !important;
    }}
    .section-heading-title {{ color: #F0F5FF !important; }}
    .section-heading-note {{ color: #9DADC7 !important; }}
    .prompt-card {{
        background: linear-gradient(145deg,#131E32,#17253D) !important;
        border: 1px solid #2B3D59 !important;
        border-radius: 18px !important;
        box-shadow: 0 9px 24px rgba(0,0,0,.17) !important;
        min-height: 140px !important;
    }}
    .prompt-card:hover {{
        background: linear-gradient(145deg,#192944,#1A2E4B) !important;
        border-color: #46658F !important;
        transform: translateY(-2px);
    }}
    .prompt-title {{ color: #F3F6FF !important; }}
    .prompt-desc {{ color: #B1C0D8 !important; }}
    .prompt-icon {{ background: #22385A !important; }}
    .chat-heading {{ border-bottom: 1px solid #2A3B55 !important; }}
    .chat-heading-title {{ color: #F4F7FF !important; }}
    .chat-heading-subtitle {{ color: #AAB9D0 !important; }}
    [data-testid="stChatMessage"] {{
        background: #131F33 !important;
        border: 1px solid #2B3D59 !important;
        border-radius: 17px !important;
        color: #EAF0FF !important;
    }}
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] span {{ color: #EAF0FF !important; }}
    div[data-testid="stForm"] {{
        background: #111B2E !important;
        border: 1px solid #2C3D58 !important;
        border-radius: 18px !important;
        padding: 13px 14px 5px !important;
        box-shadow: 0 10px 28px rgba(0,0,0,.2) !important;
    }}
    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea {{
        background: #0B1527 !important;
        color: #F3F6FC !important;
        -webkit-text-fill-color: #F3F6FC !important;
        border: 1px solid #354B6B !important;
        border-radius: 12px !important;
        min-height: 46px !important;
    }}
    div[data-testid="stTextInput"] input::placeholder,
    div[data-testid="stTextArea"] textarea::placeholder {{
        color: #91A4C1 !important;
        -webkit-text-fill-color: #91A4C1 !important;
        opacity: 1 !important;
    }}
    div[data-testid="stFormSubmitButton"] button,
    .stButton > button,
    div[data-testid="stFormSubmitButton"] button[kind="primary"] {{
        background: linear-gradient(100deg,#3478FF,#2359E8) !important;
        color: #FFFFFF !important;
        border: 1px solid #3975F5 !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        box-shadow: 0 6px 18px rgba(35,89,232,.22) !important;
    }}
    div[data-testid="stFormSubmitButton"] button *,
    .stButton > button * {{ color: #FFFFFF !important; }}
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div {{
        background: linear-gradient(180deg,#0D1830 0%,#111F3B 55%,#0D172C 100%) !important;
        border-right: 1px solid #263A5B !important;
    }}
    [data-testid="stSidebar"] .brand-name,
    [data-testid="stSidebar"] .brand-subtitle,
    [data-testid="stSidebar"] .sidebar-label,
    [data-testid="stSidebar"] .profile-name,
    [data-testid="stSidebar"] .profile-role,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{
        color: #EAF0FF !important;
    }}
    [data-testid="stSidebar"] .profile-card {{
        background: rgba(255,255,255,.055) !important;
        border-color: rgba(170,195,240,.18) !important;
    }}
    [data-testid="stSidebar"] .stButton > button {{
        background: rgba(255,255,255,.06) !important;
        border: 1px solid rgba(190,210,255,.16) !important;
        color: #F4F7FF !important;
    }}
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {{
        background: linear-gradient(100deg,#3478FF,#2359E8) !important;
        border-color: transparent !important;
    }}
    [data-testid="stSidebar"] hr {{ border-color: #293B59 !important; }}
    /* Login screen: keep both panels readable and visually balanced */
    .login-visual {{
        background:
            radial-gradient(circle at 88% 8%, rgba(41,211,194,.23), transparent 28%),
            linear-gradient(145deg,#101B36 0%,#1B3471 58%,#146D78 100%) !important;
        border: 1px solid #2C4770 !important;
    }}
    .login-form-panel {{
        background: #111B2E !important;
        border: 1px solid #2B3D59 !important;
        box-shadow: 0 18px 45px rgba(0,0,0,.2) !important;
    }}
    .login-form-title {{ color: #F5F7FF !important; }}
    .login-form-copy {{ color: #AEBED6 !important; }}
    .login-form-eyebrow {{ color: #77E1D8 !important; }}
    .footer-note {{ color: #91A2BD !important; }}
    [data-testid="stSidebar"] [data-testid="stToggle"] {{ display: none !important; }}

    
    /* LAST-RESORT OVERRIDES: force dark surfaces and readable contrast */
    html, body, .stApp, [data-testid="stApp"], [data-testid="stAppViewContainer"],
    [data-testid="stMain"], [data-testid="stMainBlockContainer"],
    section[data-testid="stMain"], section[data-testid="stMain"] > div,
    [data-testid="stMain"] > div {{
        background-color: #0A1020 !important;
        color: #EAF0FF !important;
    }}
    [data-testid="stHeader"], [data-testid="stToolbar"] {{
        background: #0A1020 !important;
    }}
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div,
    [data-testid="stSidebar"] [data-testid="stSidebarContent"] {{
        background-color: #0D1830 !important;
        color: #EAF0FF !important;
    }}
    [data-testid="stMain"] h1, [data-testid="stMain"] h2,
    [data-testid="stMain"] h3, [data-testid="stMain"] h4,
    [data-testid="stMain"] p, [data-testid="stMain"] span,
    [data-testid="stMain"] label, [data-testid="stMain"] li,
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] {{
        color: #EAF0FF !important;
    }}
    [data-testid="stMain"] .page-subtitle,
    [data-testid="stMain"] .section-heading-note,
    [data-testid="stMain"] .prompt-desc,
    [data-testid="stMain"] .chat-heading-subtitle,
    [data-testid="stMain"] [data-testid="stCaptionContainer"] {{
        color: #A8B7D0 !important;
    }}
    .login-form-panel {{
        background: #111B2E !important;
        border: 1px solid #2B3D59 !important;
        border-radius: 24px !important;
    }}
    .login-form-title, .login-form-panel h1, .login-form-panel h2,
    .login-form-panel h3 {{
        color: #F5F7FF !important;
    }}
    .login-form-copy {{ color: #B7C6DE !important; }}
    .login-form-eyebrow {{ color: #77E1D8 !important; }}
    .login-form-panel p, .login-form-panel label {{
        color: #EAF0FF !important;
    }}
    .prompt-card, .chat-shell {{
        background: #131F33 !important;
        border-color: #2B3D59 !important;
    }}
    .prompt-title, .chat-heading-title {{ color: #F3F6FF !important; }}
    .prompt-desc, .chat-heading-subtitle {{ color: #B1C0D8 !important; }}
    [data-testid="stSidebar"] .brand-name,
    [data-testid="stSidebar"] .brand-subtitle,
    [data-testid="stSidebar"] .sidebar-label,
    [data-testid="stSidebar"] .profile-name,
    [data-testid="stSidebar"] .profile-role,
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{
        color: #EAF0FF !important;
    }}
    [data-testid="stSidebar"] .stButton > button:not([kind="primary"]) {{
        background: #14213A !important;
        color: #EAF0FF !important;
        border-color: #304362 !important;
    }}
    [data-testid="stSidebar"] .stButton > button:not([kind="primary"]) * {{
        color: #EAF0FF !important;
    }}
    .stApp [data-testid="stTextInput"] input,
    .stApp [data-testid="stTextArea"] textarea {{
        background: #0B1527 !important;
        color: #F3F6FC !important;
        -webkit-text-fill-color: #F3F6FC !important;
        border: 1px solid #354B6B !important;
    }}
    .stApp [data-testid="stTextInput"] input::placeholder,
    .stApp [data-testid="stTextArea"] textarea::placeholder {{
        color: #91A4C1 !important;
        -webkit-text-fill-color: #91A4C1 !important;
    }}

    
    /* FINAL UI POLISH — high contrast, dark surfaces, no empty portal header */
    html, body, .stApp, [data-testid="stAppViewContainer"],
    [data-testid="stMain"], [data-testid="stMainBlockContainer"],
    section[data-testid="stMain"], section[data-testid="stMain"] > div {{
        background: #0A1020 !important;
        color: #EEF3FF !important;
    }}
    [data-testid="stHeader"], [data-testid="stToolbar"] {{ background: #0A1020 !important; }}
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div {{
        background: linear-gradient(180deg,#0D1830,#111F3B 58%,#0D172C) !important;
        border-right: 1px solid #263A5B !important;
    }}
    [data-testid="stMain"] h1, [data-testid="stMain"] h2,
    [data-testid="stMain"] h3, [data-testid="stMain"] h4,
    [data-testid="stMain"] p, [data-testid="stMain"] span,
    [data-testid="stMain"] label, [data-testid="stMain"] li {{
        color: #EEF3FF !important;
    }}
    [data-testid="stMain"] [data-testid="stCaptionContainer"],
    [data-testid="stMain"] .page-subtitle,
    [data-testid="stMain"] .section-heading-note,
    [data-testid="stMain"] .prompt-desc,
    [data-testid="stMain"] .chat-heading-subtitle {{
        color: #AABAD3 !important;
    }}
    .portal-welcome {{
        width: 100%;
        box-sizing: border-box;
        padding: 25px 26px 21px;
        margin: 0 0 20px;
        border-radius: 22px;
        border: 1px solid #2B4264;
        background:
          radial-gradient(circle at 90% 8%, rgba(30,194,184,.15), transparent 28%),
          linear-gradient(135deg,#121F38,#172945 70%,#10343F);
        box-shadow: 0 16px 38px rgba(0,0,0,.18);
    }}
    .portal-topline {{ display:flex; align-items:center; gap:14px; }}
    .portal-icon {{
        flex:0 0 48px; width:48px; height:48px; display:flex;
        align-items:center; justify-content:center; border-radius:15px;
        color:#FFFFFF !important; font-size:24px; font-weight:800;
        background:linear-gradient(145deg,#3478FF,#12AFAF);
        box-shadow:0 8px 20px rgba(30,125,255,.20);
    }}
    .portal-kicker {{
        color:#75E2DC !important; font-size:10px; font-weight:800;
        letter-spacing:1.8px; margin-bottom:6px;
    }}
    .portal-heading {{
        color:#F5F7FF !important; font-size:29px; font-weight:800;
        letter-spacing:-.8px; line-height:1.15; margin-bottom:5px;
    }}
    .portal-copy {{ color:#B9C9E1 !important; font-size:13px; line-height:1.6; }}
    .portal-status {{
        margin-left:auto; flex-shrink:0; display:flex; align-items:center; gap:8px;
        border:1px solid #344B69; background:rgba(255,255,255,.06);
        border-radius:999px; padding:10px 13px; color:#DCE8FA !important;
        font-size:11px; font-weight:700;
    }}
    .portal-status span {{ width:7px; height:7px; border-radius:50%; background:#2DD4A3; display:inline-block; }}
    .portal-benefits {{
        display:grid; grid-template-columns:repeat(3,minmax(0,1fr));
        gap:10px; margin-top:20px; padding-top:17px; border-top:1px solid rgba(180,205,245,.15);
    }}
    .portal-benefits div {{
        display:flex; align-items:center; gap:9px; min-width:0;
        border:1px solid rgba(180,205,245,.12); border-radius:12px;
        padding:11px 12px; background:rgba(255,255,255,.035);
    }}
    .portal-benefits b {{ color:#73DDD6 !important; font-size:11px; }}
    .portal-benefits span {{ color:#D8E4F6 !important; font-size:11px; line-height:1.35; }}
    .topline {{
        background:radial-gradient(circle at 90% 15%,rgba(20,184,166,.18),transparent 26%),
        linear-gradient(115deg,#111D35 0%,#172A4B 58%,#103B43 100%) !important;
        border:1px solid #2A3D5D !important;
    }}
    .topline .page-title {{ color:#F6F8FF !important; }}
    .topline .page-subtitle {{ color:#BDCAE0 !important; }}
    .topline .eyebrow {{ color:#77E1D8 !important; }}
    .hero-chips span {{ color:#E2EDFF !important; background:rgba(255,255,255,.07) !important; border-color:rgba(191,211,255,.17) !important; }}
    .section-heading-title {{ color:#F0F5FF !important; }}
    .prompt-card {{
        background:linear-gradient(145deg,#131E32,#17253D) !important;
        border:1px solid #2B3D59 !important; border-radius:18px !important;
        box-shadow:0 9px 24px rgba(0,0,0,.17) !important;
    }}
    .prompt-card:hover {{ background:linear-gradient(145deg,#192944,#1A2E4B) !important; border-color:#46658F !important; }}
    .prompt-title {{ color:#F3F6FF !important; }}
    .prompt-desc {{ color:#B1C0D8 !important; }}
    .prompt-icon {{ background:#22385A !important; }}
    /* Streamlit buttons under topic cards were white because their default styles won. */
    [data-testid="stMain"] .stButton > button {{
        background:#172640 !important; color:#EAF0FF !important;
        border:1px solid #344A6A !important; border-radius:12px !important;
    }}
    [data-testid="stMain"] .stButton > button * {{ color:#EAF0FF !important; }}
    [data-testid="stMain"] .stButton > button:hover {{ background:#223858 !important; border-color:#5276A7 !important; }}
    [data-testid="stMain"] [data-testid="stFormSubmitButton"] button,
    [data-testid="stMain"] [data-testid="stFormSubmitButton"] button[kind="primary"] {{
        background:linear-gradient(100deg,#3478FF,#2359E8) !important;
        color:#FFFFFF !important; border:1px solid #3975F5 !important;
    }}
    [data-testid="stMain"] [data-testid="stFormSubmitButton"] button * {{ color:#FFFFFF !important; }}
    [data-testid="stMain"] [data-testid="stChatMessage"] {{
        background:#131F33 !important; border:1px solid #2B3D59 !important;
        border-radius:17px !important; color:#EEF3FF !important;
    }}
    [data-testid="stMain"] [data-testid="stChatMessage"] p,
    [data-testid="stMain"] [data-testid="stChatMessage"] span {{ color:#EEF3FF !important; }}
    [data-testid="stMain"] .info-card {{
        background:#131F33 !important; border:1px solid #2B3D59 !important;
    }}
    [data-testid="stMain"] .info-card .card-title {{ color:#F3F6FF !important; }}
    [data-testid="stMain"] .info-card .card-desc {{ color:#B1C0D8 !important; }}
    [data-testid="stMain"] [data-testid="stTextInput"] input {{
        background:#0B1527 !important; color:#F3F6FC !important;
        -webkit-text-fill-color:#F3F6FC !important; border:1px solid #354B6B !important;
    }}
    [data-testid="stMain"] [data-testid="stTextInput"] input::placeholder {{
        color:#91A4C1 !important; -webkit-text-fill-color:#91A4C1 !important;
    }}
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{ color:#EAF0FF !important; }}
    [data-testid="stSidebar"] .stButton > button:not([kind="primary"]) {{
        background:#14213A !important; color:#EAF0FF !important; border-color:#304362 !important;
    }}
    [data-testid="stSidebar"] .stButton > button:not([kind="primary"]) * {{ color:#EAF0FF !important; }}
    .footer-note {{ color:#91A2BD !important; }}
    @media(max-width:750px) {{
        .portal-topline {{ align-items:flex-start; flex-wrap:wrap; }}
        .portal-status {{ margin-left:0; }}
        .portal-benefits {{ grid-template-columns:1fr; }}
        .portal-heading {{ font-size:24px; }}
    }}

    
    /* FIX: topic and empty-chat panels must never inherit Streamlit's white surface */
    [data-testid="stAppViewContainer"] [data-testid="stMain"] .prompt-card,
    [data-testid="stAppViewContainer"] [data-testid="stMain"] div.prompt-card,
    [data-testid="stAppViewContainer"] [data-testid="stMain"] .info-card,
    [data-testid="stAppViewContainer"] [data-testid="stMain"] div.info-card {{
        background-color: #131F33 !important;
        background-image: linear-gradient(145deg, #131F33, #17253D) !important;
        color: #EEF3FF !important;
        border: 1px solid #2B3D59 !important;
        box-shadow: 0 8px 22px rgba(0, 0, 0, 0.18) !important;
    }}
    [data-testid="stAppViewContainer"] [data-testid="stMain"] .prompt-title,
    [data-testid="stAppViewContainer"] [data-testid="stMain"] .info-card .card-title {{
        color: #F3F6FF !important;
    }}
    [data-testid="stAppViewContainer"] [data-testid="stMain"] .prompt-desc,
    [data-testid="stAppViewContainer"] [data-testid="stMain"] .info-card .card-desc {{
        color: #B9C8DE !important;
    }}
    [data-testid="stAppViewContainer"] [data-testid="stMain"] .prompt-icon {{
        background: #22385A !important;
    }}
    [data-testid="stAppViewContainer"] [data-testid="stMain"] .stButton > button,
    [data-testid="stAppViewContainer"] [data-testid="stMain"] .stButton > button p,
    [data-testid="stAppViewContainer"] [data-testid="stMain"] .stButton > button span {{
        background-color: #172640 !important;
        color: #F3F6FF !important;
        -webkit-text-fill-color: #F3F6FF !important;
        border-color: #344A6A !important;
    }}
    [data-testid="stAppViewContainer"] [data-testid="stMain"] .stButton > button:hover {{
        background-color: #223858 !important;
        border-color: #5276A7 !important;
    }}
    [data-testid="stAppViewContainer"] [data-testid="stMain"] [data-testid="stChatMessage"] {{
        background: #131F33 !important;
        color: #EEF3FF !important;
        border: 1px solid #2B3D59 !important;
    }}
    [data-testid="stAppViewContainer"] [data-testid="stMain"] [data-testid="stChatMessage"] p {{
        color: #EEF3FF !important;
    }}
    [data-testid="stAppViewContainer"] [data-testid="stMain"] hr {{
        border-color: #2B3D59 !important;
    }}

    
    /* Chat transcript: assistant on the left, student on the right */
    .chat-row {{
        display:flex; align-items:flex-start; gap:12px;
        width:100%; margin:14px 0 20px; box-sizing:border-box;
    }}
    .assistant-row {{ justify-content:flex-start; padding-right:12%; }}
    .user-row {{ justify-content:flex-end; padding-left:12%; }}
    .chat-avatar {{
        flex:0 0 38px; width:38px; height:38px; border-radius:13px;
        display:flex; align-items:center; justify-content:center;
        font-size:17px; font-weight:800; box-sizing:border-box;
    }}
    .assistant-avatar {{
        color:#073B3A !important; background:#BDF7EC;
        border:1px solid #8AE5D5;
    }}
    .user-avatar {{
        color:#FFFFFF !important; background:linear-gradient(140deg,#3478FF,#2359E8);
        border:1px solid #5D8FFF;
    }}
    .chat-bubble {{
        max-width:calc(100% - 50px); padding:15px 17px;
        border-radius:17px; box-sizing:border-box;
        box-shadow:0 8px 22px rgba(0,0,0,.12);
    }}
    .assistant-bubble {{
        background:linear-gradient(145deg,#142139,#172943);
        border:1px solid #304767; border-top-left-radius:5px;
        color:#EDF4FF !important;
    }}
    .user-bubble {{
        background:linear-gradient(145deg,#244D9B,#1E40AF);
        border:1px solid #3F6FD0; border-top-right-radius:5px;
        color:#FFFFFF !important;
    }}
    .chat-sender {{
        font-size:10px; font-weight:800; letter-spacing:1.1px;
        margin-bottom:8px; color:#83E6D9 !important;
    }}
    .chat-sender span {{ color:#9FB2D0 !important; font-weight:600; }}
    .user-bubble .chat-sender {{ color:#DCE8FF !important; }}
    .chat-message-text {{
        font-size:14px; line-height:1.75; overflow-wrap:anywhere;
        white-space:normal; color:#EDF4FF !important;
    }}
    .user-bubble .chat-message-text {{ color:#FFFFFF !important; }}
    @media(max-width:700px) {{
        .assistant-row {{ padding-right:2%; }}
        .user-row {{ padding-left:2%; }}
        .chat-bubble {{ padding:12px 13px; }}
    }}

    
    /* Voice input wrapper: remove Streamlit's default white strip and blend it into dark UI */
    [data-testid="stMain"] [data-testid="stCustomComponentV1"],
    [data-testid="stMain"] iframe,
    [data-testid="stMain"] [data-testid="stVerticalBlock"] > div:has(> [data-testid="stCustomComponentV1"]) {{
        background: #0A1020 !important;
        border: 0 !important;
        box-shadow: none !important;
    }}
    [data-testid="stMain"] [data-testid="stCustomComponentV1"] {{
        min-height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }}
    /* If the voice widget has its own frame, make the exposed frame transparent */
    [data-testid="stMain"] iframe {{
        color-scheme: dark !important;
    }}
    /* Hide the unused empty white strip only when it is the blank component frame */
    [data-testid="stMain"] [data-testid="stCustomComponentV1"] > div {{
        background: #0A1020 !important;
    }}
    [data-testid="stMain"] [data-testid="stTextInput"] > div {{
        background: transparent !important;
    }}
    [data-testid="stMain"] [data-testid="stForm"] {{
        background: #111B2E !important;
        border: 1px solid #2C3D58 !important;
        border-radius: 16px !important;
        padding: 12px !important;
    }}
    [data-testid="stMain"] [data-testid="stTextInput"] input {{
        background: #0B1527 !important;
        color: #F3F6FC !important;
        -webkit-text-fill-color: #F3F6FC !important;
        border: 1px solid #354B6B !important;
        border-radius: 11px !important;
        min-height: 46px !important;
    }}
    [data-testid="stMain"] [data-testid="stTextInput"] input::placeholder {{
        color: #91A4C1 !important;
        -webkit-text-fill-color: #91A4C1 !important;
        opacity: 1 !important;
    }}


    /* Compact microphone control: small square aligned with the message field */
    [data-testid="stMain"] [data-testid="stCustomComponentV1"] {{
        box-sizing: border-box !important;
        width: 42px !important;
        min-width: 42px !important;
        max-width: 42px !important;
        height: 42px !important;
        min-height: 42px !important;
        max-height: 42px !important;
        overflow: hidden !important;
        background: #111B2E !important;
        border: 1px solid #354B6B !important;
        border-radius: 10px !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
        flex: 0 0 42px !important;
        align-self: end !important;
    }}
    [data-testid="stMain"] [data-testid="stCustomComponentV1"] iframe {{
        display: block !important;
        box-sizing: border-box !important;
        width: 40px !important;
        min-width: 40px !important;
        max-width: 40px !important;
        height: 40px !important;
        min-height: 40px !important;
        max-height: 40px !important;
        padding: 0 !important;
        margin: 0 !important;
        border: 0 !important;
        overflow: hidden !important;
        background: #111B2E !important;
    }}
    [data-testid="stMain"] [data-testid="stElementContainer"]:has([data-testid="stCustomComponentV1"]) {{
        box-sizing: border-box !important;
        width: 42px !important;
        min-width: 42px !important;
        max-width: 42px !important;
        height: 42px !important;
        min-height: 42px !important;
        max-height: 42px !important;
        padding: 0 !important;
        margin: 0 !important;
        flex: 0 0 42px !important;
    }}
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] {{
        align-items: end !important;
        gap: 0.4rem !important;
    }}
    [data-testid="stMain"] [data-testid="stTextInput"] input {{
        min-height: 42px !important;
        height: 42px !important;
        border-radius: 10px !important;
    }}
    [data-testid="stMain"] button[kind="primary"] {{
        min-height: 42px !important;
        height: 42px !important;
        border-radius: 10px !important;
    }}
    /* Keep the voice helper line subtle and close to the composer */
    [data-testid="stMain"] [data-testid="stCaptionContainer"] {{
        margin-top: 0.15rem !important;
        margin-bottom: 0 !important;
        padding-top: 0 !important;
        line-height: 1.25 !important;
    }}

    /* FIX: remove white outer page strips */
    html,
    body,
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"],
    section[data-testid="stMain"] {{
        background: #0A1020 !important;
        background-color: #0A1020 !important;
        color: #F3F6FF !important;
    }}

    /* Make the main content occupy the available width */
    [data-testid="stMain"] {{
        background: #0A1020 !important;
        margin: 0 !important;
        padding: 0 !important;
    }}

    [data-testid="stMainBlockContainer"] {{
        background: #0A1020 !important;
        max-width: 100% !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 1.5rem 2rem 2rem !important;
        box-sizing: border-box !important;
    }}

    /* Remove the white background around the app */
    [data-testid="stAppViewContainer"] > .main,
    [data-testid="stAppViewContainer"] .main .block-container {{
        background: #0A1020 !important;
        color: #F3F6FF !important;
    }}

    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"] {{
        background: #0A1020 !important;
    }}

    /* FINAL FIX: paint the full browser viewport, including below the app content */
    html, body, #root, .stApp {{
        min-height: 100vh !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        background: #0A1020 !important;
        background-color: #0A1020 !important;
        color: #F3F6FF !important;
    }}
    [data-testid="stAppViewContainer"] {{
        min-height: 100vh !important;
        width: 100% !important;
        background: #0A1020 !important;
        background-color: #0A1020 !important;
    }}
    [data-testid="stMain"] {{
        min-height: 100vh !important;
        width: 100% !important;
        background: #0A1020 !important;
        background-color: #0A1020 !important;
    }}
    [data-testid="stMainBlockContainer"],
    [data-testid="stAppViewContainer"] .main,
    [data-testid="stAppViewContainer"] .main .block-container {{
        background: #0A1020 !important;
        background-color: #0A1020 !important;
        max-width: 100% !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }}
    /* Streamlit may reserve bottom space for its footer; keep that area dark too. */
    footer, [data-testid="stBottom"] {{
        background: #0A1020 !important;
        color: #0A1020 !important;
    }}

    </style>
    """,
    unsafe_allow_html=True,
)

# Streamlit's built-in elements can retain theme-dependent defaults. These
# light-only refinements make cards, controls, chat bubbles and navigation
# feel consistent without changing the dark theme that already looks good.
if False and not st.session_state.dark_mode:
    st.markdown(
        """
        <style>
        /* Bright, calm canvas with crisp white working surfaces */
        [data-testid="stAppViewContainer"], [data-testid="stMain"],
        [data-testid="stMainBlockContainer"] { background:#F3F6FB !important; }
        [data-testid="stSidebar"], [data-testid="stSidebar"] > div {
            background:#FFFFFF !important;
            border-right:1px solid #D9E2EF !important;
        }
        .brand-subtitle, .sidebar-label, .profile-role,
        .section-heading-note, .page-subtitle, .prompt-desc,
        .chat-heading-subtitle, .footer-note,
        [data-testid="stCaptionContainer"] {
            color:#586981 !important;
        }
        .profile-card {
            background:#F5F8FE !important;
            border-color:#D9E2EF !important;
            box-shadow:0 3px 12px rgba(25,45,80,.035);
        }
        .avatar { background:#E4ECFF !important; color:#2446B7 !important; }
        .prompt-card {
            background:#FFFFFF !important;
            border-color:#DFE6F1 !important;
            box-shadow:0 5px 18px rgba(29,54,94,.055) !important;
        }
        .prompt-card:hover {
            border-color:#B8C9F6 !important;
            box-shadow:0 9px 24px rgba(49,87,213,.09) !important;
        }
        .prompt-icon { background:#EDF2FF !important; }
        .chat-heading-icon { background:#E4F7F5 !important; color:#087F79 !important; }
        .status-pill {
            background:#FFFFFF !important;
            border-color:#D9E2EF !important;
            color:#465873 !important;
            box-shadow:0 3px 10px rgba(29,54,94,.035);
        }
        [data-testid="stChatMessage"] {
            background:#FFFFFF !important;
            border:1px solid #DFE6F1 !important;
            box-shadow:0 3px 12px rgba(29,54,94,.035) !important;
        }
        [data-testid="stChatMessage"] p,
        [data-testid="stChatMessage"] li,
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
            color:#172640 !important;
        }
        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea {
            background:#FFFFFF !important;
            color:#172640 !important;
            -webkit-text-fill-color:#172640 !important;
            border:1px solid #CAD6E6 !important;
            box-shadow:0 2px 7px rgba(29,54,94,.025) !important;
        }
        div[data-testid="stTextInput"] input:focus,
        div[data-testid="stTextArea"] textarea:focus {
            border-color:#3157D5 !important;
            box-shadow:0 0 0 3px rgba(49,87,213,.11) !important;
        }
        div[data-testid="stTextInput"] input::placeholder,
        div[data-testid="stTextArea"] textarea::placeholder {
            color:#75849A !important;
            -webkit-text-fill-color:#75849A !important;
        }
        .stButton > button[kind="secondary"] {
            background:#FFFFFF !important;
            color:#263954 !important;
            border-color:#D9E2EF !important;
        }
        .stButton > button[kind="secondary"]:hover {
            background:#F3F6FF !important;
            color:#2446B7 !important;
            border-color:#AFC2F4 !important;
        }
        [data-testid="stToggle"] label,
        [data-testid="stCheckbox"] label,
        [data-testid="stRadio"] label { color:#263954 !important; }
        [data-testid="stAlert"] { border-radius:12px !important; }
        hr { border-color:#DFE6F1 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# HELPERS
# =========================================================
def show_brand():
    st.markdown(
        """
        <div class="brand-row">
            <div class="brand-mark">✦</div>
            <div>
                <div class="brand-name">Campus Companion</div>
                <div class="brand-subtitle">AI-powered student support</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def load_students():
    """Load local demo student records without exposing the full file."""
    try:
        with open(STUDENTS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            students = data.get("students", [])
            return students if isinstance(students, list) else []
    except (OSError, json.JSONDecodeError):
        pass
    return []


def get_student_display_name(user_record):
    """Return the matching student name; safely fall back to username."""
    if not user_record:
        return "Student"
    student_id = str(user_record.get("student_id") or "").strip().upper()
    if student_id:
        for student in load_students():
            record_id = str(student.get("student_id") or student.get("id") or "").strip().upper()
            if record_id == student_id:
                return (
                    student.get("name")
                    or student.get("student_name")
                    or student.get("Student_Name")
                    or user_record.get("username")
                    or "Student"
                )
    return user_record.get("username") or "Student"


def safe_text(value):
    return html.escape(str(value or ""))


def initials(name):
    parts = str(name or "Student").split()
    return "".join(part[0] for part in parts[:2]).upper() or "ST"


def show_login():
    st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
    left, right = st.columns([1.05, 0.95], gap="large", vertical_alignment="center")

    with left:
        st.markdown(
            """
            <div class="login-visual">
                <div class="login-logo">
                    <div class="login-logo-mark">✦</div>
                    <div>
                        <div class="login-logo-title">Campus Companion</div>
                        <div class="login-logo-sub">AI-powered student support</div>
                    </div>
                </div>
                <div class="login-kicker">YOUR CAMPUS. ONE ASSISTANT.</div>
                <div class="login-headline">Student support,<br>made simpler.</div>
                <div class="login-copy">A single place to get guidance on student fees, scholarships, academic policies, and everyday campus questions.</div>
                <div class="login-feature-row"><span class="login-feature-check">✓</span><span>Personalized student assistance</span></div>
                <div class="login-feature-row"><span class="login-feature-check">✓</span><span>Answers grounded in campus information</span></div>
                <div class="login-feature-row"><span class="login-feature-check">✓</span><span>Your conversations, organized in one place</span></div>
                <div class="login-bottom">A smarter way to navigate student life.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            """
            <div class="portal-welcome">
                <div class="portal-topline">
                    <div class="portal-icon">✦</div>
                    <div>
                        <div class="portal-kicker">CAMPUS COMPANION · STUDENT PORTAL</div>
                        <div class="portal-heading">Welcome back</div>
                        <div class="portal-copy">Your personal campus support, all in one place.</div>
                    </div>
                    <div class="portal-status"><span></span> Secure sign-in</div>
                </div>
                <div class="portal-benefits">
                    <div><b>01</b><span>Fee &amp; scholarship guidance</span></div>
                    <div><b>02</b><span>Trusted campus information</span></div>
                    <div><b>03</b><span>Your own private conversations</span></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Sign in  →", type="primary", use_container_width=True)

        if submitted:
            if not username.strip() or not password:
                st.error("Please enter both your username and password.")
            else:
                result = authenticate_user(username.strip(), password)
                if result:
                    st.session_state.user = result
                    st.session_state.active_conversation_id = None
                    st.session_state.pending_question = None
                    st.session_state.composer_input = ""
                    st.session_state.last_voice_text = ""
                    st.rerun()
                else:
                    st.error("Incorrect username or password. Please try again.")

        st.markdown('<div class="footer-note">Secure student workspace · Campus Companion</div>', unsafe_allow_html=True)



# =========================================================
# QUESTION PROCESSING
# =========================================================
def process_question(question):
    question = str(question or "").strip()
    if not question:
        return

    current_user = st.session_state.user
    if not current_user:
        st.error("Please sign in again.")
        return

    user_id = current_user["id"]
    conversation_id = st.session_state.active_conversation_id

    if conversation_id is None:
        conversation_id = create_conversation(user_id, question[:45])
        st.session_state.active_conversation_id = conversation_id

    previous_rows = get_messages(user_id, conversation_id) or []
    previous_messages = []
    for row in previous_rows:
        try:
            previous_messages.append({"role": row["role"], "content": row["content"]})
        except (TypeError, KeyError, IndexError):
            if isinstance(row, dict):
                previous_messages.append({"role": row.get("role"), "content": row.get("content", "")})

    add_message(user_id, conversation_id, "user", question)
    if len(previous_messages) == 0:
        rename_conversation(user_id, conversation_id, question[:45])

    try:
        from agent import ask_agent
        with st.spinner("Searching campus information..."):
            answer = ask_agent(
                question,
                conversation_history=previous_messages,
                authorized_student_id=current_user.get("student_id"),
            )
        if not answer:
            answer = "I couldn't find a response. Please try asking in a different way."
    except Exception as error:
        print(f"[App agent error] {type(error).__name__}: {error}")
        answer = "I'm having trouble responding right now. Please try again shortly. If the issue continues, check the application terminal."

    add_message(user_id, conversation_id, "assistant", str(answer))


# =========================================================
# LOGIN GATE
# =========================================================
if st.session_state.user is None:
    show_login()
    st.stop()


# =========================================================
# CURRENT USER
# =========================================================
user = st.session_state.user
user_id = user["id"]
role = user.get("role", "student")
display_name = get_student_display_name(user)


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    show_brand()
    st.markdown(
        f"""
        <div class="profile-card">
            <div class="avatar">{safe_text(initials(display_name))}</div>
            <div>
                <div class="profile-name">{safe_text(display_name)}</div>
                <div class="profile-role">{safe_text(role.title())} workspace</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sidebar-label">Workspace</div>', unsafe_allow_html=True)

    if st.button("＋  New conversation", use_container_width=True, type="primary", key="new_chat"):
        st.session_state.active_conversation_id = None
        st.session_state.pending_question = None
        st.session_state.composer_input = ""
        st.session_state.last_voice_text = ""
        st.rerun()

    st.markdown('<div class="sidebar-label">Recent conversations</div>', unsafe_allow_html=True)
    conversations = list_conversations(user_id)
    if not conversations:
        st.caption("Your conversations will appear here.")

    for conversation in conversations:
        conv_id = conversation["id"]
        title = conversation["title"] or "New conversation"
        col1, col2 = st.columns([0.83, 0.17], gap="small")
        with col1:
            is_active = st.session_state.active_conversation_id == conv_id
            label = ("●  " if is_active else "   ") + title[:25]
            if st.button(label, key=f"open_chat_{conv_id}", use_container_width=True):
                st.session_state.active_conversation_id = conv_id
                st.session_state.pending_question = None
                st.session_state.composer_input = ""
                st.session_state.last_voice_text = ""
                st.rerun()
        with col2:
            if st.button("⋯", key=f"delete_chat_{conv_id}", help="Delete this conversation"):
                delete_conversation(user_id, conv_id)
                if st.session_state.active_conversation_id == conv_id:
                    st.session_state.active_conversation_id = None
                st.rerun()

    st.divider()
    st.caption("Campus Companion · AI Student Support")
    if st.button("↪  Sign out", use_container_width=True, key="logout_button"):
        st.session_state.user = None
        st.session_state.active_conversation_id = None
        st.session_state.pending_question = None
        st.session_state.composer_input = ""
        st.session_state.last_voice_text = ""
        st.rerun()



# =========================================================
# ADMIN WORKSPACE — APPROVAL REVIEW
# =========================================================
if role == "admin":
    import json
    from approvals import APPROVAL_FILE, decide_approval

    st.markdown(
        """
        <div class="eyebrow">ADMIN WORKSPACE</div>
        <div class="page-title">Course-change approvals</div>
        <div class="page-subtitle">
            Review student requests and approve or reject them.
            Decisions are recorded in the audit log.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not APPROVAL_FILE.exists():
        st.info("There are no course-change requests yet.")
        st.stop()

    requests = []

    with open(APPROVAL_FILE, "r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                requests.append(json.loads(line))

    pending_requests = [
        request for request in requests
        if request.get("status") == "pending"
    ]

    if not pending_requests:
        st.success("There are no pending requests.")
    else:
        for request in pending_requests:
            with st.container(border=True):
                st.write(f"**Student ID:** {request['student_id']}")
                st.write(f"**Request:** {request['details']}")
                st.caption(f"Request ID: {request['request_id']}")

                col1, col2 = st.columns(2)

                with col1:
                    if st.button(
                        "Approve request",
                        key=f"approve_{request['request_id']}",
                        type="primary",
                    ):
                        result = decide_approval(
                            request_id=request["request_id"],
                            approved=True,
                            reviewer_id=str(user_id),
                            reviewer_role=role,
                        )

                        if result.get("success"):
                            st.success(result["message"])
                        else:
                            st.error(result["error"])

                        st.rerun()

                with col2:
                    if st.button(
                        "Reject request",
                        key=f"reject_{request['request_id']}",
                    ):
                        result = decide_approval(
                            request_id=request["request_id"],
                            approved=False,
                            reviewer_id=str(user_id),
                            reviewer_role=role,
                        )

                        if result.get("success"):
                            st.warning(result["message"])
                        else:
                            st.error(result["error"])

                        st.rerun()

    st.stop()



# =========================================================
# STUDENT HOME
# =========================================================
st.markdown(
    f"""
    <div class="topline">
        <div>
            <div class="eyebrow">YOUR STUDENT SUPPORT WORKSPACE</div>
            <div class="page-title">Hello, {safe_text(display_name)}.</div>
            <div class="page-subtitle">What can I help you with today? Ask a question about fees, scholarships, campus policies, or student support.</div>
            <div class="hero-chips">
                <span>♙ Personalized answers</span><span>▤ Campus policies</span><span>♙ Secure &amp; private</span><span>◷ Available 24/7</span>
            </div>
        </div>
        <div class="status-pill"><span class="status-dot"></span> Assistant available</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="section-heading">
        <div class="section-heading-title">Start with a quick question</div>
        <div class="section-heading-note">Choose a topic to get started</div>
    </div>
    """,
    unsafe_allow_html=True,
)

quick_prompts = [
    ("💳", "Fee status", "Check your remaining fee balance.", "How much fee do I have left to pay?"),
    ("🎓", "Scholarships", "Review your scholarship status.", "Can you check my scholarship status?"),
    ("📘", "Academic policies", "Understand campus policy guidance.", "What should I know about course changes?"),
    ("🧭", "Student support", "Find the right next step for an issue.", "How can I get help with a student issue?"),
]
cols = st.columns(4, gap="medium")
for index, (emoji, title, description, question) in enumerate(quick_prompts):
    with cols[index]:
        st.markdown(
            f"""
            <div class="prompt-card">
                <div class="prompt-icon">{emoji}</div>
                <div class="prompt-title">{safe_text(title)}</div>
                <div class="prompt-desc">{safe_text(description)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"Explore topic  ↗", key=f"quick_prompt_{index}", use_container_width=True):
            st.session_state.pending_question = question
            st.rerun()


# Process quick prompts or a submitted question before rendering history.
if st.session_state.pending_question:
    question_to_process = st.session_state.pending_question
    st.session_state.pending_question = None
    process_question(question_to_process)
    st.rerun()


# =========================================================
# CHAT HISTORY
# =========================================================
st.markdown(
    """
    <div class="section-heading">
        <div class="section-heading-title">Your conversation</div>
        <div class="section-heading-note">Private to your account</div>
    </div>
    <div class="chat-heading">
        <div class="chat-heading-icon">✦</div>
        <div>
            <div class="chat-heading-title">Campus Companion AI</div>
            <div class="chat-heading-subtitle">Student support assistant · Ask naturally, get guidance</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

active_id = st.session_state.active_conversation_id
messages = (get_messages(user_id, active_id) or []) if active_id is not None else []

if not messages:
    st.markdown(
        """
        <div class="prompt-card" style="padding:23px;margin-bottom:14px;">
            <div class="prompt-title" style="font-size:15px;">How can I help you today?</div>
            <div class="prompt-desc" style="font-size:13px;margin-top:7px;">Select one of the topics above or type a question below. I can help you navigate common student services and campus information.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    for message in messages:
        message_role = str(message["role"])
        message_content = html.escape(str(message.get("content", ""))).replace("\\n", "<br>")
        if message_role == "assistant":
            st.markdown(
                f"""
                <div class="chat-row assistant-row">
                    <div class="chat-avatar assistant-avatar">✦</div>
                    <div class="chat-bubble assistant-bubble">
                        <div class="chat-sender">CAMPUS COMPANION <span>· AI ASSISTANT</span></div>
                        <div class="chat-message-text">{message_content}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="chat-row user-row">
                    <div class="chat-bubble user-bubble">
                        <div class="chat-sender">YOU</div>
                        <div class="chat-message-text">{message_content}</div>
                    </div>
                    <div class="chat-avatar user-avatar">👤</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# =========================================================
# INPUT COMPOSER — persistent voice + text + send controls
# =========================================================
st.markdown(
    '<div class="section-heading"><div class="section-heading-title">Ask a question</div>'
    '<div class="section-heading-note">Type a message or use the microphone</div></div>',
    unsafe_allow_html=True,
)

# Keep the voice control in a compact column so its component iframe cannot
# expand into the long white strip shown by the default component layout.
voice_col, text_col, send_col = st.columns([0.30, 8.0, 0.88], gap="small", vertical_alignment="bottom")

with voice_col:
    if VOICE_AVAILABLE:
        try:
            voice_text = speech_to_text(
                language="en",
                start_prompt="🎙",
                stop_prompt="■",
                just_once=True,
                use_container_width=False,
                key="student_voice",
            )
            if voice_text and voice_text.strip() and voice_text != st.session_state.last_voice_text:
                st.session_state.composer_input = voice_text.strip()
                st.session_state.last_voice_text = voice_text
        except TypeError:
            # Older streamlit-mic-recorder versions do not support every optional argument.
            try:
                voice_text = speech_to_text(
                    language="en",
                    start_prompt="🎙",
                    stop_prompt="■",
                    just_once=True,
                    key="student_voice_fallback",
                )
                if voice_text and voice_text.strip() and voice_text != st.session_state.last_voice_text:
                    st.session_state.composer_input = voice_text.strip()
                    st.session_state.last_voice_text = voice_text
            except Exception as error:
                print(f"[Voice input error] {type(error).__name__}: {error}")
        except Exception as error:
            print(f"[Voice input error] {type(error).__name__}: {error}")
    else:
        st.caption("Mic unavailable")


def handle_send():
    question = str(st.session_state.get("composer_input", "")).strip()
    if question:
        st.session_state.pending_question = question
        st.session_state.composer_input = ""
        st.session_state.last_voice_text = ""

with text_col:
    st.text_input(
        "Your message",
        key="composer_input",
        placeholder="Ask about fees, scholarships, policies, or student support...",
        label_visibility="collapsed",
    )
with send_col:
    st.button(
        "➤",
        key="send_message_button",
        type="primary",
        use_container_width=True,
        help="Send message",
        on_click=handle_send,
    )

if VOICE_AVAILABLE:
    st.caption("Tap the microphone to dictate. Your spoken words will appear in the message field so you can review them before sending.")

# =========================================================
# FOOTER
# =========================================================
st.markdown(
    """
    <div class="footer-note">
        Campus Companion can make mistakes. Confirm important fee, scholarship, and academic decisions with the relevant college office.
    </div>
    """,
    unsafe_allow_html=True,
)
