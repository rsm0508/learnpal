"""
engine.py – minimal tutoring engine for MVP.
1️⃣ Builds a system prompt based on learner age.
2️⃣ Sends user question -> GPT-4o-mini -> returns tutor reply text.
Future sprints will add adaptive mastery & item banks.
"""

import os
from openai import OpenAI

from .models import Learner
from .auth import current_user
from sqlmodel import Session
from sqlmodel import select, Field
from .models import _engine

OPENAI_MODEL = "gpt-4o-mini"      # cheap + good enough

client = OpenAI()


def build_system_prompt(learner: Learner) -> str:
    if int(learner.dob[:4]) >= 2018:   # ~7 yrs old
        return (
            "You are a friendly kindergarten math tutor. "
            "Use very short sentences and emojis."
        )
    else:
        return (
            "You are a supportive 6th-grade tutor. "
            "Encourage analytical thinking and ask follow-up questions."
        )


def tutor_reply(learner_id: int, user_text: str) -> str:
    with Session(_engine()) as s:
        learner = s.get(Learner, learner_id)
        if not learner:
            return "Learner not found."
    messages = [
        {"role": "system", "content": build_system_prompt(learner)},
        {"role": "user", "content": user_text},
    ]
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        max_tokens=150,
    )
    return resp.choices[0].message.content.strip()
