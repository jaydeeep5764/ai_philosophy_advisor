from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

from agents.council_agent import run_council_discussion
from agents.debate_agent import run_debate
from agents.philosopher_profiles import TRADITION_FILTERS, get_philosopher_names_by_tradition, get_profile
from agents.single_agent import ask_philosopher
from utils.llm import LLMError
from utils.memory import append_memory_entry, build_memory_context, create_memory_entry


APP_TITLE = "Philosophy Council AI"
MEMORY_KEY = "conversation_memory"
ACTIVE_MEMORY_KEY = "active_memory_index"
MODE_KEY = "selected_mode"
SINGLE_PHILOSOPHER_KEY = "single_philosopher"
PREFERRED_PHILOSOPHERS_KEY = "preferred_philosophers"
RESPONSE_LANGUAGE_KEY = "response_language"
RESPONSE_LANGUAGES = (
    "English",
    "Hindi",
    "Gujarati",
    "Marathi",
    "Bengali",
    "Tamil",
    "Telugu",
    "Kannada",
    "Malayalam",
    "Punjabi",
    "Urdu",
    "Spanish",
    "French",
    "German",
)
ROOT_DIR = Path(__file__).resolve().parent
OLD_MAP_TEXTURE_PATH = ROOT_DIR / "assets" / "old_map_texture.jpg"


