# Philosophy Council AI

Philosophy Council AI is a Streamlit full-stack MVP that lets users ask life, ethics, politics, career, discipline, money, and personal decision questions, then receive structured answers from philosopher-style agents.

The app does not pretend to quote historical philosophers. It gives modern interpretations written in the spirit of each philosopher's worldview.

## Features

- Ask One Philosopher mode with Diogenes, Machiavelli, Marcus Aurelius, Nietzsche, Buddha, Confucius, Laozi, Chanakya, Socrates, Plato, Aristotle, Kant, and Camus.
- Council Discussion mode where multiple philosophers answer, followed by a structured Council Review.
- Debate Mode where 2 to 4 philosophers respond, challenge another view, and receive a neutral judge summary.
- Modular agent layer separated from the Streamlit UI.
- Reusable Gemini LLM integration through `utils/llm.py`.
- Centralized prompt construction in `utils/prompts.py`.
- Philosopher profiles with worldview, tone, principles, and misuse risks.
- Philosopher taxonomy metadata for tradition, school, era, region, and future RAG source tags.
- Sidebar filtering for All, Eastern, and Western philosophers.
- Safety handling for self-harm, violence, crime, manipulation, medical, and legal topics.

## Folder Structure

```text
philosophy_council_ai/
├── app.py
├── agents/
│   ├── __init__.py
│   ├── philosopher_profiles.py
│   ├── single_agent.py
│   ├── council_agent.py
│   └── debate_agent.py
├── utils/
│   ├── __init__.py
│   ├── llm.py
│   └── prompts.py
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

On Windows:

```bash
.venv\Scripts\activate
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your environment file:

```bash
copy .env.example .env
```

On macOS or Linux:

```bash
cp .env.example .env
```

Add your Gemini API key to `.env`:

```text
GEMINI_API_KEY=your_real_key_here
GEMINI_MODEL=gemini-2.5-flash
```

Run the app:

```bash
streamlit run app.py
```

## Example Questions

- Should I leave a stable job to pursue work that feels more meaningful?
- How should I handle jealousy when a friend becomes more successful than me?
- Is it better to seek power or peace?
- How do I stay disciplined when motivation disappears?
- Should I forgive someone who betrayed my trust?
- How should I think about money without becoming obsessed with it?
- How would Eastern and Western philosophers disagree about ambition?
- Should I follow duty, happiness, or personal freedom when making a hard decision?

## Design Notes

The code is organized so new philosophers can be added by extending `PHILOSOPHER_PROFILES` in `agents/philosopher_profiles.py`. Each profile includes taxonomy fields such as `tradition`, `school`, `era`, `region`, and `source_tags`, which prepare the app for stronger filtering and future RAG retrieval. Agent orchestration lives in `agents/`, prompt construction lives in `utils/prompts.py`, and provider-specific LLM code lives in `utils/llm.py`.

This foundation is intended to support future upgrades without major rewrites:

- RAG over primary and secondary philosophy sources.
- Saved sessions and conversation history.
- User memory and preference-aware advice.
- Additional modes such as mentor mode, adversarial critique, or historical comparison.
- Swappable LLM providers through a provider interface.
- Structured JSON outputs with schema validation for richer UI rendering.

## Limitations

This MVP uses Gemini generation and profile-based prompting. It is not a historical authority, therapist, doctor, lawyer, or emergency service. Responses should be treated as reflective guidance, not professional advice or guaranteed historical interpretation.
