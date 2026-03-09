"""
Fortune generation via OpenAI GPT-4o Vision.
Sends the palm image and receives a personalised mystical fortune.
"""

import base64
from io import BytesIO

from openai import OpenAI
from PIL import Image

SYSTEM_PROMPT = (
    "You are Madame Zara, a captivating and mysterious fortune teller with centuries of wisdom. "
    "When you receive a palm image, you study it deeply and deliver a mesmerising, personalised reading. "
    "You reference specific palm features — life line, heart line, fate line, mount of Venus — "
    "as though you truly see them. Your tone is poetic, dramatic, and reassuring. "
    "You always end with a powerful, memorable prophecy."
)

USER_PROMPT = (
    "A visitor holds their palm before you. Study it carefully. "
    "Deliver your fortune reading in 3–5 sentences, under 100 words. "
    "Speak directly to the visitor (use 'you'/'your'). "
    "Be mysterious and end with a specific, vivid prophecy."
)


def _image_to_b64(image: Image.Image) -> str:
    buf = BytesIO()
    image.convert("RGB").save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def generate_fortune(image: Image.Image, client: OpenAI) -> str:
    """
    Send the palm image to GPT-4o Vision and return the fortune string.
    Raises on API error.
    """
    b64 = _image_to_b64(image)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": USER_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                    },
                ],
            },
        ],
        max_tokens=200,
        temperature=0.9,
    )

    text = response.choices[0].message.content.strip()
    # Keep under ~400 chars so HeyGen renders quickly (~30-40 s)
    if len(text) > 400:
        text = text[:400].rsplit(".", 1)[0] + "."
    return text
