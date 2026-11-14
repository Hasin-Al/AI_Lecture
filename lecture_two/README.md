# Week 2: Structured extraction with Groq

A small classroom project following **Week_2_Lecture_Notes_Structured_Extraction_with_Groq_API.docx**.
Students turn text into three fields, validate the model's answer, handle failures,
and measure what actually worked.

```text
Source text → prompt contract → Groq → JSON parsing → Pydantic → API response
                                               ↘ evidence and expected-answer checks
```

**Instructor: start with [RUN_GUIDE.md](RUN_GUIDE.md).** It contains the timed
class sequence, exact commands, what to show, and questions to ask.
Students can record observations in [the worksheet](docs/lab-worksheet.md).
For copyable prompts and the “longer is not automatically better” classroom
exercise, use [PROMPT_PLAYBOOK.md](PROMPT_PLAYBOOK.md).
For the lecture-to-file mapping, commands in teaching order, and a trace from
browser input to model output, use [LECTURE_TO_CODE.md](LECTURE_TO_CODE.md).

## Web app: show how prompt changes affect performance

```bash
source .venv/bin/activate
python -m uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000/** for the classroom **Prompt lab**.

To demonstrate **what happens without a rule**, use **Show what a rule changes**
at the top of the page. Each of the six guided experiments loads a relevant
scenario, puts the same base prompt in A and B, and adds exactly one rule to B.
The page highlights the instruction change and explains which output fields
changed, including ties and regressions. Choosing a preset makes no API calls;
click **Compare this input** to run the real experiment.

1. Choose a scenario or enter your own source text.
2. Compare **A (lecture v1)** with **B (lecture v2)**. Both full prompts are editable.
3. Click **Compare this input** to see each contact, wrong fields, raw output,
   JSON/schema/evidence checks, expected-answer match, time, and provider calls.
4. Select **All 20 live scenarios** and click **Run the comparison set**. The table
   fills one case at a time, holding both prompts and all settings fixed.
5. Inspect failures, edit B, and rerun. Download the run before replacing it if you
   want to keep the previous comparison. Exports retain the exact prompts and outputs.
6. Open **Offline failure scenarios** to demonstrate S10–S15 without model calls.

Start with S7 (injection) and E16 (requested contact appears second). Prompt-only
mode isolates prompt changes; then repeat in strict mode to distinguish structure
from correctness. Improved prompts do not guarantee better answers on every run.

For custom input, an expected answer is optional. Leave it blank to inspect output
without an accuracy score. Editing a preset's source clears its old expected answer
to prevent misleading scoring. Batch runs always use the fixed expected answers.
**Stop after this case** lets the current A/B pair finish and stops further requests.
Each case requires two model generations, plus any bounded retries or repairs.

The UI is plain HTML/CSS/JavaScript in `static/`, served directly by FastAPI.
No Node.js, frontend build, or extra runtime dependency is required. The app is
intended for local classroom use; it uses the instructor's backend key.

**Where the model is called:** `app/groq_service.py`, inside `_chat()`:

```python
return self.client.chat.completions.create(
    **params, timeout=min(20, remaining_seconds),
)
```

The request path is browser → `POST /lab/compare` (`app/lab.py`) →
`GroqExtractionService` → Groq. Both the web lab and CLI use `app/evaluation.py`
for grading. The original `POST /extract` endpoint is still available in Swagger.

## Quick start

Use Python 3.11 or newer. Run all commands from this folder.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows: `py -m venv .venv`, then `.venv\Scripts\Activate.ps1`.
`requirements-lock.txt` records the exact versions used during preparation;
install that file instead when reproducing this environment.

This workspace already has an ignored `.env` containing **only the Groq key**
copied from `../lecture_one/.env`. Week 1 files were not changed. For students
starting from a clean copy, copy `.env.example` to `.env` and insert their own key.
Do not overwrite an existing `.env` or distribute yours with the class materials.

```dotenv
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
GROQ_STRUCTURED_MODEL=openai/gpt-oss-20b
```

Both modes use the same model by default to isolate the effect of the output
constraint. The lecture's baseline `llama-3.3-70b-versatile` returned a model-access
error during preparation; `openai/gpt-oss-20b` was available using the Week 1 key.
There is no silent model fallback. Strict support must be checked again before class:
[Groq supported models](https://console.groq.com/docs/models) and
[Structured Outputs](https://console.groq.com/docs/structured-outputs).

```bash
python -m examples.check_setup          # local config check; hides the key
python -m examples.check_setup --live   # model list + two actual Groq calls
python -m examples.check_api            # optional: two live calls through /extract
python -m pytest -v                    # offline; no real model calls
python -m uvicorn app.main:app --reload
```

For the API lesson, open **http://127.0.0.1:8000/docs**. Use `GET /health`, then `POST /extract`:

```json
{
  "text": "Mina Rahman can be reached at mina@example.com. No phone is listed.",
  "mode": "prompt",
  "prompt_version": "v1",
  "repair": false
}
```

Change `mode` to `structured` to send strict JSON Schema. Change `prompt_version`
to `v2` to apply explicit ambiguity rules. Set `repair` to `true` to allow one
repair after a syntactic or schema failure. `repair` defaults to false so the
first failure stays visible during the opening demos.

The response includes `data`, `request_id`, the model and prompt version,
`schema_valid`, `evidence`, `repaired`, and `provider_calls`. A successful status
only promises validated structure. Evidence flags do not certify correctness.
`GET /health` checks local liveness, not provider availability.

## Learn in small steps

| Command | Lecture sections | Network? |
| --- | --- | --- |
| `python -m examples.demo_01_roles` | 4–5: roles and prompt contract | No; `--live` makes two calls |
| `python -m examples.demo_02_schema` | 6: parsing, required nullable fields, schema | No |
| `python -m examples.demo_03_first_call` | 7: first SDK request and finish reason | Yes |
| `python -m examples.demo_04_extract --mode prompt` | 8: raw → parse → validate | Yes |
| `python -m examples.demo_04_extract --mode structured` | 9: strict JSON Schema | Yes |
| `python -m examples.demo_05_evidence` | 12, 14: fabrication and injection | No |
| `python -m examples.demo_06_failures` | 13: broken output and one repair | No |
| `python -m examples.demo_07_tools_and_retries` | 15–16: tool validation and retry policy | No |

Use `--scenario S7 --prompt-version v2` with demo 04 to try the injection example.
Run with `python -m examples...` from the project root, rather than running a file
inside `examples/` directly, so Python can resolve `app` imports.

## Scenario lab and full evaluation

These commands make real API calls using synthetic contacts from `scenarios.py`.
The lab has the lecture's S1–S9. The full set has 20 cases; S10–S15 are separately
covered by deterministic offline tests. Expected answers are explicit product
decisions, especially for multiple contacts and automated senders.

```bash
python run_scenarios.py prompt --prompt-version v1 --output results/lab-v1
python run_scenarios.py prompt --prompt-version v2 --output results/lab-v2
python run_scenarios.py structured --prompt-version v2 --output results/lab-strict

