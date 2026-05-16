from __future__ import annotations

from dataclasses import dataclass

from agents.philosopher_profiles import get_profile
from agents.single_agent import AgentResponse
from retriever import retrieve_context
from utils.llm import generate_response
from utils.prompts import (
    build_council_review_prompt,
    build_safety_response,
    build_single_philosopher_prompt,
    detect_safety_category,
)


@dataclass(frozen=True)
class CouncilResult:
    perspectives: list[AgentResponse]
    council_review: str


def run_council_discussion(
    philosopher_names: list[str],
    question: str,
    memory_context: str | None = None,
) -> CouncilResult:
    safety_category = detect_safety_category(question)
    if safety_category:
        safety_response = build_safety_response(question, safety_category)
        return CouncilResult(
            perspectives=[AgentResponse("Safety Guidance", safety_response)],
            council_review=safety_response,
        )

    perspectives = []
    profiles = [get_profile(name) for name in philosopher_names]
    for profile in profiles:
        context = retrieve_context(question, [profile])
        prompt = build_single_philosopher_prompt(profile, question, context.text, memory_context)
        perspectives.append(AgentResponse(profile.name, generate_response(prompt), context.sources))

    review_context = retrieve_context(question, profiles, max_chunks=6)
    review_prompt = build_council_review_prompt(question, profiles, perspectives, review_context.text, memory_context)
    return CouncilResult(
        perspectives=perspectives,
        council_review=generate_response(review_prompt),
    )
