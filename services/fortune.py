"""
Fortune generation via OpenAI GPT-4o.
Personalised using the visitor's name and date of birth (numerology + astrology).
No image is sent — the palm scan is theatrical only.
"""

import datetime
from openai import OpenAI


# ─── Numerology & Astrology helpers ──────────────────────────────────────────

def _life_path_number(dob: datetime.date) -> int:
    """Reduce all digits of the full date to a single digit (1–9, or 11/22 as master numbers)."""
    digits = [int(d) for d in dob.strftime("%d%m%Y") if d.isdigit()]
    total = sum(digits)
    while total > 9 and total not in (11, 22):
        total = sum(int(d) for d in str(total))
    return total


def _zodiac_sign(dob: datetime.date) -> str:
    """Return the Western zodiac sign for the given date."""
    month, day = dob.month, dob.day
    if (month == 3 and day >= 21) or (month == 4 and day <= 19):   return "Aries"
    if (month == 4 and day >= 20) or (month == 5 and day <= 20):   return "Taurus"
    if (month == 5 and day >= 21) or (month == 6 and day <= 20):   return "Gemini"
    if (month == 6 and day >= 21) or (month == 7 and day <= 22):   return "Cancer"
    if (month == 7 and day >= 23) or (month == 8 and day <= 22):   return "Leo"
    if (month == 8 and day >= 23) or (month == 9 and day <= 22):   return "Virgo"
    if (month == 9 and day >= 23) or (month == 10 and day <= 22):  return "Libra"
    if (month == 10 and day >= 23) or (month == 11 and day <= 21): return "Scorpio"
    if (month == 11 and day >= 22) or (month == 12 and day <= 21): return "Sagittarius"
    if (month == 12 and day >= 22) or (month == 1 and day <= 19):  return "Capricorn"
    if (month == 1 and day >= 20) or (month == 2 and day <= 18):   return "Aquarius"
    return "Pisces"


# ─── Public API ───────────────────────────────────────────────────────────────

def get_reading_context(name: str, dob: datetime.date) -> dict:
    """Return the numerology/astrology context dict for display in the UI."""
    return {
        "name": name,
        "zodiac": _zodiac_sign(dob),
        "life_path": _life_path_number(dob),
    }


def generate_fortune(name: str, dob: datetime.date, client: OpenAI) -> str:
    """
    Generate a personalised mystical fortune based on name and date of birth.
    Returns the fortune string. Raises on API error.
    """
    life_path = _life_path_number(dob)
    zodiac = _zodiac_sign(dob)
    age = (datetime.date.today() - dob).days // 365

    system_prompt = (
        "You are Madame Zara, a captivating and mysterious fortune teller with centuries of ancient wisdom. "
        "You read destinies through numerology, astrology, and the mystical arts. "
        "Your tone is poetic, dramatic, and deeply personal. "
        "You always end with a powerful, memorable prophecy that feels uniquely tailored to the person."
    )

    user_prompt = (
        f"The visitor before you is {name}, a {zodiac} with a Life Path Number of {life_path}. "
        f"They are {age} years old. "
        "Deliver a SHORT, dramatic fortune of exactly 1–2 sentences, strictly under 25 words total. "
        "Use their first name once. Be vivid and end on a prophecy. No filler words."
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=60,
        temperature=0.9,
    )

    text = response.choices[0].message.content.strip()
    # Hard cap at 150 chars (~10 seconds of speech at normal pace)
    if len(text) > 150:
        text = text[:150].rsplit(".", 1)[0] + "."
    return text