# Same 20 inputs, same expected answers, both output modes:
python run_scenarios.py prompt structured --cases full --prompt-version v2 --repair
```

Use `--limit 1` for a quick pre-class check and `--delay 2` to space requests.
`python run_scenarios.py --help` lists the options. Without positional modes,
both modes run. Without `--output`, a timestamped path is generated in `results/`.
An explicit output name replaces the previous files at that name.

Each run saves JSON and CSV, including raw first/repaired outputs, source text,
expected answers, model IDs, prompt version, the actual prompt and schema,
and measurements. `results/` is ignored because later student datasets may contain
personal information. Saved synthetic observations are useful if class Wi-Fi fails;
label them as earlier observations, never as a fresh live run.

| Measurement | Meaning |
| --- | --- |
| `parse`, `schema` | First response syntax and structure; repair never changes these |
| `final_schema` | Valid final response, after repair if enabled |
| `evidence` | Every final value passes the simple source-presence heuristic |
| `match` | Final data exactly matches the expected answer |
| First/final validity | Valid cases / all attempted cases, including provider failures |
| Field accuracy | Correct final fields / (3 × all cases); invalid cases score 0 |
| Repair rate | Cases attempting an output repair / all cases |
| Average seconds | Whole case duration, including retries and repair; excludes inter-case delay |
| Calls per success | Actual provider attempts / schema-valid final cases; `null` if none |

“First response” means the first returned output after any transient provider
retries. Requests that never returned usable content still count as provider
calls; a case that exhausts retries stays in the validity denominator.

Exit code 1 means at least one case never produced valid output. Semantic mismatches
are recorded observations and do not alone set exit code 1. For serious conclusions,
repeat runs and report variability: one 20-case run is a teaching exercise.

## Where the code lives

| File | Responsibility |
| --- | --- |
| `app/schemas.py` | Input, model-output, API-response, and local tool contracts |
| `app/prompts.py` | Trusted rules, v1/v2, and repair instructions |
| `app/config.py` | `.env` settings; credentials are masked and loaded only when needed |
| `app/groq_service.py` | SDK call, local validation, and at most one repair |
| `app/evidence.py` | Small source-presence heuristic, with deliberate limitations |
| `app/retry.py` | Bounded transient retries, Retry-After, and timeout policy |
| `app/main.py` | `/health`, `/extract`, safe errors, and request IDs |
| `app/lab.py`, `app/evaluation.py` | Web comparison endpoints and grading shared with the CLI |
| `app/offline_lab.py` | The six controlled S10–S15 demonstrations |
| `static/` | Small browser interface, with no framework or build step |
| `scenarios.py`, `run_scenarios.py` | Fixed teaching cases and measured results |
| `tests/` | Network-blocked tests; fake provider replies make failures repeatable |

Start reading with `schemas.py` → `prompts.py` → `groq_service.py` → `main.py`.
There is no frontend framework, database, CRM connection, or side-effecting tool.
The web lab is the classroom interface; Swagger remains available for teaching HTTP requests.

## Failure policy and teaching limits

| Failure | Behavior |
| --- | --- |
| Empty, blank, >8,000-character input, invalid mode/version | 422 before any model request |
| Empty/malformed content, missing/extra key, wrong type | Reject, or one repair if enabled; validate again |
| `length`, refusal, missing choices, unexpected finish reason | Reject incomplete generation without repair |
| 429, connection failure, 5xx | Up to 3 attempts per generation, exponential backoff + jitter |
| Retry-After | Honor seconds or HTTP date; stop if it exceeds the retry budget |
| Timeout | No automatic retry; endpoint returns 504 |
| Authentication, permission, unsupported model/schema | No unchanged retry; safe 502 |
| Valid shape but wrong values | Evidence flags and expected-answer tests expose some failures |

SDK retries are disabled. Each generation has a 45-second retry scheduling budget
and at most a 20-second timeout per SDK request. HTTP timeouts constrain I/O waits,
so this is not hard wall-clock cancellation. A repair is a second generation with
its own budget: at most 6 provider attempts in total. A long Retry-After ends the
attempt instead of being capped and retried too early.

The evidence function follows the lecture's deliberately basic matching:
email substring, phone digits, and name words. It can match the wrong person's
email, concatenate unrelated digits, or accept all-null output that missed real
details. It is not an authorization or security boundary. Plain string fields
also do not validate email syntax. These are discussion points, not hidden claims.

See [the worksheet and exercises](docs/lab-worksheet.md) and
[verification observations](docs/verification.md) for the prepared class evidence.

## Troubleshooting

- **Import error:** activate `.venv`, run from this folder, and use `python -m ...`.
- **Missing/invalid key:** check `.env` locally; never paste it into a model prompt.
- **Model unavailable / strict call rejected:** run `examples.check_setup --live`;
  verify access and strict support. Keep the failure visible; do not silently switch modes.
- **Rate limit:** wait and rerun with `--delay 2`; use the offline demos meanwhile.
- **Port 8000 in use:** add `--port 8001` and open `http://127.0.0.1:8001/docs`.
- **No internet:** schema, evidence, failure, tool, and test lessons still work.
- **Before committing:** run `git check-ignore .env`. This folder belongs to the
  parent `AI_Course` Git repository; keep the Week 2 `.gitignore` when sharing it.

Official references: [Groq SDK](https://github.com/groq/groq-python),
[Pydantic models](https://docs.pydantic.dev/latest/concepts/models/),
[FastAPI request bodies](https://fastapi.tiangolo.com/tutorial/body/).
