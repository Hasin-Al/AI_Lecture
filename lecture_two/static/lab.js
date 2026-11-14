// Plain browser JavaScript: no frontend framework or build step.
const $ = (id) => document.getElementById(id);
let config, busy = false, stopRequested = false;
let currentComparison = null, batchRows = [], batchSettings = null;

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text; // Model output is never HTML.
  if (className) element.className = className;
  return element;
}
function status(message, error = false) {
  $("status").textContent = message;
  $("status").className = error ? "status error" : "status";
}
async function request(path, body) {
  const response = await fetch(path, body === undefined ? {} : {
    method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) {
    const detail = data.detail;
    throw new Error(typeof detail === "string" ? detail :
      Array.isArray(detail) ? detail.map(e => e.msg).join("; ") : detail?.error || `HTTP ${response.status}`);
  }
  return data;
}
function lock(value, batch = false) {
  busy = value;
  document.querySelectorAll("[data-lock]").forEach(el => { el.disabled = value; });
  $("run-offline").disabled = value;
  $("stop").hidden = !value || !batch;
  $("stop").disabled = false;
}
function updateCount() { $("char-count").textContent = `${$("source").value.length} / 8,000`; }
function selectedScenario() { return config.scenarios.find(s => s.id === $("scenario").value); }
function loadScenario() {
  const scenario = selectedScenario();
  $("source").value = scenario?.text || "";
  $("expected").value = scenario ? JSON.stringify(scenario.expected, null, 2) : "";
  updateCount();
}
function guidedExperiment(a = $("prompt-a").value.trim(), b = $("prompt-b").value.trim()) {
  return config.experiments.find(e => e.prompt_a === a && e.prompt_b === b);
}
function updatePromptDifference() {
  const a = $("prompt-a").value.trim().split("\n"), b = $("prompt-b").value.trim().split("\n");
  let start = 0, tail = 0;
  while (start < a.length && start < b.length && a[start] === b[start]) start++;
  while (tail < a.length - start && tail < b.length - start && a[a.length - 1 - tail] === b[b.length - 1 - tail]) tail++;
  const removed = a.slice(start, a.length - tail), added = b.slice(start, b.length - tail);
  $("prompt-diff").textContent = [...removed.map(line => "− " + line), ...added.map(line => "+ " + line)].join("\n") || "The prompts are identical. No instruction was changed.";
  const guided = guidedExperiment();
  $("label-a").textContent = guided ? "Without the rule" : "Baseline";
  $("label-b").textContent = guided ? "With the rule" : "Revised";
  $("version-a").textContent = guided ? "same base" : "editable";
  $("version-b").textContent = guided ? "+ one rule" : "editable";
  const selected = config.experiments.find(e => e.id === $("experiment").value);
  if (selected) $("experiment-question").textContent = selected.question +
    (guided?.id === selected.id ? " Only the displayed rule differs between A and B." : " Prompts edited: reselect this experiment to restore the one-rule comparison.");
}
function loadExperiment() {
  const chosen = config.experiments.find(e => e.id === $("experiment").value);
  $("prompt-a").value = chosen ? chosen.prompt_a : config.prompts.v1;
  $("prompt-b").value = chosen ? chosen.prompt_b : config.prompts.v2;
  if (chosen) {
    $("scenario").value = chosen.scenario_id; loadScenario();
    $("mode").value = "prompt"; $("repair").checked = false;
    $("model-name").textContent = config.models.prompt;
  } else $("experiment-question").textContent = "The original lecture comparison adds several rules at once. Choose a guided experiment to isolate one rule.";
  updatePromptDifference();
  $("comparison-results").hidden = true;
  status(chosen ? "Predict the difference, then click Compare this input. Selecting an experiment makes no model calls." : "Lecture prompts restored. Choose an input to compare.");
}
function readSettings() {
  const settings = {prompt_a: $("prompt-a").value.trim(), prompt_b: $("prompt-b").value.trim(),
    mode: $("mode").value, repair: $("repair").checked};
  if (!settings.prompt_a || !settings.prompt_b) throw new Error("Enter both prompts before comparing.");
  return settings;
}
function readExpected() {
  if (!$("expected").value.trim()) return null;
  let expected;
  try { expected = JSON.parse($("expected").value); }
  catch { throw new Error("Expected answer must be valid JSON, or left blank for an unscored input."); }
  const keys = ["full_name", "email", "phone"];
  if (!expected || Array.isArray(expected) || Object.keys(expected).length !== 3 ||
      !keys.every(k => Object.hasOwn(expected, k) && (expected[k] === null || typeof expected[k] === "string"))) {
    throw new Error("Expected answer needs exactly full_name, email, and phone, each a string or null.");
  }
  return expected;
}
function badge(value, yes = "Match", no = "Mismatch") {
  return node("span", value === null ? "Not scored" : value ? yes : no,
    `badge ${value === null ? "neutral" : value ? "pass" : "fail"}`);
}
function renderOutput(container, row, name, expected) {
  container.replaceChildren();
  const heading = node("div", undefined, "result-title");
  heading.append(node("h3", name), badge(row.match));
  container.append(heading);
  const checks = node("div", undefined, "checks");
  checks.append(badge(row.parse, "JSON ✓", "JSON ✕"), badge(row.schema, "Schema ✓", "Schema ✕"),
    badge(row.evidence, "Evidence ✓", "Evidence ✕"));
  container.append(checks);
  if (row.data) {
    const fields = node("div", undefined, "fields");
    for (const key of ["full_name", "email", "phone"]) {
      const wrong = expected !== null && row.data[key] !== expected[key];
      const field = node("div", undefined, "field-row");
      const value = node("div", JSON.stringify(row.data[key]), `field-value${wrong ? " field-wrong" : ""}`);
      if (wrong) value.append(node("span", `Expected: ${JSON.stringify(expected[key])}`, "field-expected"));
      field.append(node("span", key, "field-key"), value);
      fields.append(field);
    }
    container.append(fields);
  } else container.append(node("p", "No schema-valid contact was returned.", "error-note"));
  if (row.note.trim()) container.append(node("p", row.note.trim(), row.final_schema ? "hint" : "error-note"));
  container.append(node("p", `${row.seconds.toFixed(2)} s · ${row.calls} provider call(s) · ${row.repair_attempted ? "Repair attempted" : "No repair"} · Final schema: ${row.final_schema ? "pass" : "fail"}`, "result-meta"));
  for (const [title, value] of [["Raw first output", row.raw], ["Repaired output", row.repaired_raw], ["Exact prompt used", row.prompt]]) {
    if (value === null || value === undefined) continue;
    const details = node("details");
    details.append(node("summary", title), node("pre", value));
    container.append(details);
  }
}
function showComparison(result) {
  currentComparison = result;
  $("comparison-results").hidden = false;
  $("result-heading").textContent = `Results · ${result.case.id}`;
  $("result-context").textContent = `${result.mode === "structured" ? "Strict JSON Schema" : "Prompt-only"} · ${result.a.model} · ${result.recorded_at_utc} · Source: ${result.case.text}`;
  const experiment = guidedExperiment(result.a.prompt, result.b.prompt);
  renderOutput($("result-a"), result.a, experiment ? "A / Without the rule" : "A / Baseline", result.case.expected);
  renderOutput($("result-b"), result.b, experiment ? "B / With the rule" : "B / Revised", result.case.expected);
  $("result-difference").textContent = describeDifference(result);
}
function describeDifference(result) {
  const a = result.a, b = result.b;
  if (!a.final_schema || !b.final_schema) return "At least one response did not produce a valid contact. Inspect the raw output and error before judging a semantic improvement.";
  const changed = ["full_name", "email", "phone"].filter(key => a.data[key] !== b.data[key]);
  if (!changed.length) return "Both prompts returned the same contact. This run showed no output change from the instruction change. A model may infer a rule even when it is not written down; try more cases before drawing a conclusion.";
  const differences = changed.map(key => `${key}: ${JSON.stringify(a.data[key])} → ${JSON.stringify(b.data[key])}`).join("; ");
  const outcome = a.match === null ? "No expected answer was supplied, so this is a change, not a measured improvement." :
    !a.match && b.match ? "B matched the expected answer; A did not. This is an observed improvement for this case, not a guarantee for future runs." :
    a.match && !b.match ? "A matched the expected answer; B did not. The revised prompt made this case worse." :
    "Neither answer matched the full expected contact. Different output does not necessarily mean better output.";
  return `${differences}. ${outcome}`;
}
async function compareOne() {
  if (busy) return;
  try {
    const settings = readSettings(), expected = readExpected(), text = $("source").value.trim();
    if (!text) throw new Error("Enter source text or choose a scenario first.");
    lock(true);
    $("comparison-results").hidden = true;
    status("Running prompt A, then prompt B on the same input…");
    const result = await request("/lab/compare", {...settings, text, expected, case_id: $("scenario").value});
    showComparison(result);
    status("Comparison complete. Inspect the answer match as well as schema validity.");
  } catch (error) { status(error.message, true); }
  finally { lock(false); }
}
function metrics(side) {
  const rows = batchRows.map(r => r[side]), n = rows.length;
  return {n, matches: rows.filter(r => r.match === true).length,
    schema: rows.filter(r => r.schema).length, final: rows.filter(r => r.final_schema).length,
    fields: rows.reduce((sum, r) => sum + r.correct_fields, 0),
    seconds: n ? rows.reduce((sum, r) => sum + r.seconds, 0) / n : 0,
    calls: rows.reduce((sum, r) => sum + r.calls, 0),
    repairs: rows.filter(r => r.repair_attempted).length};
}
function renderBatch() {
  $("batch-results").hidden = false;
  const scores = $("scoreboard"); scores.replaceChildren();
  for (const [side, label] of [["a", "A / BASELINE"], ["b", "B / REVISED"]]) {
    const m = metrics(side), panel = node("div", undefined, "score-panel");
    panel.append(node("h3", label), node("span", `${m.matches} / ${m.n}`, "score-number"), node("span", "contacts matched", "score-caption"));
    const details = node("div", undefined, "score-metrics");
    for (const text of [`First schema ${m.schema}/${m.n}`, `Final schema ${m.final}/${m.n}`,
      `Fields ${m.fields}/${3*m.n}`, `${m.seconds.toFixed(2)} s avg`, `${m.calls} calls`, `${m.repairs} repairs`]) details.append(node("span", text));
    panel.append(details); scores.append(panel);
  }
  const a = metrics("a"), b = metrics("b"), change = b.matches - a.matches;
  $("batch-conclusion").textContent = !a.n ? "Waiting for the first case…" :
    change === 0 ? `A and B matched the same number of contacts across ${a.n} attempted cases. Inspect individual rows for differences.` :
    `Prompt B matched ${Math.abs(change)} ${change > 0 ? "more" : "fewer"} contact(s) than A: ${change > 0 ? "+" : ""}${(100*change/a.n).toFixed(1)} percentage points across ${a.n} attempted cases.`;
  $("batch-body").replaceChildren();
  batchRows.forEach(result => {
    const tr = node("tr"), scenario = config.scenarios.find(s => s.id === result.case.id);
    const name = node("td"); name.append(node("strong", result.case.id), document.createTextNode(" " + (scenario?.tests || "")));
    tr.append(name);
    for (const side of ["a", "b"]) { const td = node("td"); td.append(badge(result[side].match)); tr.append(td); }
    tr.append(node("td", `${result.a.schema ? "Pass" : "Fail"} / ${result.b.schema ? "Pass" : "Fail"}`),
      node("td", `${result.a.seconds.toFixed(2)} / ${result.b.seconds.toFixed(2)} s`));
    const td = node("td"), button = node("button", "View outputs ↗", "text-button");
    button.addEventListener("click", () => { showComparison(result); $("comparison-results").scrollIntoView({behavior: "smooth", block: "start"}); });
    td.append(button); tr.append(td); $("batch-body").append(tr);
  });
  $("download-batch").disabled = !batchRows.length;
}
async function runAll() {
  if (busy) return;
  try {
    const settings = readSettings();
    const cases = $("case-set").value === "lab" ? config.scenarios.slice(0, 9) : config.scenarios;
    batchSettings = {...settings, started_at_utc: new Date().toISOString(), planned_cases: cases.map(c => c.id)};
    batchRows = []; stopRequested = false; lock(true, true); renderBatch();
    $("batch-context").textContent = `${cases.length} planned cases · ${config.models[settings.mode]} · ${settings.mode} · ${settings.repair ? "One repair enabled" : "Repair disabled"}. The prompts and settings are held fixed for this run.`;
    $("progress-wrap").hidden = false;
    $("progress").max = cases.length; $("progress").value = 0;
    for (const scenario of cases) {
      if (stopRequested) break;
      status(`Comparing ${scenario.id} · ${scenario.tests}. Running A, then B…`);
      $("progress-label").textContent = `${batchRows.length} / ${cases.length} completed · working on ${scenario.id}`;
      const result = await request("/lab/compare", {...settings, text: scenario.text, expected: scenario.expected, case_id: scenario.id});
      batchRows.push(result); renderBatch(); showComparison(result);
      $("progress").value = batchRows.length;
      $("progress-label").textContent = `${batchRows.length} / ${cases.length} completed`;
      if (stopRequested) break;
      // Pace the requests. Provider retries are also bounded in the backend.
      await new Promise(resolve => setTimeout(resolve, 400));
    }
    status(`${stopRequested ? "Stopped" : "Finished"}: ${batchRows.length} of ${cases.length} cases compared. Results are from this live run.`);
  } catch (error) {
    // No fabricated pair if the HTTP request itself fails. Mark the run partial.
    status(`Run incomplete after ${batchRows.length} complete comparison(s): ${error.message}. The interrupted case is not scored.`, true);
  } finally {
    if (batchSettings) batchSettings.completed_cases = batchRows.length;
    lock(false);
  }
}
function download(value, name) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], {type: "application/json"}));
  const link = node("a"); link.href = url; link.download = name; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
