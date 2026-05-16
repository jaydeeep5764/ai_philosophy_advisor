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
