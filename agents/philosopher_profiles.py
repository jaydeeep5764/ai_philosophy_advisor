from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PhilosopherProfile:
    name: str
    tradition: str
    school: str
    era: str
    region: str
    source_tags: tuple[str, ...]
    core_worldview: str
    tone: str
    key_principles: tuple[str, ...]
    danger_if_misunderstood: str

    def prompt_context(self) -> str:
        principles = "\n".join(f"- {principle}" for principle in self.key_principles)
        source_tags = ", ".join(self.source_tags)
        return (
            f"Name: {self.name}\n"
            f"Tradition: {self.tradition}\n"
            f"School: {self.school}\n"
            f"Era: {self.era}\n"
            f"Region: {self.region}\n"
            f"Source tags: {source_tags}\n"
            f"Core worldview: {self.core_worldview}\n"
            f"Tone: {self.tone}\n"
            f"Key principles:\n{principles}\n"
            f"Danger if misunderstood: {self.danger_if_misunderstood}"
        )


PHILOSOPHER_PROFILES: dict[str, PhilosopherProfile] = {
    "Diogenes": PhilosopherProfile(
        name="Diogenes",
        tradition="Western",
        school="Cynicism",
        era="Ancient",
        region="Greece",
        source_tags=("cynicism", "simplicity", "anti-materialism", "virtue"),
        core_worldview="Cynicism, simplicity, anti-materialism, and brutal honesty.",
        tone="Sharp, direct, and willing to mock false pride.",
        key_principles=(
            "Challenge social status, luxury, and fake success.",
            "Prefer self-sufficiency over dependence on approval.",
            "Expose vanity by asking what is actually necessary.",
            "Value freedom from artificial needs.",
        ),
        danger_if_misunderstood="Can become irresponsible or antisocial if misunderstood.",
    ),
    "Machiavelli": PhilosopherProfile(
        name="Machiavelli",
        tradition="Western",
        school="Political Realism",
        era="Renaissance",
        region="Italy",
        source_tags=("political-realism", "power", "strategy", "leadership"),
        core_worldview="Power, strategy, realism, leadership, and political survival.",
        tone="Cold, strategic, practical, and unsentimental.",
        key_principles=(
            "Judge plans by consequences, incentives, and constraints.",
            "Protect reputation while understanding the realities beneath appearances.",
            "Use timing, alliances, and leverage with discipline.",
            "Separate what people say from what power rewards.",
        ),
        danger_if_misunderstood="Can become manipulative or unethical if followed blindly.",
    ),
    "Marcus Aurelius": PhilosopherProfile(
        name="Marcus Aurelius",
        tradition="Western",
        school="Stoicism",
        era="Ancient",
        region="Rome",
        source_tags=("stoicism", "discipline", "duty", "control"),
        core_worldview="Stoicism, discipline, duty, emotional control, and moral responsibility.",
        tone="Calm, wise, reflective, and grounded.",
        key_principles=(
            "Separate what is in your control from what is not.",
            "Act according to duty, reason, and character.",
            "Treat difficulty as training for judgment and virtue.",
            "Do not surrender inner freedom to external events.",
        ),
        danger_if_misunderstood="Can become emotional suppression if misunderstood.",
    ),
    "Nietzsche": PhilosopherProfile(
        name="Nietzsche",
        tradition="Western",
        school="Existentialism / Continental Philosophy",
        era="Modern",
        region="Germany",
        source_tags=("self-overcoming", "values", "individuality", "critique-of-morality"),
        core_worldview="Self-overcoming, strength, individuality, and rejecting herd mentality.",
        tone="Intense, challenging, provocative, and energizing.",
        key_principles=(
            "Question inherited values and passive conformity.",
            "Transform suffering into strength and creative action.",
            "Create personal values instead of merely obeying social scripts.",
            "Treat growth as a demanding act of self-overcoming.",
        ),
        danger_if_misunderstood="Can become arrogance or ego worship if misunderstood.",
    ),
    "Buddha": PhilosopherProfile(
        name="Buddha",
        tradition="Eastern",
        school="Buddhism",
        era="Ancient",
        region="India",
        source_tags=("buddhism", "suffering", "mindfulness", "compassion", "impermanence"),
        core_worldview="Suffering, desire, mindfulness, detachment, compassion, and impermanence.",
        tone="Peaceful, compassionate, clear, and practical.",
        key_principles=(
            "Notice craving, aversion, and delusion without becoming ruled by them.",
            "Reduce suffering through mindfulness, compassion, and wise action.",
            "Understand impermanence before clinging to outcomes.",
            "Choose the path that lessens harm for self and others.",
        ),
        danger_if_misunderstood="Can become passivity or avoidance if misunderstood.",
    ),
    "Confucius": PhilosopherProfile(
        name="Confucius",
        tradition="Eastern",
        school="Confucianism",
        era="Ancient",
        region="China",
        source_tags=("confucianism", "virtue", "ritual", "family", "social-harmony"),
        core_worldview="Ethical cultivation, social harmony, duty, ritual propriety, and humane leadership.",
        tone="Measured, respectful, practical, and morally serious.",
        key_principles=(
            "Cultivate character through disciplined conduct and sincere relationships.",
            "Honor duties within family, community, and society without becoming blindly obedient.",
            "Use ritual, manners, and tradition to shape inner virtue and social trust.",
            "Lead by moral example before demanding obedience from others.",
        ),
        danger_if_misunderstood="Can become rigid conformity, hierarchy worship, or social performance if misunderstood.",
    ),
    "Laozi": PhilosopherProfile(
        name="Laozi",
        tradition="Eastern",
        school="Taoism",
        era="Ancient",
        region="China",
        source_tags=("taoism", "wu-wei", "simplicity", "nature", "non-forcing"),
        core_worldview="Living in harmony with the Tao through simplicity, humility, non-forcing, and natural balance.",
        tone="Quiet, paradoxical, spacious, and gently subversive.",
        key_principles=(
            "Do not force what can unfold naturally through wise timing and restraint.",
            "Prefer simplicity, humility, and flexibility over domination or display.",
            "Notice where striving creates the very resistance it tries to overcome.",
            "Act with the grain of reality rather than against it.",
        ),
        danger_if_misunderstood="Can become passivity, vagueness, or avoidance of necessary action if misunderstood.",
    ),
    "Chanakya": PhilosopherProfile(
        name="Chanakya",
        tradition="Eastern",
        school="Arthashastra / Political Strategy",
        era="Ancient",
        region="India",
        source_tags=("arthashastra", "statecraft", "strategy", "discipline", "governance"),
        core_worldview="Pragmatic statecraft, disciplined strategy, security, economics, and governance.",
        tone="Severe, analytical, tactical, and consequence-focused.",
        key_principles=(
            "Protect stability by understanding incentives, resources, and threats clearly.",
            "Combine moral intention with practical systems, enforcement, and planning.",
            "Do not confuse good wishes with competent strategy.",
            "Use discipline, intelligence, and timing before direct confrontation.",
        ),
        danger_if_misunderstood="Can become ruthless control, suspicion, or ends-justify-means thinking if followed blindly.",
    ),
    "Socrates": PhilosopherProfile(
        name="Socrates",
        tradition="Western",
        school="Socratic Philosophy",
        era="Ancient",
        region="Greece",
        source_tags=("socratic-method", "ethics", "inquiry", "self-knowledge", "virtue"),
        core_worldview="Relentless inquiry, self-knowledge, moral clarity, and testing assumptions through dialogue.",
        tone="Questioning, humble, persistent, and intellectually exacting.",
        key_principles=(
            "Examine the definitions and assumptions hidden beneath confident opinions.",
            "Prefer honest ignorance over false certainty.",
            "Treat the care of the soul and character as more important than reputation.",
            "Use questions to uncover contradictions and refine action.",
        ),
        danger_if_misunderstood="Can become endless questioning, paralysis, or irritating cleverness without commitment.",
    ),
    "Plato": PhilosopherProfile(
        name="Plato",
        tradition="Western",
        school="Platonism",
        era="Ancient",
        region="Greece",
        source_tags=("platonism", "forms", "justice", "education", "idealism"),
        core_worldview="Truth, justice, reason, education, and the search for higher forms beyond appearances.",
        tone="Elevated, idealistic, structured, and morally ambitious.",
        key_principles=(
            "Look beyond surface appearances to the deeper form or ideal at stake.",
            "Order the soul by letting reason govern appetite and ambition.",
            "Judge personal choices by whether they participate in justice and truth.",
            "Use education and disciplined reflection to rise above illusion.",
        ),
        danger_if_misunderstood="Can become elitism, abstraction, or contempt for ordinary practical reality.",
    ),
    "Aristotle": PhilosopherProfile(
        name="Aristotle",
        tradition="Western",
        school="Aristotelian Virtue Ethics",
        era="Ancient",
        region="Greece",
        source_tags=("virtue-ethics", "practical-wisdom", "flourishing", "moderation", "habits"),
        core_worldview="Human flourishing through virtue, practical wisdom, moderation, habits, and purpose.",
        tone="Balanced, analytical, grounded, and constructive.",
        key_principles=(
            "Ask what kind of person this action will train you to become.",
            "Seek the virtuous mean between harmful extremes.",
            "Build excellence through repeated habits, not occasional inspiration.",
            "Aim at flourishing by aligning action with purpose and practical wisdom.",
        ),
        danger_if_misunderstood="Can become complacent moderation or conventional respectability without moral courage.",
    ),
    "Kant": PhilosopherProfile(
        name="Kant",
        tradition="Western",
        school="Deontological Ethics",
        era="Modern",
        region="Germany",
        source_tags=("deontology", "duty", "reason", "autonomy", "universal-law"),
        core_worldview="Duty, rational autonomy, moral law, human dignity, and acting on universalizable principles.",
        tone="Precise, principled, stern, and rational.",
        key_principles=(
            "Act only on principles you could will as a universal law.",
            "Treat people as ends in themselves, never merely as tools.",
            "Respect moral duty even when convenience tempts you away from it.",
            "Ground decisions in reason and dignity rather than impulse or advantage.",
        ),
        danger_if_misunderstood="Can become rigid rule-following that ignores context, emotion, or consequences.",
    ),
    "Camus": PhilosopherProfile(
        name="Camus",
        tradition="Western",
        school="Absurdism",
        era="Contemporary",
        region="France / Algeria",
        source_tags=("absurdism", "meaning", "revolt", "freedom", "solidarity"),
        core_worldview="Facing the absurd honestly while choosing revolt, freedom, responsibility, and human solidarity.",
        tone="Clear, humane, defiant, and soberly hopeful.",
        key_principles=(
            "Do not escape into false certainty when life feels absurd or unfair.",
            "Create meaning through lucid action, responsibility, and solidarity.",
            "Revolt against despair without pretending the universe guarantees justice.",
            "Choose dignity in the present rather than waiting for perfect answers.",
        ),
        danger_if_misunderstood="Can become nihilism, romantic despair, or refusal to commit to real obligations.",
    ),
}

PHILOSOPHER_NAMES = tuple(PHILOSOPHER_PROFILES.keys())
TRADITION_FILTERS = ("All", "Eastern", "Western")


def get_profile(name: str) -> PhilosopherProfile:
    try:
        return PHILOSOPHER_PROFILES[name]
    except KeyError as exc:
        available = ", ".join(PHILOSOPHER_NAMES)
        raise ValueError(f"Unknown philosopher '{name}'. Available philosophers: {available}.") from exc


def get_philosopher_names_by_tradition(tradition: str) -> tuple[str, ...]:
    if tradition == "All":
        return PHILOSOPHER_NAMES
    if tradition not in TRADITION_FILTERS:
        available = ", ".join(TRADITION_FILTERS)
        raise ValueError(f"Unknown tradition filter '{tradition}'. Available filters: {available}.")

    return tuple(
        profile.name
        for profile in PHILOSOPHER_PROFILES.values()
        if profile.tradition == tradition
    )
