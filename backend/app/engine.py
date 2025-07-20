"""
engine.py – minimal tutoring engine for MVP.
• Builds a persona-based system prompt
• Calls GPT-4o-mini *only if* OPENAI_API_KEY is present
• Records simple progress (#attempts / #correct) for one starter concept
"""

import os
from sqlmodel import Session, select

from .models import _engine, Learner, Concept, Progress

OPENAI_MODEL = "gpt-4o-mini"  # inexpensive and capable

# ──────────────────────────────────────────────────────────────────────────────
# Prompt helpers
# ──────────────────────────────────────────────────────────────────────────────
def build_system_prompt(learner: Learner) -> str:
    if int(learner.dob[:4]) >= 2018:  # ~7 yrs old
        return (
            "You are a friendly kindergarten math tutor. "
            "Use very short sentences and emojis."
        )
    return (
        "You are a supportive 6th-grade tutor. "
        "Encourage analytical thinking and ask follow-up questions."
    )


# ──────────────────────────────────────────────────────────────────────────────
# Starter concepts seeding
# ──────────────────────────────────────────────────────────────────────────────
STARTER_CONCEPTS = [
    ("math", "addition within 10", "K"),
    ("math", "counting by 5s", "K"),
    ("reading", "identify main idea", "6"),
]


def seed_concepts():
    with Session(_engine()) as s:
        if s.exec(select(Concept)).first():
            return
        for domain, label, grade in STARTER_CONCEPTS:
            s.add(Concept(domain=domain, label=label, grade=grade))
        s.commit()


# ──────────────────────────────────────────────────────────────────────────────
# Tutor main entry
# ──────────────────────────────────────────────────────────────────────────────
def _gpt_reply(messages: list[dict[str, str]]) -> str:
    """
    Return GPT reply *or* a stub if OPENAI_API_KEY is missing (CI safety).
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # CI / offline fallback
        return "OK, let's keep going!"

    from openai import OpenAI  # local import so module loads without key
    client = OpenAI(api_key=api_key)

    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        max_tokens=150,
    )
    return resp.choices[0].message.content.strip()


def tutor_reply(learner_id: int, user_text: str) -> str:
    """Return tutor reply and update simple progress."""
    with Session(_engine()) as session:
        learner = session.get(Learner, learner_id)
        if not learner:
            return "Learner not found."

        # GPT (or stub) reply
        messages = [
            {"role": "system", "content": build_system_prompt(learner)},
            {"role": "user", "content": user_text},
        ]
        reply = _gpt_reply(messages)

        # Progress write-back (very naive)
        concept = session.exec(
            select(Concept).where(Concept.label == "addition within 10")
        ).first()
        if concept:
            prog_pk = (learner.id, concept.id)
            prog = session.get(Progress, prog_pk)
            if not prog:
                prog = Progress(learner_id=learner.id, concept_id=concept.id)
            prog.attempts += 1
            if "+" in user_text:
                prog.correct += 1
            session.add(prog)
            session.commit()

        return reply
