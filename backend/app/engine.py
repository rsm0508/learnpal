"""
engine.py – minimal tutoring engine for MVP.
1️⃣ Builds a system prompt based on learner age.
2️⃣ Sends user question -> GPT-4o-mini -> returns tutor reply text.
3️⃣ Records simple progress (#attempts / #correct) for one starter concept.
"""

from openai import OpenAI
from sqlmodel import Session, select

from .models import _engine, Learner, Concept, Progress

OPENAI_MODEL = "gpt-4o-mini"  # inexpensive and capable
client = OpenAI()


# ------------------------------------------------------------------ #
#   Prompt helpers
# ------------------------------------------------------------------ #
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


# ------------------------------------------------------------------ #
#   Starter concepts seeding
# ------------------------------------------------------------------ #
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


# ------------------------------------------------------------------ #
#   Tutor main entry
# ------------------------------------------------------------------ #
def tutor_reply(learner_id: int, user_text: str) -> str:
    """Return GPT reply *and* update simple progress metrics."""
    with Session(_engine()) as session:
        learner = session.get(Learner, learner_id)
        if not learner:
            return "Learner not found."

        # --- GPT call ---
        messages = [
            {"role": "system", "content": build_system_prompt(learner)},
            {"role": "user", "content": user_text},
        ]
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=150,
        )
        reply = resp.choices[0].message.content.strip()

        # --- Progress write-back (very naive for MVP) ---
        # Use the first starter concept just to create some data.
        concept = session.exec(
            select(Concept).where(Concept.label == "addition within 10")
        ).first()
        if concept:
            prog_pk = (learner.id, concept.id)
            prog = session.get(Progress, prog_pk)
            if not prog:
                prog = Progress(learner_id=learner.id, concept_id=concept.id)
            prog.attempts += 1
            # dumb heuristic: if user types "+" we say it's correct
            if "+" in user_text:
                prog.correct += 1
            session.add(prog)
            session.commit()

        return reply
