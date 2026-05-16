from __future__ import annotations

from dataclasses import dataclass

from agents.philosopher_profiles import get_profile
from retriever import retrieve_context
from utils.llm import generate_response
from utils.prompts import build_single_philosopher_prompt, build_safety_response, detect_safety_category


@dataclass(frozen=True)
class AgentResponse:
    philosopher: str
    response: str
    sources: tuple[str, ...] = ()


def ask_philosopher(
    philosopher_name: str,
    question: str,
    memory_context: str | None = None,
) -> AgentResponse:
    safety_category = detect_safety_category(question)
    if safety_category:
        return AgentResponse(
            philosopher="Safety Guidance",
            response=build_safety_response(question, safety_category),
        )

    profile = get_profile(philosopher_name)
    context = retrieve_context(question, [profile])
    prompt = build_single_philosopher_prompt(profile, question, context.text, memory_context)
    return AgentResponse(
        philosopher=profile.name,
        response=generate_response(prompt),
        sources=context.sources,
    )
