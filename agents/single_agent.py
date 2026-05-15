from __future__ import annotations

from dataclasses import dataclass

from agents.philosopher_profiles import get_profile
from utils.llm import generate_response
from utils.prompts import build_single_philosopher_prompt, build_safety_response, detect_safety_category


@dataclass(frozen=True)
class AgentResponse:
    philosopher: str
    response: str


def ask_philosopher(philosopher_name: str, question: str) -> AgentResponse:
    safety_category = detect_safety_category(question)
    if safety_category:
        return AgentResponse(
            philosopher="Safety Guidance",
            response=build_safety_response(question, safety_category),
        )

    profile = get_profile(philosopher_name)
    prompt = build_single_philosopher_prompt(profile, question)
    return AgentResponse(philosopher=profile.name, response=generate_response(prompt))
