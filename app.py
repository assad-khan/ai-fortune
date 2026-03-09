"""
AI Fortune-Telling Booth – Streamlit POC
Madame Zara reads your palm via GPT-4o Vision and delivers your fortune
through a HeyGen AI avatar video.
"""

import os
import time

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image

from services.palm import detect_palm
from services.fortune import generate_fortune
from services.heygen import (
    fetch_avatars,
    fetch_voices,
    create_video,
    get_video_status,
    poll_until_ready,
)

# ─── Environment ──────────────────────────────────────────────────────────────
load_dotenv()
HEYGEN_KEY = os.getenv("heygen_api", "")
OPENAI_KEY = os.getenv("openai_api", "")
openai_client = OpenAI(api_key=OPENAI_KEY)

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Madame Zara – Fortune Booth",
    page_icon="🔮",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ─── CSS theme ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Background */
.stApp {
    background: radial-gradient(ellipse at top, #1a0a2e 0%, #0d0221 55%, #000010 100%);
    color: #e8d5f5;
}
/* Sidebar */
section[data-testid="stSidebar"] {
    background: #110720;
    border-right: 1px solid #4a2070;
}
section[data-testid="stSidebar"] * { color: #c9a0dc !important; }

/* Headings */
.zara-title {
    font-size: 2.8em;
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

/* Fortune card */
.fortune-card {
    background: linear-gradient(135deg, rgba(108,52,131,0.18), rgba(74,32,112,0.28));
    border: 1px solid #6c3483;
    border-radius: 16px;
    padding: 26px 34px;
    font-size: 1.12em;
    line-height: 1.85;
    color: #edd5ff;
    text-align: center;
    font-style: italic;
    box-shadow: 0 0 32px rgba(155,89,182,0.22);
    margin-top: 18px;
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

/* Progress bar */
.stProgress > div > div { background-color: #9b59b6 !important; }

/* Divider */
hr { border-color: #4a2070 !important; }

/* Info / success / error */
div[data-testid="stAlert"] { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ─── Session state defaults ────────────────────────────────────────────────────
_defaults = {
    "stage": "welcome",          # welcome | scan | generating | reveal
    "avatar_id": None,
    "voice_id": None,
    "captured_image": None,      # PIL Image
    "fortune_text": "",
    "video_url": "",
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ─── Sidebar ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_avatars(key: str) -> list[dict]:
    try:
        return fetch_avatars(key)
    except Exception:
        return []


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_voices(key: str) -> list[dict]:
    try:
        return fetch_voices(key, language_prefix="en")
    except Exception:
        return []


with st.sidebar:
    st.markdown("### 🎭 Oracle Configuration")
    st.caption("Set the avatar and voice for the booth.")
    st.markdown("---")

    # Avatars
    with st.spinner("Loading avatars…"):
        avatars = _fetch_avatars(HEYGEN_KEY)

    if avatars:
        avatar_labels = [
            f"{a.get('avatar_name', 'Unnamed')}  ({a.get('gender', '–')})"
            for a in avatars
        ]
        avatar_ids = [a["avatar_id"] for a in avatars]
        # Default to Abigail (confirmed working); fall back to index 0
        _default_avatar = "Abigail_expressive_2024112501"
        _default_avatar_idx = avatar_ids.index(_default_avatar) if _default_avatar in avatar_ids else 0
        chosen_idx = st.selectbox(
            "Avatar", range(len(avatar_labels)),
            format_func=lambda i: avatar_labels[i],
            index=_default_avatar_idx,
        )
        chosen_avatar = avatars[chosen_idx]
        st.session_state.avatar_id = chosen_avatar["avatar_id"]

        preview = chosen_avatar.get("preview_image_url")
        if preview:
            st.image(preview, caption="Preview", use_container_width=True)
    else:
        st.error("Could not load avatars. Check HeyGen API key.")

    st.markdown("---")

    # Voices
    with st.spinner("Loading voices…"):
        voices = _fetch_voices(HEYGEN_KEY)

    if voices:
        voice_labels = [
            f"{v.get('name', '?')}  ({v.get('gender', '–')})"
            for v in voices
        ]
        voice_ids = [v["voice_id"] for v in voices]
        # Default to Amy (confirmed working); fall back to index 0
        _default_voice = "M2WosQ2Ju3f2b7jdddsj"
        _default_voice_idx = voice_ids.index(_default_voice) if _default_voice in voice_ids else 0
        voice_idx = st.selectbox(
            "Voice", range(len(voice_labels)),
            format_func=lambda i: voice_labels[i],
            index=_default_voice_idx,
        )
        st.session_state.voice_id = voices[voice_idx]["voice_id"]
    else:
        st.warning("Could not load voices.")

    st.markdown("---")
    st.caption("🔮 AI Fortune Booth — POC")


# ─── Stages ───────────────────────────────────────────────────────────────────

def _header(title: str, subtitle: str):
    st.markdown(f'<h1 class="zara-title">{title}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="zara-sub">{subtitle}</p>', unsafe_allow_html=True)
    st.markdown("---")


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

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✨  Begin Your Reading"):
            if not st.session_state.avatar_id or not st.session_state.voice_id:
                st.error("Please select an avatar and voice in the sidebar first.")
            else:
                st.session_state.stage = "scan"
                st.rerun()


# ── Palm Scan ────────────────────────────────────────────────────────────────
def show_scan():
    _header("🖐 Show Me Your Palm", "Hold your dominant hand open, palm facing the camera")

    st.info("📸 Centre your open palm in the frame, then click the capture button below.")

    img_data = st.camera_input("", label_visibility="collapsed")

    if img_data:
        image = Image.open(img_data)

        with st.spinner("🔍 Detecting your palm…"):
            detected, msg = detect_palm(image)

        if detected:
            st.success("✅ Palm detected! The oracle is awakening…")
            st.session_state.captured_image = image
            st.session_state.stage = "generating"
            time.sleep(0.8)
            st.rerun()
        else:
            st.error(f"❌ {msg}")

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("← Back"):
            st.session_state.stage = "welcome"
            st.rerun()


# ── Generating ───────────────────────────────────────────────────────────────
def show_generating():
    _header("🌙 The Oracle Speaks…", "Reading the ancient lines of your palm")

    image: Image.Image | None = st.session_state.captured_image
    if image is None:
        st.error("No palm image found. Please start over.")
        if st.button("Restart"):
            st.session_state.stage = "welcome"
            st.rerun()
        return

    progress = st.progress(0)
    status_box = st.empty()

    try:
        # ── Step 1: Generate fortune text ─────────────────────────────────
        status_box.markdown("🔮 *Reading your life line, heart line, fate line…*")
        fortune = generate_fortune(image, openai_client)
        st.session_state.fortune_text = fortune
        progress.progress(30)

        # ── Step 2: Submit video to HeyGen ────────────────────────────────
        status_box.markdown("🎭 *Awakening the oracle avatar…*")
        video_id = create_video(
            HEYGEN_KEY,
            st.session_state.avatar_id,
            st.session_state.voice_id,
            fortune,
        )
        progress.progress(50)

        # ── Step 3: Poll with live progress bar ───────────────────────────
        status_box.markdown("✨ *Weaving the vision together… (30–90 s)*")
        deadline = time.time() + 480  # 8 minutes
        poll_pct = 50
        while time.time() < deadline:
            time.sleep(5)
            d = get_video_status(HEYGEN_KEY, video_id)
            vid_status = d.get("status")

            if vid_status == "completed":
                url = d.get("video_url", "")
                if not url:
                    raise RuntimeError("Video completed but no URL returned.")
                st.session_state.video_url = url
                break

            if vid_status == "failed":
                raise RuntimeError(f"Rendering failed: {d.get('error', 'unknown')}")

            # Nudge progress bar forward while waiting
            poll_pct = min(poll_pct + 3, 93)
            progress.progress(poll_pct)
        else:
            raise RuntimeError("Video generation timed out after 5 minutes.")

        progress.progress(100)
        status_box.markdown("🌟 *Your destiny has been revealed!*")
        time.sleep(1)

        st.session_state.stage = "reveal"
        st.rerun()

    except Exception as exc:
        progress.empty()
        status_box.empty()
        st.error(f"The crystal ball has gone dark: {exc}")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Try Again"):
                st.session_state.stage = "scan"
                st.rerun()


# ── Reveal ───────────────────────────────────────────────────────────────────
def show_reveal():
    _header("🌟 Your Fortune", "Madame Zara has spoken")

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
            st.session_state.fortune_text = ""
            st.session_state.video_url = ""
            st.session_state.captured_image = None
            st.session_state.stage = "welcome"
            st.rerun()


# ─── Router ───────────────────────────────────────────────────────────────────
{
    "welcome": show_welcome,
    "scan": show_scan,
    "generating": show_generating,
    "reveal": show_reveal,
}.get(st.session_state.stage, show_welcome)()
