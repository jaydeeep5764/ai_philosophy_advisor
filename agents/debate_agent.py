from __future__ import annotations

from dataclasses import dataclass

from agents.philosopher_profiles import PhilosopherProfile, get_profile
from agents.single_agent import AgentResponse
from utils.llm import generate_response
from utils.prompts import (
    build_debate_challenge_prompt,
    build_debate_judge_prompt,
    build_safety_response,
    build_single_philosopher_prompt,
    detect_safety_category,
)


@dataclass(frozen=True)
class DebateChallenge:
    philosopher: str
    target_philosopher: str
    challenge: str


@dataclass(frozen=True)
class DebateResult:
    opening_views: list[AgentResponse]
    challenges: list[DebateChallenge]
    judge_summary: str


def _challenge_target(profiles: list[PhilosopherProfile], index: int) -> PhilosopherProfile:
    return profiles[(index + 1) % len(profiles)]


def run_debate(philosopher_names: list[str], question: str) -> DebateResult:
    safety_category = detect_safety_category(question)
    if safety_category:
        safety_response = build_safety_response(question, safety_category)
        return DebateResult(
            opening_views=[AgentResponse("Safety Guidance", safety_response)],
            challenges=[],
            judge_summary=safety_response,
        )

    profiles = [get_profile(name) for name in philosopher_names]
    opening_views = [
        AgentResponse(profile.name, generate_response(build_single_philosopher_prompt(profile, question)))
        for profile in profiles
    ]

    challenges: list[DebateChallenge] = []
    for index, challenger in enumerate(profiles):
        target = _challenge_target(profiles, index)
        prompt = build_debate_challenge_prompt(question, challenger, target, opening_views)
        challenges.append(
            DebateChallenge(
                philosopher=challenger.name,
                target_philosopher=target.name,
                challenge=generate_response(prompt),
            )
        )

    judge_prompt = build_debate_judge_prompt(question, profiles, opening_views, challenges)
    return DebateResult(
        opening_views=opening_views,
        challenges=challenges,
        judge_summary=generate_response(judge_prompt),
    )
