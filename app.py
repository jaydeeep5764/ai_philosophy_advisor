from __future__ import annotations

import streamlit as st

from agents.council_agent import run_council_discussion
from agents.debate_agent import run_debate
from agents.philosopher_profiles import TRADITION_FILTERS, get_philosopher_names_by_tradition, get_profile
from agents.single_agent import ask_philosopher
from utils.llm import LLMError


APP_TITLE = "Philosophy Council AI"


def configure_page() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
            .main .block-container {
                max-width: 1180px;
                padding-top: 2rem;
            }
            .small-muted {
                color: #667085;
                font-size: 0.92rem;
                line-height: 1.45;
            }
            div[data-testid="stVerticalBlockBorderWrapper"] {
                border-color: #d0d5dd;
                box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_intro() -> None:
    st.title(APP_TITLE)
    st.caption(
        "Ask one philosopher, convene a council, or stage a debate. "
        "Responses are interpretive and written in the spirit of each worldview, not as historical quotations."
    )


def render_profile_sidebar(selected_names: list[str]) -> None:
    with st.sidebar.expander("Selected philosopher notes", expanded=False):
        if not selected_names:
            st.caption("Choose philosophers to see their worldview notes.")
            return

        for name in selected_names:
            profile = get_profile(name)
            st.markdown(f"**{profile.name}**")
            st.caption(f"{profile.tradition} | {profile.school} | {profile.region}, {profile.era}")
            st.caption(profile.core_worldview)
            st.caption(f"Risk: {profile.danger_if_misunderstood}")


def render_agent_card(title: str, body: str, subtitle: str | None = None) -> None:
    with st.container(border=True):
        st.subheader(title)
        if subtitle:
            st.markdown(f"<div class='small-muted'>{subtitle}</div>", unsafe_allow_html=True)
        st.markdown(body)


def format_sources(sources: tuple[str, ...]) -> str | None:
    if not sources:
        return "RAG citations: No retrieved Chroma context. Run `python ingest.py --reset` after adding source data."
    return "RAG citations: " + ", ".join(sources)


def render_tradition_filter() -> tuple[str, tuple[str, ...]]:
    tradition = st.sidebar.selectbox("Philosopher tradition", TRADITION_FILTERS)
    philosopher_names = get_philosopher_names_by_tradition(tradition)
    st.sidebar.caption(f"{len(philosopher_names)} philosophers available")
    return tradition, philosopher_names


def render_single_mode(question: str, philosopher_names: tuple[str, ...]) -> tuple[bool, str | None]:
    if not philosopher_names:
        st.warning("No philosophers are available for this filter yet.")
        return False, None

    default_index = philosopher_names.index("Marcus Aurelius") if "Marcus Aurelius" in philosopher_names else 0
    selected = st.selectbox("Choose a philosopher", philosopher_names, index=default_index)
    render_profile_sidebar([selected])
    submitted = st.button("Ask", type="primary", use_container_width=False)
    if not submitted:
        return False, selected

    if not question.strip():
        st.warning("Please enter a question first.")
        return False, selected

    with st.spinner(f"Consulting {selected}..."):
        result = ask_philosopher(selected, question)

    profile = get_profile(selected)
    render_agent_card(
        f"{result.philosopher}",
        result.response,
        format_sources(result.sources) or f"In the spirit of {profile.name}: {profile.core_worldview}",
    )
    return True, selected


def render_council_mode(question: str, philosopher_names: tuple[str, ...]) -> tuple[bool, list[str]]:
    if not philosopher_names:
        st.warning("No philosophers are available for this filter yet.")
        return False, []

    st.markdown("Choose at least two philosophers for the council.")
    default_names = {"Marcus Aurelius", "Buddha", "Nietzsche"}
    selected = [
        name
        for name in philosopher_names
        if st.checkbox(
            name,
            value=name in default_names,
            key=f"council_{name}",
            help=f"{get_profile(name).tradition} | {get_profile(name).school}",
        )
    ]
    render_profile_sidebar(selected)

    submitted = st.button("Ask", type="primary", use_container_width=False)
    if not submitted:
        return False, selected

    if not question.strip():
        st.warning("Please enter a question first.")
        return False, selected
    if len(selected) < 2:
        st.warning("Please select at least two philosophers for a council discussion.")
        return False, selected

    with st.spinner("Convening the council..."):
        result = run_council_discussion(selected, question)

    st.subheader("Philosopher Perspectives")
    columns = st.columns(2)
    for index, perspective in enumerate(result.perspectives):
        with columns[index % 2]:
            profile = get_profile(perspective.philosopher) if perspective.philosopher in philosopher_names else None
            render_agent_card(
                perspective.philosopher,
                perspective.response,
                format_sources(perspective.sources) or (f"In the spirit of {profile.name}" if profile else None),
            )

    st.subheader("Council Review")
    render_agent_card("Final Review", result.council_review)
    return True, selected


def render_debate_mode(question: str, philosopher_names: tuple[str, ...]) -> tuple[bool, list[str]]:
    if not philosopher_names:
        st.warning("No philosophers are available for this filter yet.")
        return False, []

    st.markdown("Choose 2 to 4 philosophers for the debate.")
    default_names = {"Diogenes", "Machiavelli", "Marcus Aurelius"}
    selected = [
        name
        for name in philosopher_names
        if st.checkbox(
            name,
            value=name in default_names,
            key=f"debate_{name}",
            help=f"{get_profile(name).tradition} | {get_profile(name).school}",
        )
    ]
    render_profile_sidebar(selected)

    submitted = st.button("Ask", type="primary", use_container_width=False)
    if not submitted:
        return False, selected

    if not question.strip():
        st.warning("Please enter a question first.")
        return False, selected
    if not 2 <= len(selected) <= 4:
        st.warning("Debate Mode needs 2 to 4 philosophers.")
        return False, selected

    with st.spinner("Opening the debate..."):
        result = run_debate(selected, question)

    st.subheader("Opening Views")
    opening_columns = st.columns(2)
    for index, perspective in enumerate(result.opening_views):
        with opening_columns[index % 2]:
            render_agent_card(
                perspective.philosopher,
                perspective.response,
                format_sources(perspective.sources),
            )

    st.subheader("Challenges")
    challenge_columns = st.columns(2)
    for index, challenge in enumerate(result.challenges):
        with challenge_columns[index % 2]:
            render_agent_card(
                f"{challenge.philosopher} challenges {challenge.target_philosopher}",
                challenge.challenge,
            )

    st.subheader("Neutral Judge")
    render_agent_card("Final Summary", result.judge_summary)
    return True, selected


def main() -> None:
    configure_page()
    render_intro()

    mode = st.sidebar.radio(
        "Mode",
        ["Ask One Philosopher", "Council Discussion", "Debate Mode"],
    )
    _, philosopher_names = render_tradition_filter()

    question = st.text_area(
        "Your question",
        placeholder="Example: Should I leave a stable job to pursue work that feels more meaningful?",
        height=150,
    )

    try:
        if mode == "Ask One Philosopher":
            render_single_mode(question, philosopher_names)
        elif mode == "Council Discussion":
            render_council_mode(question, philosopher_names)
        else:
            render_debate_mode(question, philosopher_names)
    except LLMError as exc:
        st.error(str(exc))
        st.info("Check your Gemini API key, quota, and network connection, then try again.")


if __name__ == "__main__":
    main()