def get_asset_data_uri(path: Path, mime_type: str) -> str:
    if not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def configure_page() -> None:
    old_map_background = get_asset_data_uri(OLD_MAP_TEXTURE_PATH, "image/jpeg")
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="PC",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
            :root {
                --paper: #d9b979;
                --paper-light: #f2dcad;
                --paper-deep: #9b6b32;
                --burnt: #3b2515;
                --burnt-soft: #6d4828;
                --terracotta: #9b4e24;
                --terracotta-deep: #63301b;
                --ink: #25180f;
                --muted-ink: #6a4727;
                --sepia: #7b4c24;
                --sepia-dark: #442713;
                --gild: #b98036;
                --border: #6b4424;
            }

            html, body, [data-testid="stAppViewContainer"] {
                background:
                    radial-gradient(circle at 50% 42%, rgba(250, 224, 164, 0.56), rgba(68, 39, 19, 0.34) 78%, rgba(37, 24, 15, 0.78) 100%),
                    linear-gradient(90deg, rgba(37, 24, 15, 0.42), transparent 18%, transparent 82%, rgba(37, 24, 15, 0.48)),
                    url("__OLD_MAP_BG__"),
                    linear-gradient(180deg, #7a542b 0%, #d5b375 45%, #8b5d2e 100%);
                background-size: cover, cover, cover, cover;
                background-position: center;
                background-attachment: fixed;
                color: var(--ink);
            }

            [data-testid="stAppViewContainer"]::before {
                content: "";
                position: fixed;
                inset: 0;
                pointer-events: none;
                opacity: 0.62;
                mix-blend-mode: multiply;
                background-image:
                    radial-gradient(circle at 18% 20%, rgba(64, 38, 19, 0.28) 0 1px, transparent 2px),
                    radial-gradient(circle at 82% 24%, rgba(64, 38, 19, 0.22) 0 1px, transparent 2px),
                    radial-gradient(circle at 46% 76%, rgba(64, 38, 19, 0.24) 0 1px, transparent 2px),
                    repeating-linear-gradient(12deg, rgba(65, 40, 20, 0.055) 0 1px, transparent 1px 7px),
                    repeating-linear-gradient(98deg, rgba(255, 236, 180, 0.045) 0 1px, transparent 1px 11px);
                background-size: 37px 37px, 51px 51px, 43px 43px, 100% 100%, 100% 100%;
            }

            [data-testid="stAppViewContainer"]::after {
                content: "";
                position: fixed;
                inset: 0;
                pointer-events: none;
                opacity: 0.52;
                background:
                    radial-gradient(ellipse at center, transparent 42%, rgba(45, 27, 14, 0.52) 100%),
                    linear-gradient(180deg, rgba(45, 27, 14, 0.54), transparent 18%, transparent 82%, rgba(45, 27, 14, 0.62));
            }

            .main .block-container {
                max-width: 1180px;
                margin-top: 1rem;
                padding: 1.35rem 1.45rem 3rem 1.45rem;
                padding-bottom: 3rem;
                background:
                    radial-gradient(circle at 12% 18%, rgba(255, 238, 188, 0.46), transparent 20rem),
                    radial-gradient(circle at 92% 86%, rgba(108, 68, 36, 0.18), transparent 17rem),
                    linear-gradient(180deg, rgba(238, 203, 137, 0.88), rgba(212, 172, 105, 0.82));
                border: 1px solid rgba(72, 42, 19, 0.38);
                box-shadow:
                    0 28px 70px rgba(31, 19, 10, 0.34),
                    inset 0 0 42px rgba(71, 43, 21, 0.18);
                clip-path: polygon(
                    0.6% 1.2%, 7% 0.3%, 16% 1.4%, 26% 0.6%, 38% 1.1%,
                    52% 0.4%, 66% 1.2%, 79% 0.5%, 92% 1.1%, 99.4% 0.7%,
                    99.1% 12%, 99.7% 24%, 99.2% 38%, 99.8% 52%, 99.1% 66%,
                    99.6% 80%, 99.2% 98.6%, 90% 99.3%, 77% 98.7%, 64% 99.4%,
                    49% 98.8%, 35% 99.5%, 22% 98.6%, 10% 99.2%, 0.7% 98.7%,
                    1.3% 84%, 0.5% 70%, 1.2% 55%, 0.6% 41%, 1.1% 26%, 0.5% 12%
                );
            }

            h1, h2, h3, [data-testid="stMarkdownContainer"] h1,
            [data-testid="stMarkdownContainer"] h2,
            [data-testid="stMarkdownContainer"] h3 {
                color: var(--ink);
                letter-spacing: 0;
            }

            p, li, label, span, div {
                color: var(--ink);
            }

            .archive-hero {
                position: relative;
                overflow: hidden;
                isolation: isolate;
                border: 2px solid rgba(45, 26, 13, 0.62);
                background:
                    radial-gradient(circle at 18% 16%, rgba(255, 235, 174, 0.55), transparent 9rem),
                    radial-gradient(circle at 75% 34%, rgba(69, 39, 18, 0.34), transparent 8.5rem),
                    radial-gradient(circle at 46% 92%, rgba(56, 32, 15, 0.34), transparent 12rem),
                    linear-gradient(90deg, rgba(55, 31, 14, 0.38), transparent 13%, transparent 88%, rgba(55, 31, 14, 0.42)),
                    url("__OLD_MAP_BG__"),
                    linear-gradient(180deg, #d5ae67, #a86c35);
                background-size: cover, cover, cover, cover, cover, cover;
                background-position: center;
                border-radius: 0;
                padding: 2.05rem 2rem 1.65rem 2rem;
                box-shadow:
                    0 26px 50px rgba(28, 16, 8, 0.38),
                    inset 0 0 0 1px rgba(255, 232, 170, 0.18),
                    inset 0 0 70px rgba(37, 21, 10, 0.52);
                margin: 0.35rem auto 1.35rem auto;
                max-width: 980px;
                filter: contrast(1.08) saturate(0.86);
                clip-path: polygon(
                    0.8% 8%, 3.8% 3%, 7.6% 6%, 12.4% 2.2%, 18.5% 5.3%,
                    25.5% 1.5%, 32.6% 4.8%, 40.2% 2.4%, 48.5% 4.9%,
                    57.4% 1.8%, 66.6% 5.1%, 75.2% 2.1%, 84.8% 5.4%,
                    93.2% 2.6%, 99.1% 7.8%, 97.2% 14.2%, 99.4% 22.6%,
                    97.6% 31.8%, 99.1% 41.5%, 97.4% 51.8%, 99.3% 61.2%,
                    97.7% 70.7%, 98.9% 81.4%, 97.1% 93.6%, 91.6% 97.8%,
                    82.2% 95.7%, 73.1% 98.6%, 64.4% 96.3%, 55.1% 98.8%,
                    45.7% 96.6%, 36% 99%, 27.5% 96.4%, 18.7% 98.8%,
                    10.4% 95.8%, 2% 98.1%, 2.8% 88.4%, 1% 78.7%,
                    2.6% 68.4%, 0.9% 58.6%, 2.4% 48.5%, 0.8% 38.8%,
                    2.7% 28.6%, 0.9% 17.5%
                );
            }

            .archive-hero::before {
                content: "";
                position: absolute;
                inset: 0;
                pointer-events: none;
                z-index: -1;
                opacity: 0.78;
                mix-blend-mode: multiply;
                background:
                    radial-gradient(circle at 3% 8%, rgba(36, 20, 9, 0.94) 0 1.8rem, transparent 1.95rem),
                    radial-gradient(circle at 97% 8%, rgba(36, 20, 9, 0.82) 0 1.9rem, transparent 2.08rem),
                    radial-gradient(circle at 4% 92%, rgba(36, 20, 9, 0.86) 0 1.75rem, transparent 1.95rem),
                    radial-gradient(circle at 97% 91%, rgba(36, 20, 9, 0.9) 0 1.95rem, transparent 2.2rem),
                    radial-gradient(ellipse at 21% 74%, rgba(69, 38, 17, 0.42), transparent 8rem),
                    radial-gradient(ellipse at 77% 23%, rgba(69, 38, 17, 0.36), transparent 7rem),
                    repeating-linear-gradient(7deg, rgba(43, 25, 12, 0.12) 0 1px, transparent 1px 5px),
                    repeating-linear-gradient(96deg, rgba(255, 232, 172, 0.055) 0 1px, transparent 1px 9px),
                    linear-gradient(90deg, rgba(43, 25, 12, 0.62), transparent 11%, transparent 89%, rgba(43, 25, 12, 0.66)),
                    linear-gradient(180deg, rgba(43, 25, 12, 0.62), transparent 15%, transparent 84%, rgba(43, 25, 12, 0.68));
            }

            .archive-hero::after {
                content: "";
                position: absolute;
                inset: 0.95rem 1rem;
                pointer-events: none;
                opacity: 0.58;
                border: 2px solid rgba(48, 28, 14, 0.5);
                border-radius: 44% 56% 53% 47% / 14% 25% 16% 24%;
                background:
                    radial-gradient(circle at 16% 24%, rgba(45, 26, 13, 0.22) 0 0.2rem, transparent 0.28rem),
                    radial-gradient(circle at 63% 72%, rgba(45, 26, 13, 0.18) 0 0.16rem, transparent 0.24rem),
                    radial-gradient(circle at 84% 54%, transparent 0 3.3rem, rgba(48, 28, 14, 0.2) 3.45rem 3.65rem, transparent 3.8rem),
                    repeating-linear-gradient(8deg, transparent 0 10px, rgba(52, 31, 15, 0.08) 11px 12px),
                    repeating-linear-gradient(112deg, transparent 0 18px, rgba(255, 232, 170, 0.04) 19px 20px);
                box-shadow:
                    inset 0 0 28px rgba(48, 28, 14, 0.18),
                    0 0 0 1px rgba(245, 211, 149, 0.08);
            }

            .archive-kicker {
                position: relative;
                display: inline-block;
                color: #4a2a15;
                background: rgba(92, 53, 25, 0.18);
                border: 1px solid rgba(50, 29, 14, 0.34);
                padding: 0.18rem 0.55rem;
                font-size: 0.74rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 700;
                margin-bottom: 0.55rem;
                z-index: 1;
            }

            .archive-hero h1 {
                position: relative;
                margin: 0;
                color: #211309;
                font-size: clamp(2rem, 5vw, 3.7rem);
                line-height: 1.02;
                font-family: Georgia, "Times New Roman", serif;
                font-weight: 800;
                text-transform: none;
                text-shadow:
                    0 1px 0 rgba(255, 229, 172, 0.36),
                    0 2px 8px rgba(39, 22, 10, 0.16);
                z-index: 1;
            }

            .archive-subtitle {
                position: relative;
                color: #432711;
                max-width: 790px;
                margin-top: 0.7rem;
                font-size: 1rem;
                line-height: 1.58;
                z-index: 1;
            }

            .archive-rule {
                position: relative;
                height: 1px;
                margin-top: 1.05rem;
                background:
                    linear-gradient(90deg, transparent, rgba(68, 39, 18, 0.5), transparent);
                z-index: 1;
            }

            .small-muted {
                color: var(--muted-ink);
                font-size: 0.92rem;
                line-height: 1.45;
            }

            [data-testid="stSidebar"] {
                background:
                    radial-gradient(circle at top left, rgba(246, 220, 167, 0.4), transparent 14rem),
                    url("__OLD_MAP_BG__"),
                    linear-gradient(180deg, #b9894f 0%, #8f5c2f 100%);
                background-size: cover;
                background-position: center left;
                border-right: 2px solid rgba(49, 29, 14, 0.48);
                box-shadow: inset -28px 0 45px rgba(45, 27, 14, 0.22);
            }

            [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] span {
                color: var(--ink);
            }

            div[data-testid="stVerticalBlockBorderWrapper"] {
                border-color: rgba(68, 39, 18, 0.48);
                background:
                    radial-gradient(circle at 8% 12%, rgba(255, 241, 204, 0.52), transparent 12rem),
                    linear-gradient(180deg, rgba(232, 196, 124, 0.9), rgba(196, 145, 79, 0.78));
                box-shadow:
                    0 12px 28px rgba(45, 27, 14, 0.18),
                    inset 0 0 24px rgba(68, 39, 18, 0.12);
                border-radius: 0;
                clip-path: polygon(1% 3%, 17% 1%, 32% 2%, 48% 1%, 63% 2%, 81% 1%, 99% 3%, 98% 31%, 99% 49%, 98% 69%, 99% 97%, 76% 99%, 54% 98%, 33% 99%, 14% 98%, 1% 97%, 2% 72%, 1% 48%, 2% 26%);
            }

            div[data-testid="stVerticalBlockBorderWrapper"] h3 {
                font-family: Georgia, "Times New Roman", serif;
            }

            textarea, input, select {
                background-color: rgba(244, 214, 153, 0.88) !important;
                color: var(--ink) !important;
                border-color: rgba(68, 39, 18, 0.5) !important;
            }

            div[data-baseweb="select"] > div,
            div[data-baseweb="popover"] ul,
            div[data-baseweb="menu"] {
                background-color: #f1d59a !important;
                color: #211309 !important;
                border-color: rgba(68, 39, 18, 0.5) !important;
            }

            div[data-baseweb="select"] span,
            div[data-baseweb="popover"] li,
            div[data-baseweb="menu"] li {
                color: #211309 !important;
            }

            textarea:focus, input:focus {
                border-color: var(--gild) !important;
                box-shadow: 0 0 0 1px rgba(184, 138, 68, 0.25) !important;
            }

            .stButton > button {
                border-radius: 0;
                border: 1px solid rgba(68, 39, 18, 0.56);
                background: linear-gradient(180deg, #e8c47c, #c7934f);
                color: var(--ink);
                box-shadow: 0 2px 0 rgba(48, 28, 14, 0.28);
            }

            .stButton > button[kind="primary"],
            button[data-testid="baseButton-primary"] {
                background: linear-gradient(180deg, #7a4a28 0%, #5d351d 100%) !important;
                color: #fff8e8 !important;
                border-color: #4a2b18 !important;
            }

            div[data-baseweb="radio"] label,
            div[data-baseweb="checkbox"] label {
                background: rgba(246, 220, 164, 0.82);
                border: 1px solid rgba(68, 39, 18, 0.42);
                border-radius: 0;
                padding: 0.22rem 0.42rem;
                margin-bottom: 0.24rem;
                box-shadow: inset 0 0 12px rgba(67, 39, 19, 0.08);
            }

            div[data-baseweb="radio"] label p,
            div[data-baseweb="radio"] label span,
            div[data-baseweb="checkbox"] label p,
            div[data-baseweb="checkbox"] label span {
                color: #211309 !important;
                font-weight: 650;
            }

            div[data-baseweb="checkbox"] [aria-checked="true"],
            div[data-baseweb="radio"] [aria-checked="true"] {
                background-color: #5d351d !important;
                border-color: #3b2515 !important;
            }

            div[data-testid="stAlert"] {
                border-radius: 8px;
            }

            [data-testid="stExpander"] {
                border-color: rgba(68, 39, 18, 0.34);
                background: rgba(218, 174, 104, 0.58);
            }
        </style>
        """.replace("__OLD_MAP_BG__", old_map_background),
        unsafe_allow_html=True,
    )


def render_intro() -> None:
    st.markdown(
        f"""
        <section class="archive-hero">
            <div class="archive-kicker">Historical reasoning archive</div>
            <h1>{APP_TITLE}</h1>
            <div class="archive-subtitle">
                Ask one philosopher, convene a council, or stage a debate. Responses are interpretive
                and written in the spirit of each worldview, grounded where possible in the knowledge base,
                not presented as guaranteed historical quotations.
            </div>
            <div class="archive-rule"></div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_profile_sidebar(selected_names: list[str]) -> None:
    with st.sidebar.expander("Selected philosopher notes", expanded=False):
        if not selected_names:
            st.caption("Choose philosophers to see their worldview notes.")
            return

        for name in selected_names:
            profile = get_profile(name)
            full_name = getattr(profile, "full_name", profile.name)
            st.markdown(f"**{profile.name}**")
            st.caption(full_name)
            st.caption(f"{profile.tradition} | {profile.school} | {profile.region}, {profile.era}")
            st.caption(profile.core_worldview)
            st.caption(f"Risk: {profile.danger_if_misunderstood}")


def init_memory() -> None:
    if MEMORY_KEY not in st.session_state:
        st.session_state[MEMORY_KEY] = []
    if ACTIVE_MEMORY_KEY not in st.session_state:
        st.session_state[ACTIVE_MEMORY_KEY] = None


def get_memory_context() -> str:
    history = st.session_state.get(MEMORY_KEY, [])
    active_entry = get_active_memory_entry()
    if not active_entry:
        return build_memory_context(history)

    return build_memory_context([active_entry, *[entry for entry in history if entry is not active_entry]])


def remember_interaction(mode: str, question: str, philosophers: list[str], answer: str) -> None:
    entry = create_memory_entry(mode, question, philosophers, answer)
    st.session_state[MEMORY_KEY] = append_memory_entry(st.session_state.get(MEMORY_KEY, []), entry)
    st.session_state[ACTIVE_MEMORY_KEY] = len(st.session_state[MEMORY_KEY]) - 1


def get_active_memory_entry() -> dict[str, object] | None:
    history = st.session_state.get(MEMORY_KEY, [])
    active_index = st.session_state.get(ACTIVE_MEMORY_KEY)
    if active_index is None:
        return None
    if not isinstance(active_index, int) or active_index < 0 or active_index >= len(history):
        return None
    return history[active_index]


def activate_memory(index: int) -> None:
    history = st.session_state.get(MEMORY_KEY, [])
    if index < 0 or index >= len(history):
        return

    entry = history[index]
    philosophers = tuple(entry.get("philosophers", ()))
    st.session_state[ACTIVE_MEMORY_KEY] = index
    st.session_state[MODE_KEY] = entry.get("mode", "Ask One Philosopher")
    st.session_state[PREFERRED_PHILOSOPHERS_KEY] = philosophers
    if philosophers:
        st.session_state[SINGLE_PHILOSOPHER_KEY] = philosophers[0]
    st.rerun()


def render_memory_sidebar() -> None:
    history = st.session_state.get(MEMORY_KEY, [])
    with st.sidebar.expander("Session memory", expanded=False):
        if not history:
            st.caption("No remembered questions yet.")
        else:
            st.caption(f"Remembering the last {len(history)} interaction(s).")
            for index in range(len(history) - 1, max(-1, len(history) - 6), -1):
                entry = history[index]
                philosophers = ", ".join(entry.get("philosophers", ()))
                label = f"{entry.get('mode', '')}: {entry.get('question', '')[:42]}"
                if st.button(label, key=f"memory_{index}", use_container_width=True):
                    activate_memory(index)
                st.caption(f"Philosophers: {philosophers}")

        if st.button("Clear memory", use_container_width=True):
            st.session_state[MEMORY_KEY] = []
            st.session_state[ACTIVE_MEMORY_KEY] = None
            st.rerun()


def render_active_memory() -> None:
    entry = get_active_memory_entry()
    if not entry:
        return

    philosophers = ", ".join(entry.get("philosophers", ()))
    with st.container(border=True):
        st.caption("Continuing selected memory")
        st.subheader(entry.get("question", "Previous question"))
        st.caption(f"{entry.get('mode', '')} | {philosophers} | {entry.get('created_at', '')}")
        with st.expander("Previous answer", expanded=False):
            st.markdown(str(entry.get("answer", entry.get("answer_preview", ""))))
        if st.button("Stop continuing this memory"):
            st.session_state[ACTIVE_MEMORY_KEY] = None
            st.rerun()


def render_agent_card(title: str, body: str, subtitle: str | None = None) -> None:
    with st.container(border=True):
        st.subheader(title)
        if subtitle:
            st.markdown(f"<div class='small-muted'>{subtitle}</div>", unsafe_allow_html=True)
        st.markdown(body)


def render_tradition_filter() -> tuple[str, tuple[str, ...]]:
    tradition = st.sidebar.selectbox("Philosopher tradition", TRADITION_FILTERS)
    philosopher_names = get_philosopher_names_by_tradition(tradition)
    st.sidebar.caption(f"{len(philosopher_names)} philosophers available")
    return tradition, philosopher_names


def render_language_selector() -> str:
    language = st.sidebar.selectbox(
        "Response language",
        RESPONSE_LANGUAGES,
        key=RESPONSE_LANGUAGE_KEY,
        help="Choose the language used for philosopher answers and council summaries.",
    )
    st.sidebar.caption("Quotes from retrieved sources may stay in their original wording for grounding.")
    return language


def render_single_mode(
    question: str,
    philosopher_names: tuple[str, ...],
    memory_context: str,
    response_language: str,
) -> tuple[bool, str | None]:
    if not philosopher_names:
        st.warning("No philosophers are available for this filter yet.")
        return False, None

    preferred = st.session_state.get(SINGLE_PHILOSOPHER_KEY)
    if preferred not in philosopher_names:
        preferred = "Marcus Aurelius" if "Marcus Aurelius" in philosopher_names else philosopher_names[0]
    default_index = philosopher_names.index(preferred)
    selected = st.selectbox(
        "Choose a philosopher",
        philosopher_names,
        index=default_index,
        key=SINGLE_PHILOSOPHER_KEY,
    )
    render_profile_sidebar([selected])
    submitted = st.button("Ask", type="primary", use_container_width=False)
    if not submitted:
        return False, selected

    if not question.strip():
        st.warning("Please enter a question first.")
        return False, selected

    with st.spinner(f"Consulting {selected}..."):
        result = ask_philosopher(
            selected,
            question,
            memory_context=memory_context,
            response_language=response_language,
        )

    render_agent_card(
        f"{result.philosopher}",
        result.response,
    )
    remember_interaction("Ask One Philosopher", question, [selected], result.response)
    return True, selected


def render_council_mode(
    question: str,
    philosopher_names: tuple[str, ...],
    memory_context: str,
    response_language: str,
) -> tuple[bool, list[str]]:
    if not philosopher_names:
        st.warning("No philosophers are available for this filter yet.")
        return False, []

    st.markdown("Choose at least two philosophers for the council.")
    preferred_names = set(st.session_state.get(PREFERRED_PHILOSOPHERS_KEY, ()))
    default_names = preferred_names or {"Marcus Aurelius", "Buddha", "Nietzsche"}
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
        result = run_council_discussion(
            selected,
            question,
            memory_context=memory_context,
            response_language=response_language,
        )

    st.subheader("Philosopher Perspectives")
    columns = st.columns(2)
    for index, perspective in enumerate(result.perspectives):
        with columns[index % 2]:
            render_agent_card(
                perspective.philosopher,
                perspective.response,
            )

    st.subheader("Council Review")
    render_agent_card("Final Review", result.council_review)
    remember_interaction("Council Discussion", question, selected, result.council_review)
    return True, selected


def render_debate_mode(
    question: str,
    philosopher_names: tuple[str, ...],
    memory_context: str,
    response_language: str,
) -> tuple[bool, list[str]]:
    if not philosopher_names:
        st.warning("No philosophers are available for this filter yet.")
        return False, []

    st.markdown("Choose 2 to 4 philosophers for the debate.")
    preferred_names = set(st.session_state.get(PREFERRED_PHILOSOPHERS_KEY, ()))
    default_names = preferred_names or {"Diogenes", "Machiavelli", "Marcus Aurelius"}
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
        result = run_debate(
            selected,
            question,
            memory_context=memory_context,
            response_language=response_language,
        )

    st.subheader("Opening Views")
    opening_columns = st.columns(2)
    for index, perspective in enumerate(result.opening_views):
        with opening_columns[index % 2]:
            render_agent_card(
                perspective.philosopher,
                perspective.response,
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
    remember_interaction("Debate Mode", question, selected, result.judge_summary)
    return True, selected


def main() -> None:
    configure_page()
    init_memory()
    render_intro()
    render_memory_sidebar()

    modes = ["Ask One Philosopher", "Council Discussion", "Debate Mode"]
    preferred_mode = st.session_state.get(MODE_KEY, modes[0])
    mode_index = modes.index(preferred_mode) if preferred_mode in modes else 0
    mode = st.sidebar.radio(
        "Mode",
        modes,
        index=mode_index,
        key=MODE_KEY,
    )
    _, philosopher_names = render_tradition_filter()
    response_language = render_language_selector()
    memory_context = get_memory_context()
    render_active_memory()

    question = st.text_area(
        "Your question",
        placeholder="Example: Should I leave a stable job to pursue work that feels more meaningful?",
        height=150,
    )

    try:
        if mode == "Ask One Philosopher":
            render_single_mode(question, philosopher_names, memory_context, response_language)
        elif mode == "Council Discussion":
            render_council_mode(question, philosopher_names, memory_context, response_language)
        else:
            render_debate_mode(question, philosopher_names, memory_context, response_language)
    except LLMError as exc:
        st.error(str(exc))
        st.info("Check your Gemini API key, quota, and network connection, then try again.")


if __name__ == "__main__":
    main()
