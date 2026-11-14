# Week 2 classroom implementation

Build the lecture's contact extraction project for a 110–130 minute class.
Use ordinary synchronous Python functions, the official Groq SDK, Pydantic v2,
and FastAPI's built-in Swagger page. No frontend framework or database is needed.

1. Define tests for required nullable fields, input validation, provider failures,
   one repair, bounded retries, evidence checks, and evaluation accounting.
2. Implement the small `app/` modules using the lecture's names. Keep trusted
   task rules in system messages and source/repair data in user messages.
3. Add numbered runnable demos: roles, schema, first call, extraction modes,
   evidence, malformed output/repair, and tool validation/retries.
4. Preserve S1–S9, add 11 evaluation cases, and record first/final validity,
   expected-answer accuracy, latency, repairs, and actual provider attempts.
5. Write a timed teaching guide, worksheet, setup instructions, and exercises.
6. Run offline tests without credentials, deterministic demos, and live Groq
   checks in both modes. Save genuine evaluation observations separately.

Defaults chosen for this teaching project: v1 for the first lab; explicit v2
rules for comparison; optional one-repair switch; evidence is reported rather
than advertised as proof of correctness. The endpoint has no side-effecting tools.
Reuse only the Groq key from Week 1 in an ignored local `.env`.

Completed: the app, seven demos, scenario runner, teaching guide, worksheet, and
109 offline tests are implemented, including the browser comparison API and guided rule experiments. Both API modes were verified live. Recorded
20-case runs and the observed S7 failure are in `docs/verification.md`.
The live model check required replacing the unavailable lecture baseline with
`openai/gpt-oss-20b` (also the existing Week 1 model) for both modes.

The follow-up classroom web app is served by FastAPI at `/`: editable A/B prompts,
custom input, all 20 live scenarios with progressive scoring, and offline S10–S15.
Its grading is shared with the CLI in `app/evaluation.py`. Browser checks covered
a real two-call S7 comparison, simulated batch interactions, and responsive layout.

Small correctness fixes to the lecture snippets: reject whitespace-only input;
reject non-stop finish reasons; never retry timeouts; honor Retry-After;
retain v2 rules during repair; keep network failures in evaluation denominators;
count retries as calls; include repair time in latency.
