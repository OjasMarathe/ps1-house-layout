# PS1 — Engineering Drawing Verification (Agentic + Z3)

Two-agent system that designs a house layout on an L-shaped plot, verifies it
against Seattle Building Code (SBC) setbacks + tree protection using Z3, and
emits a `.dxf` engineering drawing on pass.

- **A1 (Generator)** = Gemini — writes `ezdxf` Python code to draw the house.
- **A2 (Verifier)** = Groq — translates Z3 violations into actionable feedback.
- **Judge** = Z3 SMT solver (deterministic, not the LLM).

## Layout

```
plot.py           plot polygon + tree + entry side
constraints.py    SBC setback / buffer constants with citations
verifier_z3.py    pure Z3 checker — the real judge
geometry_parser.py   regex extractor for ezdxf calls from A1's code
agent1_gemini.py  Gemini call: produces ezdxf Python code
agent2_groq.py    Groq call: turns Z3 violations into feedback for A1
loop.py           orchestrator
output/           per-iteration .dxf files
```

## Run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then paste your GEMINI_API_KEY and GROQ_API_KEY
python loop.py
```

## How the loop works

1. A1 receives plot polygon + tree + SBC rules (+ feedback if iter > 1).
2. A1 emits Python code using `ezdxf` that draws the house outline + door.
3. `geometry_parser.py` regex-extracts the house corners and door position.
4. `verifier_z3.py` builds a Z3 model and checks every constraint.
5. If all pass: execute A1's code, save `.dxf`, done.
6. If any fail: A2 (Groq) reads the Z3 violation list and writes a clear,
   prioritized feedback message. Back to step 1.

## Why this design

The brief says "verifier uses Z3." A common trap is to let the LLM "verify" by
narration. We don't. **Z3 is the deterministic judge**; the LLM only translates
its violations into prose the generator can act on. This makes the system
reproducible and means "passes verification" actually means something.
