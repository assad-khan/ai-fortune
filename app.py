"""
AI Fortune-Telling Booth – Streamlit POC
Madame Zara reads your destiny using your name and date of birth,
while you show your palm live on camera. Fortune delivered via HeyGen AI avatar.
"""

import datetime
import os
import time

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from streamlit_webrtc import webrtc_streamer, WebRtcMode

from services.fortune import generate_fortune, get_reading_context
from services.heygen import (
    fetch_avatars,
    fetch_voices,
    create_video,
    get_video_status,
)

# ─── Environment ──────────────────────────────────────────────────────────────
load_dotenv()
HEYGEN_KEY  = os.getenv("heygen_api", "")
OPENAI_KEY  = os.getenv("openai_api", "")
openai_client = OpenAI(api_key=OPENAI_KEY)

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Madame Zara – Fortune Booth",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.stApp {
    background: radial-gradient(ellipse at top, #1a0a2e 0%, #0d0221 55%, #000010 100%);
    color: #e8d5f5;
}
section[data-testid="stSidebar"] {
    background: #110720;
    border-right: 1px solid #4a2070;
}
section[data-testid="stSidebar"] * { color: #c9a0dc !important; }

.zara-title {
    font-size: 2.6em;
    text-align: center;
    color: #d4a8ff;
    text-shadow: 0 0 22px #9b59b6, 0 0 45px #6c3483;
    font-family: Georgia, serif;
    margin-bottom: 2px;
}
.zara-sub {
    text-align: center;
    color: #9b72cb;
    font-style: italic;
    font-size: 1.05em;
    margin-top: 0;
}

/* Avatar idle glow */
.avatar-idle img {
    border-radius: 16px;
    border: 2px solid #6c3483;
    animation: avatarGlow 3s ease-in-out infinite;
    width: 100%;
}
@keyframes avatarGlow {
    0%, 100% { box-shadow: 0 0 20px rgba(155,89,182,0.5), 0 0 40px rgba(108,52,131,0.3); }
    50%       { box-shadow: 0 0 50px rgba(155,89,182,0.9), 0 0 80px rgba(108,52,131,0.6); }
}

/* Scanning overlay on avatar */
.avatar-wrapper {
    position: relative;
    border-radius: 16px;
    overflow: hidden;
}
.scan-line {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, transparent, #c9a0dc, transparent);
    animation: scanDown 2.5s linear infinite;
}
@keyframes scanDown {
    0%   { top: 0%; opacity: 1; }
    90%  { top: 100%; opacity: 1; }
    100% { top: 100%; opacity: 0; }
}

/* Palm cam label */
.cam-label {
    text-align: center;
    color: #9b72cb;
    font-size: 0.88em;
    font-style: italic;
    margin-top: 8px;
}

/* Phase card */
.phase-card {
    background: rgba(74,32,112,0.2);
    border: 1px solid #4a2070;
    border-radius: 14px;
    padding: 18px 24px;
    text-align: center;
    margin: 10px 0;
}
.phase-emoji {
    font-size: 2.8em;
    display: block;
    margin-bottom: 8px;
    animation: pulse 2s infinite;
}
.phase-msg {
    font-size: 1.05em;
    color: #c9a0dc;
    font-style: italic;
}
@keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 1; }
    50%       { transform: scale(1.12); opacity: 0.75; }
}

/* Fortune card */
.fortune-card {
    background: linear-gradient(135deg, rgba(108,52,131,0.18), rgba(74,32,112,0.28));
    border: 1px solid #6c3483;
    border-radius: 16px;
    padding: 22px 30px;
    font-size: 1.1em;
    line-height: 1.85;
    color: #edd5ff;
    text-align: center;
    font-style: italic;
    box-shadow: 0 0 32px rgba(155,89,182,0.22);
    margin-top: 14px;
}

/* Astro badge */
.astro-badge {
    display: inline-block;
    background: rgba(108,52,131,0.3);
    border: 1px solid #6c3483;
    border-radius: 20px;
    padding: 4px 16px;
    font-size: 0.9em;
    color: #d4a8ff;
    margin: 4px;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #6c3483, #8e44ad) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 30px !important;
    padding: 12px 28px !important;
    font-size: 1em !important;
    width: 100% !important;
    box-shadow: 0 0 18px rgba(142,68,173,0.45);
    transition: box-shadow 0.25s, transform 0.2s;
}
.stButton > button:hover {
    box-shadow: 0 0 28px rgba(142,68,173,0.85) !important;
    transform: translateY(-2px);
}

