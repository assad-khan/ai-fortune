"""
HeyGen API client – avatar listing, video generation, and status polling.
"""

import time
import requests

HEYGEN_BASE = "https://api.heygen.com"
_TIMEOUT = 15  # seconds for individual HTTP calls


def _headers(api_key: str) -> dict:
    return {"X-Api-Key": api_key}


# ── Avatar & Voice discovery ──────────────────────────────────────────────────

def fetch_avatars(api_key: str) -> list[dict]:
    """Return list of available avatar dicts from HeyGen."""
    r = requests.get(
        f"{HEYGEN_BASE}/v2/avatars",
        headers=_headers(api_key),
        timeout=_TIMEOUT,
    )
    r.raise_for_status()
    return r.json().get("data", {}).get("avatars", [])


def fetch_voices(api_key: str, language_prefix: str = "en") -> list[dict]:
    """Return available voices, optionally filtered by language prefix."""
    r = requests.get(
        f"{HEYGEN_BASE}/v2/voices",
        headers=_headers(api_key),
        timeout=_TIMEOUT,
    )
    r.raise_for_status()
    all_voices: list[dict] = r.json().get("data", {}).get("voices", [])
    if language_prefix:
        filtered = [v for v in all_voices if v.get("language", "").startswith(language_prefix)]
        return filtered if filtered else all_voices
    return all_voices


# ── Video generation ──────────────────────────────────────────────────────────

def create_video(
    api_key: str,
    avatar_id: str,
    voice_id: str,
    script: str,
    bg_color: str = "#1a0a2e",
    width: int = 1280,
    height: int = 720,
) -> str:
    """
    Submit a video generation job to HeyGen.
    Returns the video_id string.
    """
    payload = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,
                    "avatar_style": "normal",
                },
                "voice": {
                    "type": "text",
                    "input_text": script,
                    "voice_id": voice_id,
                    "speed": 0.9,
                },
                "background": {
                    "type": "color",
                    "value": bg_color,
                },
            }
        ],
        "dimension": {"width": width, "height": height},
        "aspect_ratio": "16:9",
    }

    r = requests.post(
        f"{HEYGEN_BASE}/v2/video/generate",
        headers={**_headers(api_key), "Content-Type": "application/json"},
        json=payload,
        timeout=_TIMEOUT,
    )

    data = r.json()
    if r.status_code != 200 or "data" not in data:
        raise RuntimeError(
            data.get("message") or f"HeyGen error {r.status_code}: {r.text}"
        )

    return data["data"]["video_id"]


def get_video_status(api_key: str, video_id: str) -> dict:
    """Return the raw status dict for a video job."""
    r = requests.get(
        f"{HEYGEN_BASE}/v1/video_status.get",
        params={"video_id": video_id},
        headers=_headers(api_key),
        timeout=_TIMEOUT,
    )
    r.raise_for_status()
    return r.json().get("data", {})


def poll_until_ready(
    api_key: str,
    video_id: str,
    timeout_s: int = 300,
    interval_s: int = 5,
) -> str:
    """
    Poll HeyGen until the video is completed or timeout is reached.
    Returns the video URL on success.
    Raises RuntimeError on failure or timeout.
    """
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        status_data = get_video_status(api_key, video_id)
        status = status_data.get("status")

        if status == "completed":
            url = status_data.get("video_url", "")
            if not url:
                raise RuntimeError("Video completed but no URL returned.")
            return url

        if status == "failed":
            raise RuntimeError(
                f"HeyGen rendering failed: {status_data.get('error', 'unknown error')}"
            )

        time.sleep(interval_s)

    raise RuntimeError("Video generation timed out after 5 minutes.")
