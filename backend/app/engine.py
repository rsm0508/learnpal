"""
engine.py – adaptive tutor with hint tiers, latency tracking, memory cap,
and starter-concept seeding (required by main.py).

Key components
──────────────
• seed_concepts(): populates Concept table at app start
• _gpt_reply() returns (text, latency_ms) with robust logging
• _tier_update() manages wrong-streak with bounded OrderedDict
"""

import logging
import os
import re
import time
from collections import OrderedDict
from typing import Tuple

from dotenv import load_dotenv
from sqlmodel import Session, select

from .models import _engine, Concept, Learner, Progress

load_dotenv(override=True)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

OPENAI_MODEL = "gpt-4o-mini"
MAX_STREAK_ENTRIES = int(os.getenv("MAX_STREAK_ENTRIES", "1000"))

# ────────────────────────────── starter concepts & seed fn
STARTER_CONCEPTS = [
    ("math", "addition within 10", "K"),
    ("math", "counting by 5s", "K"),
    ("reading", "identify main idea", "6"),
]


def seed_concepts() -> None:
    """Populate Concept table once (main.py imports this)."""
    with Session(_engine()) as s:
        if s.exec(select(Concept)).first():
            return
        for dom, label, grade in STARTER_CONCEPTS:
            s.add(Concept(domain=dom, label=label, grade=grade))
        s.commit()
        log.info("Seeded starter concepts")


# ────────────────────────────── GPT wrapper
def _gpt_reply(messages) -> Tuple[str, int]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "OK, let's keep going!", 0
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, timeout=10)
        t0 = time.monotonic()
        resp = client.chat.completions.create(
            model=OPENAI_MODEL, messages=messages, max_tokens=150
        )
        latency = int((time.monotonic() - t0) * 1000)
        return resp.choices[0].message.content.strip(), latency
    except Exception as exc:  # noqa: BLE001
        log.error("GPT API error: %s", exc)
        return "I'm having trouble responding right now.", 0


# ────────────────────────────── helpers
_WRONG_STREAK: "OrderedDict[Tuple[int, int], int]" = OrderedDict()
HINT_THRESHOLD = 2
ANSWER_THRESHOLD = 3
_ADD_RE = re.compile(r"\b(\d+)\s*\+\s*(\d+)\b")


def _system_prompt(learner: Learner, tier: str) -> str:
    base = (
        "You are a friendly kindergarten math tutor. Use very short sentences and emojis."
        if int(learner.dob[:4]) >= 2018
        else "You are a supportive 6th-grade tutor. Encourage analytical thinking."
    )
    return {
        "normal": base,
        "hint": f"{base} Provide **one** helpful hint only. DO NOT reveal the answer.",
        "answer": f"{base} State the correct answer as simply as possible.",
    }[tier]


def _is_correct(text: str) -> bool:
    text = text.strip()
    if text.isdigit():
        return 0 <= int(text) <= 10
    if m := _ADD_RE.search(text):
        a, b = map(int, m.groups())
        return (a + b) <= 10
    return False


def _tier_update(key: Tuple[int, int], correct: bool) -> str:
    if correct:
        _WRONG_STREAK.pop(key, None)
        return "normal"
    _WRONG_STREAK[key] = _WRONG_STREAK.get(key, 0) + 1
    if _WRONG_STREAK[key] == HINT_THRESHOLD:
        tier = "hint"
    elif _WRONG_STREAK[key] >= ANSWER_THRESHOLD:
        tier = "answer"
        _WRONG_STREAK.pop(key, None)
    else:
        tier = "normal"

    if len(_WRONG_STREAK) > MAX_STREAK_ENTRIES:
        _WRONG_STREAK.popitem(last=False)
    return tier


# ────────────────────────────── public entry
def tutor_reply(learner_id: int, user_text: str):
    with Session(_engine()) as s:
        learner = s.get(Learner, learner_id)
        if not learner:
            return {"type": "error", "content": "Learner not found.", "latency_ms": 0}

        concept = s.exec(
            select(Concept).where(Concept.label == "addition within 10")
        ).first()
        if concept is None:  # auto-seed for test DBs
            concept = Concept(domain="math", label="addition within 10", grade="K")
            s.add(concept)
            s.commit()
            s.refresh(concept)

        correct = _is_correct(user_text)
        pk = (learner.id, concept.id)
        prog = s.get(Progress, pk) or Progress(
            learner_id=learner.id, concept_id=concept.id
        )
        prog.attempts += 1
        if correct:
            prog.correct += 1
        s.add(prog)

        tier = _tier_update(pk, correct)
        reply_text, latency = _gpt_reply(
            [
                {"role": "system", "content": _system_prompt(learner, tier)},
                {"role": "user", "content": user_text},
            ]
        )
        s.commit()
        return {"type": tier, "content": reply_text, "latency_ms": latency}