.stProgress > div > div { background-color: #9b59b6 !important; }
.stTextInput input, .stDateInput input {
    background: rgba(26,10,46,0.8) !important;
    border: 1px solid #6c3483 !important;
    color: #e8d5f5 !important;
    border-radius: 8px !important;
}
hr { border-color: #4a2070 !important; }
div[data-testid="stAlert"] { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ─── Session state ─────────────────────────────────────────────────────────────
_defaults = {
    "stage": "welcome",       # welcome | input | generating | reveal
    "avatar_id": None,
    "voice_id": None,
    "avatar_preview_url": "", # for idle animation
    "name": "",
    "dob": None,
    "fortune_text": "",
    "video_url": "",
    "video_id": "",           # persists across reruns during polling
    "poll_count": 0,          # tracks polling cycles
    "poll_pct": 45,           # persists progress bar position
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ─── Sidebar ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_avatars(key: str) -> list[dict]:
    try:    return fetch_avatars(key)
    except Exception: return []

@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_voices(key: str) -> list[dict]:
    try:    return fetch_voices(key, language_prefix="en")
    except Exception: return []


with st.sidebar:
    st.markdown("### 🎭 Oracle Configuration")
    st.caption("Set the avatar and voice for the booth.")
    st.markdown("---")

    with st.spinner("Loading avatars…"):
        avatars = _fetch_avatars(HEYGEN_KEY)

    if avatars:
        avatar_ids     = [a["avatar_id"] for a in avatars]
        avatar_labels  = [f"{a.get('avatar_name','?')}  ({a.get('gender','–')})" for a in avatars]
        _def_av        = "Abigail_expressive_2024112501"
        _def_av_idx    = avatar_ids.index(_def_av) if _def_av in avatar_ids else 0
        chosen_idx     = st.selectbox("Avatar", range(len(avatar_labels)),
                                      format_func=lambda i: avatar_labels[i], index=_def_av_idx)
        chosen_avatar  = avatars[chosen_idx]
        st.session_state.avatar_id          = chosen_avatar["avatar_id"]
        st.session_state.avatar_preview_url = chosen_avatar.get("preview_image_url", "")

        if st.session_state.avatar_preview_url:
            st.image(st.session_state.avatar_preview_url, caption="Preview", width="stretch")
    else:
        st.error("Could not load avatars.")

    st.markdown("---")

    with st.spinner("Loading voices…"):
        voices = _fetch_voices(HEYGEN_KEY)

    if voices:
        voice_ids    = [v["voice_id"] for v in voices]
        voice_labels = [f"{v.get('name','?')}  ({v.get('gender','–')})" for v in voices]
        _def_vo      = "M2WosQ2Ju3f2b7jdddsj"
        _def_vo_idx  = voice_ids.index(_def_vo) if _def_vo in voice_ids else 0
        voice_idx    = st.selectbox("Voice", range(len(voice_labels)),
                                    format_func=lambda i: voice_labels[i], index=_def_vo_idx)
        st.session_state.voice_id = voices[voice_idx]["voice_id"]
    else:
        st.warning("Could not load voices.")

    st.markdown("---")
    st.caption("🔮 AI Fortune Booth — POC")


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _header(title: str, subtitle: str):
    st.markdown(f'<h1 class="zara-title">{title}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="zara-sub">{subtitle}</p>', unsafe_allow_html=True)
    st.markdown("---")


def _avatar_idle(preview_url: str, label: str = "Madame Zara is watching…"):
    """Render the avatar preview image with a scanning/glowing idle animation."""
    if preview_url:
        st.markdown(
            f"""
            <div class="avatar-wrapper avatar-idle">
                <img src="{preview_url}" style="width:100%; border-radius:16px;
                     border:2px solid #6c3483;
                     box-shadow: 0 0 30px rgba(155,89,182,0.5);" />
                <div class="scan-line"></div>
            </div>
            <div class="cam-label">{label}</div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div style="text-align:center; font-size:5em; animation:pulse 2s infinite;">🔮</div>'
            f'<div class="cam-label">{label}</div>',
            unsafe_allow_html=True,
        )


# ─── Stages ───────────────────────────────────────────────────────────────────

# ── Welcome ──────────────────────────────────────────────────────────────────
def show_welcome():
    _header("🔮 Madame Zara", "Ancient Wisdom · Modern Magic · Your Destiny Awaits")
    st.markdown("""
    <div style="text-align:center; color:#a678c8; padding:22px 0; font-size:1.06em; line-height:2;">
        The crystal ball glows. The stars have aligned.<br>
        Your future is written in the lines of your palm.<br>
        <em>Step forward, seeker, and reveal your destiny…</em>
    </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("✨  Begin Your Reading"):
            if not st.session_state.avatar_id or not st.session_state.voice_id:
                st.error("Please select an avatar and voice in the sidebar first.")
            else:
                st.session_state.stage = "input"
                st.rerun()


# ── Input: Name & DOB ─────────────────────────────────────────────────────────
def show_input():
    _header("🌟 Tell Me Who You Are", "The stars need your name and birth date to align")

    left, right = st.columns([1.2, 1])

    with left:
        st.markdown("""
        <div style="color:#a678c8; padding:10px 0 18px; font-size:1em; line-height:1.8;">
            <em>Every destiny is unique.<br>Share your details and let the cosmos speak…</em>
        </div>
        """, unsafe_allow_html=True)

        name = st.text_input("✦  Your Full Name", placeholder="e.g. Sofia Khalil")
        dob  = st.date_input(
            "✦  Date of Birth",
            value=datetime.date(1990, 1, 1),
            min_value=datetime.date(1900, 1, 1),
            max_value=datetime.date.today(),
        )
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔮  Reveal My Fortune"):
            if not name.strip():
                st.error("Please enter your name.")
            else:
                st.session_state.name  = name.strip()
                st.session_state.dob   = dob
                st.session_state.stage = "generating"
                st.rerun()

        st.markdown("---")
        if st.button("← Back"):
            st.session_state.stage = "welcome"
            st.rerun()

    with right:
        # Show avatar idling while user fills form
        _avatar_idle(
            st.session_state.avatar_preview_url,
            label="Madame Zara awaits your details…",
        )


# ── Generating ────────────────────────────────────────────────────────────────
def show_generating():
    name = st.session_state.name or "Seeker"
    dob: datetime.date | None = st.session_state.dob

    if not dob:
        st.error("Missing birth date. Please start over.")
        if st.button("Restart"):
            st.session_state.stage = "welcome"
            st.rerun()
        return

    ctx        = get_reading_context(name, dob)
    first_name = name.split()[0]

    _header("🌙 The Oracle Speaks…", f"Reading the cosmic blueprint of {first_name}")

    # Astro badges
    st.markdown(
        f'<div style="text-align:center; margin-bottom:14px;">'
        f'<span class="astro-badge">♈ {ctx["zodiac"]}</span>'
        f'<span class="astro-badge">🔢 Life Path {ctx["life_path"]}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Two-column layout: live palm cam | avatar idle
    cam_col, avatar_col = st.columns(2)

    with cam_col:
        st.markdown('<div class="cam-label" style="font-size:1em; margin-bottom:8px;">🖐 Hold your palm up to the camera</div>', unsafe_allow_html=True)
        webrtc_streamer(
            key="palm-live",
            mode=WebRtcMode.SENDRECV,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )

    with avatar_col:
        avatar_box = st.empty()
        if st.session_state.avatar_preview_url:
            avatar_box.markdown(
                f"""
                <div class="avatar-wrapper avatar-idle">
                    <img src="{st.session_state.avatar_preview_url}"
                         style="width:100%; border-radius:16px; border:2px solid #6c3483;
                                box-shadow: 0 0 30px rgba(155,89,182,0.5);" />
                    <div class="scan-line"></div>
                </div>
                <div class="cam-label">Madame Zara is preparing your reading…</div>
                """,
                unsafe_allow_html=True,
            )
        else:
            avatar_box.markdown(
                '<div style="text-align:center;font-size:5em;">🔮</div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    phases = [
        ("🔮", f"Consulting the ancient star charts for {first_name}…"),
        ("🌙", f"Your Life Path {ctx['life_path']} reveals hidden truths…"),
        ("✨", f"The {ctx['zodiac']} alignment is powerful today…"),
        ("🎴", "The oracle is weaving your destiny into words…"),
        ("🌟", "Madame Zara is preparing your message…"),
        ("🎭", "Almost ready… the vision is taking shape…"),
    ]

    try:
        # ── Step 1: Generate fortune (only once) ──────────────────────────
        if not st.session_state.fortune_text:
            emoji, msg = phases[0]
            st.markdown(
                f'<div class="phase-card"><span class="phase-emoji">{emoji}</span>'
                f'<div class="phase-msg">{msg}</div></div>',
                unsafe_allow_html=True,
            )
            st.progress(15)
            fortune = generate_fortune(name, dob, openai_client)
            st.session_state.fortune_text = fortune
            st.rerun()
            return

        fortune = st.session_state.fortune_text

        # ── Step 2: Submit to HeyGen (only once) ──────────────────────────
        if not st.session_state.video_id:
            emoji, msg = phases[1]
            st.markdown(
                f'<div class="phase-card"><span class="phase-emoji">{emoji}</span>'
                f'<div class="phase-msg">{msg}</div></div>',
                unsafe_allow_html=True,
            )
            st.progress(30)
            video_id = create_video(
                HEYGEN_KEY,
                st.session_state.avatar_id,
                st.session_state.voice_id,
                fortune,
            )
            st.session_state.video_id    = video_id
            st.session_state.poll_count  = 0
            st.session_state.poll_pct    = 45
            st.rerun()
            return

        # ── Step 3: Poll once per rerun ────────────────────────────────────
        d = get_video_status(HEYGEN_KEY, st.session_state.video_id)
        vid_status = d.get("status")

        if vid_status == "completed":
            url = d.get("video_url", "")
            if not url:
                raise RuntimeError("Video completed but no URL returned.")
            st.session_state.video_url  = url
            # Clear polling state for next session
            st.session_state.video_id   = ""
            st.session_state.poll_count = 0
            st.session_state.poll_pct   = 45
            st.session_state.stage      = "reveal"
            st.rerun()
            return

        if vid_status == "failed":
            raise RuntimeError(f"Rendering failed: {d.get('error', 'unknown')}")

        # Still processing — show current phase, teaser, progress
        st.session_state.poll_count += 1
        st.session_state.poll_pct    = min(st.session_state.poll_pct + 2, 93)

        phase_idx = 2 + st.session_state.poll_count // 2
        emoji, msg = phases[phase_idx % len(phases)]
        st.markdown(
            f'<div class="phase-card"><span class="phase-emoji">{emoji}</span>'
            f'<div class="phase-msg">{msg}</div></div>',
            unsafe_allow_html=True,
        )
        st.progress(st.session_state.poll_pct)
        st.markdown(
            f'<div class="fortune-card" style="opacity:0.85;">"{fortune}"</div>',
            unsafe_allow_html=True,
        )

        # Wait then rerun to poll again
        time.sleep(5)
        st.rerun()

    except Exception as exc:
        st.error(f"The crystal ball has gone dark: {exc}")
        # Reset polling state on error
        st.session_state.video_id    = ""
        st.session_state.fortune_text = ""
        st.session_state.poll_count  = 0
        st.session_state.poll_pct    = 45
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Try Again"):
                st.session_state.stage = "input"
                st.rerun()


# ── Reveal ────────────────────────────────────────────────────────────────────
def show_reveal():
    name = st.session_state.name or "Seeker"
    _header("🌟 Your Fortune", f"Madame Zara has spoken, {name.split()[0]}")

    if st.session_state.video_url:
        st.video(st.session_state.video_url)
    else:
        st.warning("Avatar video unavailable — showing text fortune only.")

    st.markdown(
        f'<div class="fortune-card">"{st.session_state.fortune_text}"</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔮  Read Another Fortune"):
            for k in ("fortune_text", "video_url", "name", "video_id"):
                st.session_state[k] = ""
            st.session_state.dob        = None
            st.session_state.poll_count = 0
            st.session_state.poll_pct   = 45
            st.session_state.stage      = "welcome"
            st.rerun()


# ─── Router ───────────────────────────────────────────────────────────────────
{
    "welcome":    show_welcome,
    "input":      show_input,
    "generating": show_generating,
    "reveal":     show_reveal,
}.get(st.session_state.stage, show_welcome)()