async function runOffline() {
  if (busy) return;
  lock(true); status("Running deterministic local demos…");
  try {
    const data = await request("/lab/offline", {});
    $("offline-results").replaceChildren();
    for (const row of data.rows) {
      const card = node("article", undefined, "panel offline-card");
      card.append(badge(row.passed, `${row.id} · demonstrated`, `${row.id} · unexpected failure`), node("h3", row.title), node("p", row.details));
      $("offline-results").append(card);
    }
    status("All six offline demos completed. No live model calls were made.");
  } catch (error) { status(error.message, true); }
  finally { lock(false); }
}
function switchView(offline) {
  $("live-view").hidden = offline; $("offline-view").hidden = !offline;
  $("live-tab").setAttribute("aria-pressed", String(!offline));
  $("offline-tab").setAttribute("aria-pressed", String(offline));
}

$("compare").addEventListener("click", compareOne);
$("run-all").addEventListener("click", runAll);
$("stop").addEventListener("click", () => { stopRequested = true; $("stop").disabled = true; status("Stopping after the current A/B comparison finishes. Its provider calls may still be running."); });
$("scenario").addEventListener("change", loadScenario);
$("source").addEventListener("input", () => { $("scenario").value = "custom"; $("expected").value = ""; updateCount(); });
$("mode").addEventListener("change", () => { $("model-name").textContent = config.models[$("mode").value]; });
$("reset-prompts").addEventListener("click", () => { $("experiment").value = "lecture"; loadExperiment(); });
$("experiment").addEventListener("change", loadExperiment);
$("prompt-a").addEventListener("input", updatePromptDifference);
$("prompt-b").addEventListener("input", updatePromptDifference);
$("live-tab").addEventListener("click", () => switchView(false));
$("offline-tab").addEventListener("click", () => switchView(true));
$("run-offline").addEventListener("click", runOffline);
$("download-single").addEventListener("click", () => { if (currentComparison) download(currentComparison, "prompt-comparison.json"); });
$("download-batch").addEventListener("click", () => download({settings: batchSettings, metrics: {a: metrics("a"), b: metrics("b")}, rows: batchRows}, "prompt-lab-run.json"));

async function init() {
  try {
    config = await request("/lab/config");
    for (const experiment of config.experiments) { const option = node("option", experiment.title); option.value = experiment.id; $("experiment").append(option); }
    const custom = node("option", "Custom text"); custom.value = "custom"; $("scenario").append(custom);
    for (const scenario of config.scenarios) { const option = node("option", `${scenario.id} · ${scenario.tests}`); option.value = scenario.id; $("scenario").append(option); }
    $("scenario").value = "S7"; loadScenario();
    $("prompt-a").value = config.prompts.v1; $("prompt-b").value = config.prompts.v2;
    $("lecture-rules").textContent = config.prompts.v2.slice(config.prompts.v1.length).trim();
    updatePromptDifference();
    $("model-name").textContent = config.models.prompt;
    lock(false); status("Ready. Start with S7, or choose any scenario. Edit prompt B to test your own rule.");
  } catch (error) { status(`Could not load the lab: ${error.message}. Reload after checking the server.`, true); }
}
init();
