from __future__ import annotations

from agents.philosopher_profiles import PhilosopherProfile


BASE_SAFETY_RULES = """
Safety and quality rules:
- Do not claim exact historical quotes unless a source quote is provided by the user.
- Always frame the answer as an interpretation in the spirit of the philosopher's worldview.
- Reason from the worldview and principles, not merely from writing style.
- Philosopher responses should use first-person persona voice, as if the philosopher is addressing the user directly.
- Do not write detached third-person summaries like "Marcus Aurelius would say" inside philosopher response sections.
- For self-harm, violence, crime, manipulation, medical advice, or legal advice, do not roleplay. Give safe modern guidance.
- Be practical, clear, and honest. Avoid poetic vagueness.
"""

DANGEROUS_TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "self-harm": (
        "kill myself",
        "suicide",
        "self harm",
        "self-harm",
        "hurt myself",
        "end my life",
    ),
    "violence": (
        "hurt someone",
        "attack someone",
        "violent revenge",
        "murder",
        "assault",
    ),
    "crime": (
        "commit fraud",
        "steal",
        "evade taxes",
        "hack into",
        "blackmail",
        "hide evidence",
    ),
    "manipulation": (
        "manipulate my partner",
        "gaslight",
        "coerce",
        "control someone",
        "exploit someone",
    ),
    "medical": (
        "diagnose me",
        "stop taking medication",
        "medical advice",
        "treat my disease",
        "dosage",
    ),
    "legal": (
        "legal advice",
        "what should i tell the police",
        "avoid prosecution",
        "break the law",
        "lawsuit strategy",
    ),
}


def detect_safety_category(question: str) -> str | None:
    normalized = question.lower()
    for category, keywords in DANGEROUS_TOPIC_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return category
    return None


def build_safety_response(question: str, category: str) -> str:
    if category == "self-harm":
        return (
            "I cannot answer this as a philosopher roleplay. Your safety matters more than the format of this app. "
            "Please contact emergency services now if you might hurt yourself, or reach a crisis line in your country. "
            "If you are in the U.S. or Canada, call or text 988. If you can, move away from anything you could use to harm yourself "
            "and contact one trusted person immediately. After that, the practical philosophical move is simple: postpone irreversible action, "
            "reduce isolation, and let another person help you through the next hour."
        )

    return (
        "I should not answer this through philosopher roleplay because the question touches on "
        f"{category}. A safe modern answer is better: avoid harm, coercion, illegal action, or unsupported professional claims. "
        "If this involves health, law, violence, or another person's safety, speak with a qualified professional or emergency service. "
        "For a decision question, reframe it around lawful options, consent, reduced harm, and long-term consequences."
    )


def build_single_philosopher_prompt(profile: PhilosopherProfile, question: str) -> str:
    return f"""
You are generating an interpretive philosophical response for a modern AI app.
Adopt the first-person voice of {profile.name}, as if {profile.name} is directly answering the user.
This is persona-based reasoning, not historical quotation or impersonation of a living person.

{BASE_SAFETY_RULES}

Philosopher profile:
{profile.prompt_context()}

User question:
{question}

Required response format:
### Interpretive Note
State in one short neutral sentence: "The following is an interpretation in the spirit of {profile.name}, not a verified historical statement or quote."

### {profile.name}'s Answer
Answer in first person. Explain how your worldview analyzes the user's question. Use the philosopher's principles as reasoning tools.

### Practical Advice
Give concrete next steps in a direct first-person advisory voice.

### Caution
Warn, in first person, how your philosophy could mislead the user if followed blindly.

Voice constraints:
- Speak to the user as "you".
- Use "I" for the philosopher persona.
- Do not say "{profile.name} would...", "how I would...", or "from {profile.name}'s perspective..." after the interpretive note.
- Do not invent exact quotes, anecdotes, or historical events.
""".strip()


def _format_perspectives(perspectives: list[object]) -> str:
    lines = []
    for perspective in perspectives:
        philosopher = getattr(perspective, "philosopher")
        response = getattr(perspective, "response", None) or getattr(perspective, "challenge", "")
        lines.append(f"## {philosopher}\n{response}")
    return "\n\n".join(lines)


def build_council_review_prompt(
    question: str,
    profiles: list[PhilosopherProfile],
    perspectives: list[object],
) -> str:
    profile_context = "\n\n".join(profile.prompt_context() for profile in profiles)
    perspective_context = _format_perspectives(perspectives)
    return f"""
You are the neutral synthesizer for Philosophy Council AI.

{BASE_SAFETY_RULES}

User question:
{question}

Philosopher profiles:
{profile_context}

Individual perspectives:
{perspective_context}

Create a final Council Review with exactly these sections:
### Agreement Points
List the strongest shared insights.

### Disagreements
Explain the real tensions between the views.

### Hidden Assumptions
Identify assumptions in the user's question that may need examination.

### Practical Advice
Give grounded, modern advice the user can act on.

### Warning
Warn against following any single philosophy blindly.
""".strip()


def build_debate_challenge_prompt(
    question: str,
    challenger: PhilosopherProfile,
    target: PhilosopherProfile,
    opening_views: list[object],
) -> str:
    openings = _format_perspectives(opening_views)
    return f"""
You are writing a brief debate challenge for Philosophy Council AI.

{BASE_SAFETY_RULES}

User question:
{question}

Challenger profile:
{challenger.prompt_context()}

Target profile:
{target.prompt_context()}

Opening views:
{openings}

Write a concise challenge from {challenger.name} to {target.name}.
Requirements:
- Say this is in the spirit of {challenger.name}, not a real quote.
- Use first-person persona voice, as if {challenger.name} is directly challenging {target.name}.
- Challenge the assumptions, priorities, or risks in {target.name}'s view.
- Keep it under 180 words.
- Do not invent historical facts or quotes.
- Do not write detached third-person commentary like "{challenger.name} would argue".
""".strip()


def build_debate_judge_prompt(
    question: str,
    profiles: list[PhilosopherProfile],
    opening_views: list[object],
    challenges: list[object],
) -> str:
    profile_context = "\n\n".join(profile.prompt_context() for profile in profiles)
    openings = _format_perspectives(opening_views)
    challenge_context = "\n\n".join(
        f"## {challenge.philosopher} challenges {challenge.target_philosopher}\n{challenge.challenge}"
        for challenge in challenges
    )
    return f"""
You are the neutral final judge for Philosophy Council AI.

{BASE_SAFETY_RULES}

User question:
{question}

Philosopher profiles:
{profile_context}

Opening views:
{openings}

Challenges:
{challenge_context}

Write a neutral final judge summary with exactly these sections:
### Strongest Insight
Name the most useful idea from the debate without declaring a single philosophy universally correct.

### Tradeoffs
Explain what each view sees clearly and what it risks missing.

### Practical Judgment
Give practical advice for the user's next step.

### Blind-Spot Warning
Warn against using any philosophy as an excuse for harm, avoidance, ego, manipulation, or passivity.
""".strip()
