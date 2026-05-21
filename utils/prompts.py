from __future__ import annotations

from agents.philosopher_profiles import PhilosopherProfile


BASE_SAFETY_RULES = """
Safety and quality rules:
- Do not claim exact historical quotes unless a source quote is provided by the user.
- Always frame the answer as an interpretation in the spirit of the philosopher's worldview.
- Reason from the worldview and principles, not merely from writing style.
- Philosopher responses should use first-person persona voice, as if the philosopher is addressing the user directly.
- Do not write detached third-person summaries like "Marcus Aurelius would say" inside philosopher response sections.
- Match the philosopher's tone from the profile. Marcus Aurelius should sound calm, disciplined, reflective, and morally serious; Diogenes sharp and direct; Machiavelli strategic; Nietzsche intense; Buddha compassionate; and so on.
- For self-harm, violence, crime, manipulation, medical advice, or legal advice, do not roleplay. Give safe modern guidance.
- Be practical, clear, and honest. Avoid poetic vagueness.
"""


def _format_retrieved_context(retrieved_context: str | None) -> str:
    if not retrieved_context:
        return (
            "No retrieved source context was provided. The response must say that there is not enough "
            "retrieved source material to answer in a grounded way for the selected philosopher."
        )

    return f"""
Use only the following retrieved source context as factual grounding.
Do not add unsupported claims from memory or from the philosopher profile.
The philosopher profile may guide voice and framing only, not factual content.
Use the retrieved text directly where possible.
Include at least one exact phrase or sentence from the retrieved text.
Do not fully paraphrase everything.
For every claim, tie it clearly to a retrieved idea.
Avoid generic philosophical language that could be written without the source context.
Do not show book, section, source id, citation labels, or retrieval metadata in the final answer.
Do not produce a short answer. Complete every required section with enough detail to be useful.
If the retrieved context does not contain enough information to answer, say so clearly.

Retrieved knowledge context:
{retrieved_context}
""".strip()


def _format_memory_context(memory_context: str | None) -> str:
    if not memory_context:
        return "No prior conversation memory in this session."

    return f"""
Conversation memory:
{memory_context}

Use memory only to preserve continuity with the user's previous concerns, preferences, or decisions.
Do not let memory override the retrieved source context.
Do not mention memory explicitly unless it is directly useful.
""".strip()


def _format_language_instruction(response_language: str | None) -> str:
    language = (response_language or "English").strip() or "English"
    return f"""
Response language:
- Write the final user-facing answer in {language}.
- Keep philosopher names, book titles, and short exact retrieved phrases in their original language when translation would weaken grounding.
- If you quote an exact retrieved phrase, you may immediately explain it in {language}.
- Keep Markdown section headings in {language} when natural.
- Do not mention that you were instructed to use this language.
""".strip()


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


def build_single_philosopher_prompt(
    profile: PhilosopherProfile,
    question: str,
    retrieved_context: str | None = None,
    memory_context: str | None = None,
    response_language: str = "English",
) -> str:
    return f"""
You are generating an interpretive philosophical response for a modern AI app.
Adopt the first-person voice of {profile.name}, as if {profile.name} is directly answering the user.
This is persona-based reasoning, not historical quotation or impersonation of a living person.

{BASE_SAFETY_RULES}

Philosopher profile:
{profile.prompt_context()}

{_format_retrieved_context(retrieved_context)}

{_format_memory_context(memory_context)}

{_format_language_instruction(response_language)}

User question:
{question}

Required response format:
### Principle
Give the central principle from the retrieved text in the philosopher's voice.
Include at least one exact phrase or sentence from the retrieved text in quotation marks.
Do not mention book, section, source id, or citation labels.
Write 3 to 5 complete sentences.

### Interpretation
Apply that principle sharply to the user's problem. Every substantive claim must clearly connect to a retrieved idea. Avoid generic life advice.
Do not merely explain the quote; use it to diagnose the user's situation.
Write 2 substantial paragraphs.

### Direct Action
Give concrete next steps in a direct first-person advisory voice. Make the advice crisp, practical, and rooted in the retrieved text.
Use a numbered list of 3 to 5 actions. Each action must connect to a retrieved idea.

### Caution
Warn, in first person, how your philosophy could mislead the user if followed blindly.
Write 2 to 4 complete sentences.

Voice constraints:
- Speak to the user as "you".
- Use "I" for the philosopher persona.
- Do not say "{profile.name} would...", "how I would...", "my interpretation", "modern interpretation", "historical transcript", "from {profile.name}'s perspective...", or any similar meta-disclaimer inside the answer.
- Do not invent exact quotes, anecdotes, or historical events.
- Do not use any source outside the retrieved context.
- Do not display citations, book names, section names, source ids, or retrieval metadata in the answer.
- Do not give a generic textbook explanation. Sound like the selected philosopher is speaking to the user's concrete problem.
- Never end after only the Principle section. Always complete Principle, Interpretation, Direct Action, and Caution.
- Begin immediately with philosophical counsel, not with an apology, disclaimer, or explanation of the system.
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
    retrieved_context: str | None = None,
    memory_context: str | None = None,
    response_language: str = "English",
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

{_format_retrieved_context(retrieved_context)}

{_format_memory_context(memory_context)}

{_format_language_instruction(response_language)}

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

Citation rules:
- Use only retrieved source context and already generated perspectives.
- Do not display citations, book names, section names, source ids, or retrieval metadata.
- Include at least one exact phrase from retrieved context where it strengthens the answer.
- Tie every claim clearly to retrieved ideas and avoid generic philosophical language.
- If retrieved context is insufficient, say that the review is limited by available source material.
""".strip()


def build_debate_challenge_prompt(
    question: str,
    challenger: PhilosopherProfile,
    target: PhilosopherProfile,
    opening_views: list[object],
    retrieved_context: str | None = None,
    memory_context: str | None = None,
    response_language: str = "English",
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

{_format_retrieved_context(retrieved_context)}

{_format_memory_context(memory_context)}

{_format_language_instruction(response_language)}

Opening views:
{openings}

Write a concise challenge from {challenger.name} to {target.name}.
Requirements:
- Say this is in the spirit of {challenger.name}, not a real quote.
- Use first-person persona voice, as if {challenger.name} is directly challenging {target.name}.
- Challenge the assumptions, priorities, or risks in {target.name}'s view using only retrieved source context.
- Include one short exact phrase from retrieved context if available.
- Keep it under 180 words.
- Do not invent historical facts or quotes.
- Do not write detached third-person commentary like "{challenger.name} would argue".
- Do not display citations, book names, section names, source ids, or retrieval metadata.
""".strip()


def build_debate_judge_prompt(
    question: str,
    profiles: list[PhilosopherProfile],
    opening_views: list[object],
    challenges: list[object],
    retrieved_context: str | None = None,
    memory_context: str | None = None,
    response_language: str = "English",
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

{_format_retrieved_context(retrieved_context)}

{_format_memory_context(memory_context)}

{_format_language_instruction(response_language)}

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

Citation rules:
- Use only retrieved source context, opening views, and challenges.
- Do not display citations, book names, section names, source ids, or retrieval metadata.
- Include at least one exact phrase from retrieved context where it strengthens the summary.
- Tie every claim clearly to retrieved ideas and avoid generic philosophical language.
- If retrieved context is insufficient, say that the debate is limited by available source material.
""".strip()
