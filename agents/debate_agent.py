from __future__ import annotations

from dataclasses import dataclass

from agents.philosopher_profiles import PhilosopherProfile, get_profile
from agents.single_agent import AgentResponse
from retriever import retrieve_context
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


def run_debate(
    philosopher_names: list[str],
    question: str,
    memory_context: str | None = None,
) -> DebateResult:
    safety_category = detect_safety_category(question)
    if safety_category:
        safety_response = build_safety_response(question, safety_category)
        return DebateResult(
            opening_views=[AgentResponse("Safety Guidance", safety_response)],
            challenges=[],
            judge_summary=safety_response,
        )

    profiles = [get_profile(name) for name in philosopher_names]
    opening_views = []
    for profile in profiles:
        context = retrieve_context(question, [profile])
        opening_views.append(
            AgentResponse(
                profile.name,
                generate_response(build_single_philosopher_prompt(profile, question, context.text, memory_context)),
                context.sources,
            )
        )

    challenges: list[DebateChallenge] = []
    for index, challenger in enumerate(profiles):
        target = _challenge_target(profiles, index)
        context = retrieve_context(question, [challenger, target])
        prompt = build_debate_challenge_prompt(
            question,
            challenger,
            target,
            opening_views,
            context.text,
            memory_context,
        )
        challenges.append(
            DebateChallenge(
                philosopher=challenger.name,
                target_philosopher=target.name,
                challenge=generate_response(prompt),
            )
        )

    judge_context = retrieve_context(question, profiles, max_chunks=6)
    judge_prompt = build_debate_judge_prompt(
        question,
        profiles,
        opening_views,
        challenges,
        judge_context.text,
        memory_context,
    )
    return DebateResult(
        opening_views=opening_views,
        challenges=challenges,
        judge_summary=generate_response(judge_prompt),
    )
