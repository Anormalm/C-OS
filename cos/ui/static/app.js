const ingestForm = document.getElementById("ingestForm");
const retrieveForm = document.getElementById("retrieveForm");
const temporalForm = document.getElementById("temporalForm");

const ingestResult = document.getElementById("ingestResult");
const retrieveResult = document.getElementById("retrieveResult");
const temporalResult = document.getElementById("temporalResult");
const coachResult = document.getElementById("coachResult");
const wizardResult = document.getElementById("wizardResult");
const todayResult = document.getElementById("todayResult");
const onboardingResult = document.getElementById("onboardingResult");
const weeklyResult = document.getElementById("weeklyResult");
const qualityResult = document.getElementById("qualityResult");
const evaluationResult = document.getElementById("evaluationResult");
const insightResult = document.getElementById("insightResult");
const personaResult = document.getElementById("personaResult");

const loadSampleBtn = document.getElementById("loadSample");
const coachAdviceBtn = document.getElementById("coachAdviceBtn");
const coachCheckinBtn = document.getElementById("coachCheckinBtn");

const refreshTodayBtn = document.getElementById("refreshToday");
const refreshOnboardingBtn = document.getElementById("refreshOnboarding");
const loadStarterPackBtn = document.getElementById("loadStarterPack");
const runWeeklySummaryBtn = document.getElementById("runWeeklySummary");
const runTemporalQueryBtn = document.getElementById("runTemporalQuery");
const refreshQualityBtn = document.getElementById("refreshQuality");
const runEvaluationBtn = document.getElementById("runEvaluation");
const refreshInsightsBtn = document.getElementById("refreshInsights");
const refreshPersonasBtn = document.getElementById("refreshPersonas");

const wizardLoadStarterBtn = document.getElementById("wizardLoadStarter");
const wizardAskFirstBtn = document.getElementById("wizardAskFirst");
const wizardAdviceFirstBtn = document.getElementById("wizardAdviceFirst");
const suggestionButtons = document.querySelectorAll("[data-query-suggestion]");

let lastCoachContext = { persona: "general", focus: null };
const DRAFT_NOTE_KEY = "cos_draft_note";
const DRAFT_REFLECTION_KEY = "cos_draft_reflection";

async function api(path, method = "GET", body = null) {
  const options = { method, headers: {} };
  if (body !== null) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const response = await fetch(path, options);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `HTTP ${response.status}`);
  }
  return response.json();
}

function setBusy(target, text) {
  target.innerHTML = `<p class="meta">${escapeHtml(text)}</p>`;
}

function timestampFromLocal(value) {
  if (!value) {
    return null;
  }
  return new Date(value).toISOString();
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll("\"", "&quot;")
    .replaceAll("'", "&#039;");
}

function renderCards(rows, rowRenderer, emptyText = "No results yet.") {
  if (!rows || rows.length === 0) {
    return `<p class="meta">${escapeHtml(emptyText)}</p>`;
  }
  return `<div class="card-list">${rows.map(rowRenderer).join("")}</div>`;
}

function coachPayload() {
  return {
    persona: document.getElementById("persona").value,
    focus: document.getElementById("focusArea").value || null
  };
}

function renderAdvice(adviceResponse, includeIngestion = null) {
  const rows = adviceResponse.advice || [];
  if (!rows.length) {
    return `<p class="meta">No advice generated yet.</p>`;
  }

  const primary = rows[0];
  const nextAction = primary.actions && primary.actions.length ? primary.actions[0] : "No action suggested.";
  const additional = rows.slice(1);
  const additionalHtml = additional.length
    ? `<details><summary>Show more suggestions</summary>${renderCards(
        additional,
        (item) => `
          <article class="memory-card">
            <p><strong>${escapeHtml(item.title)}</strong></p>
            <p class="meta">${escapeHtml(item.why)}</p>
          </article>
        `
      )}</details>`
    : "";

  const ingestHeader = includeIngestion
    ? `<p class="meta">Reflection saved (${includeIngestion.statement_count} statements).</p>`
    : "";

  return `
    ${ingestHeader}
    <article class="memory-card" data-advice-title="${escapeHtml(primary.title)}">
      <p><strong>${escapeHtml(primary.title)}</strong></p>
      <p>${escapeHtml(primary.why)}</p>
      <p><strong>Next action:</strong> ${escapeHtml(nextAction)}</p>
      <div class="actions">
        <button class="feedback-btn" data-rating="useful" data-title="${escapeHtml(primary.title)}" data-action="${escapeHtml(nextAction)}" data-note="done" type="button">Done</button>
        <button class="feedback-btn ghost" data-rating="not_useful" data-title="${escapeHtml(primary.title)}" type="button">Not Useful</button>
      </div>
      <details>
        <summary>Why this recommendation</summary>
        <p class="meta">Priority: ${escapeHtml(primary.priority)} | Confidence: ${((primary.confidence || 0) * 100).toFixed(0)}%</p>
        <p class="meta"><strong>Evidence:</strong> ${(primary.evidence || []).map(escapeHtml).join(" | ")}</p>
      </details>
    </article>
    ${additionalHtml}
    <p class="meta">${escapeHtml(adviceResponse.caution || "")}</p>
  `;
}

function renderNextStep(stepResponse) {
  const alternatives = (stepResponse.alternatives || []).filter(Boolean);
  const alternativesText = alternatives.length ? alternatives.join(" | ") : "No alternatives yet.";
  return `
    <article class="memory-card" data-advice-title="${escapeHtml(stepResponse.title)}">
      <p><strong>${escapeHtml(stepResponse.title)}</strong></p>
      <p>${escapeHtml(stepResponse.why)}</p>
      <p><strong>Do this next (${escapeHtml(stepResponse.estimated_minutes)} min):</strong> ${escapeHtml(stepResponse.action)}</p>
      <div class="actions">
        <button class="feedback-btn" data-rating="useful" data-title="${escapeHtml(stepResponse.title)}" data-action="${escapeHtml(stepResponse.action)}" data-note="done" type="button">I did this</button>
        <button class="feedback-btn ghost" data-rating="not_useful" data-title="${escapeHtml(stepResponse.title)}" type="button">Not Useful</button>
        <button class="more-options-btn ghost" type="button">Show More Options</button>
      </div>
      <details>
        <summary>Why this suggestion</summary>
        <p class="meta">Confidence: ${((stepResponse.confidence || 0) * 100).toFixed(0)}%</p>
        <p class="meta">Alternative directions: ${escapeHtml(alternativesText)}</p>
      </details>
      <p class="meta">${escapeHtml(stepResponse.caution || "")}</p>
    </article>
  `;
}

loadSampleBtn.addEventListener("click", () => {
  document.getElementById("source").value = "journal";
  document.getElementById("noteText").value = [
    "2025-01-02 Atlas is active.",
    "Atlas uses Neo4j.",
    "Atlas requires GPU infrastructure.",
    "2025-03-01 Atlas is paused."
  ].join("\n");
  localStorage.setItem(DRAFT_NOTE_KEY, document.getElementById("noteText").value);
});

ingestForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  ingestResult.textContent = "Saving...";
  try {
    const payload = {
      text: document.getElementById("noteText").value,
      source_type: "note",
      source_uri: document.getElementById("source").value || "web-ui://manual-entry",
      valid_from: timestampFromLocal(document.getElementById("validFrom").value),
      metadata: { ui: "simplified-workspace" }
    };
    const result = await api("/ingest/text", "POST", payload);
    ingestResult.textContent = `Saved ${result.statement_count} statements.`;
    localStorage.removeItem(DRAFT_NOTE_KEY);
    document.getElementById("noteText").value = "";
    document.getElementById("source").value = "";
    document.getElementById("validFrom").value = "";
    await refreshToday();
  } catch (error) {
    ingestResult.textContent = `Save failed: ${error.message}`;
  }
});

retrieveForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await runSearch();
});

async function runSearch(queryOverride = null) {
  setBusy(retrieveResult, "Searching...");
  try {
    const query = queryOverride || document.getElementById("question").value;
    const rows = await api("/query/retrieve", "POST", { query, query_type: "exploratory", top_k: 5 });
    retrieveResult.innerHTML = renderCards(
      rows,
      (row) => {
        const p = row.payload || {};
        const line =
          p.relation && p.subject && p.object
            ? `${p.subject_label || p.subject} ${p.relation} ${p.object_label || p.object}`
            : p.name || "Memory item";
        return `
          <article class="memory-card">
            <p><strong>${escapeHtml(line)}</strong></p>
            <p class="meta">${escapeHtml(row.explanation || "")}</p>
          </article>
        `;
      },
      "No memory found yet."
    );
    await refreshToday();
  } catch (error) {
    retrieveResult.innerHTML = `<p class="meta">Search failed: ${escapeHtml(error.message)}</p>`;
  }
}

coachAdviceBtn.addEventListener("click", async () => {
  setBusy(coachResult, "Generating next step...");
  try {
    const payload = coachPayload();
    lastCoachContext = payload;
    const result = await api("/coach/next-step", "POST", payload);
    coachResult.innerHTML = renderNextStep(result);
    await refreshToday();
  } catch (error) {
    coachResult.innerHTML = `<p class="meta">Advice failed: ${escapeHtml(error.message)}</p>`;
  }
});

coachCheckinBtn.addEventListener("click", async () => {
  setBusy(coachResult, "Saving reflection and generating advice...");
  const reflection = document.getElementById("reflection").value.trim();
  if (!reflection) {
    coachResult.innerHTML = `<p class="meta">Add a reflection first.</p>`;
    return;
  }
  try {
    const payload = { ...coachPayload(), reflection };
    lastCoachContext = payload;
    const result = await api("/coach/checkin", "POST", payload);
    coachResult.innerHTML = renderAdvice(result.advice, result.ingestion);
    localStorage.removeItem(DRAFT_REFLECTION_KEY);
    document.getElementById("reflection").value = "";
    await refreshToday();
  } catch (error) {
    coachResult.innerHTML = `<p class="meta">Check-in failed: ${escapeHtml(error.message)}</p>`;
  }
});

coachResult.addEventListener("click", async (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) {
    return;
  }

  if (target.classList.contains("more-options-btn")) {
    setBusy(coachResult, "Loading more options...");
    try {
      const result = await api("/coach/advice", "POST", {
        persona: lastCoachContext.persona || "general",
        focus: lastCoachContext.focus || null,
      });
      coachResult.innerHTML = renderAdvice(result);
      await refreshToday();
    } catch (error) {
      coachResult.innerHTML = `<p class="meta">Could not load more options: ${escapeHtml(error.message)}</p>`;
    }
    return;
  }

  if (!target.classList.contains("feedback-btn")) {
    return;
  }
  const title = target.dataset.title || "";
  const rating = target.dataset.rating || "";
  const note = target.dataset.note || null;
  const actionText = target.dataset.action || null;
  if (!title || !rating) {
    return;
  }
  target.textContent = "Saving...";
  target.setAttribute("disabled", "true");
  try {
    if (note === "done" && actionText) {
      await api("/today/action", "POST", {
        action_text: actionText,
        advice_title: title,
        persona: lastCoachContext.persona || "general",
        focus: lastCoachContext.focus || null,
        note: "completed from UI"
      });
    }
    await api("/coach/feedback", "POST", {
      advice_title: title,
      rating,
      persona: lastCoachContext.persona || "general",
      context_focus: lastCoachContext.focus || null,
      note
    });
    target.textContent = rating === "useful" ? "Saved as Done" : "Saved";
    await refreshToday();
  } catch (error) {
    target.textContent = "Retry";
    target.removeAttribute("disabled");
  }
});

async function refreshToday() {
  setBusy(todayResult, "Loading your day...");
  try {
    const brief = await api("/today/brief");
    const progress = ((brief.onboarding_progress || 0) * 100).toFixed(0);
    const habitState =
      Number(progress) >= 80 ? "Strong rhythm" : Number(progress) >= 40 ? "Building momentum" : "Getting started";

    todayResult.innerHTML = `
      <div class="card-list">
        <article class="memory-card">
          <p><strong>Do this now</strong></p>
          <p>${escapeHtml(brief.next_action || "No immediate action yet. Ask for advice to generate one.")}</p>
        </article>
        <article class="memory-card">
          <p><strong>Reminder</strong></p>
          <p>${escapeHtml(brief.reminder || "")}</p>
        </article>
        <article class="memory-card">
          <p><strong>This Week Snapshot</strong></p>
          <p>${escapeHtml(brief.weekly_snippet || "")}</p>
          <p class="meta">Habit status: ${habitState}</p>
          <p class="meta">Onboarding progress: ${progress}%</p>
          <p class="meta">Completed actions (7d): ${brief.completed_actions_last_7d || 0}</p>
        </article>
      </div>
    `;
  } catch (error) {
    todayResult.innerHTML = `<p class="meta">Could not load Today card: ${escapeHtml(error.message)}</p>`;
  }
}

async function refreshOnboarding() {
  setBusy(onboardingResult, "Loading...");
  try {
    const status = await api("/onboarding/status");
    const percent = ((status.progress_ratio || 0) * 100).toFixed(0);
    onboardingResult.innerHTML = `
      <p><strong>Progress: ${percent}%</strong></p>
      <p class="meta">${escapeHtml(status.recommended_next_step || "")}</p>
      ${renderCards(
        status.steps || [],
        (step) => `
          <article class="memory-card">
            <p><strong>${escapeHtml(step.title)}</strong></p>
            <p class="meta">${step.completed}/${step.target}</p>
          </article>
        `
      )}
    `;
  } catch (error) {
    onboardingResult.innerHTML = `<p class="meta">Load failed: ${escapeHtml(error.message)}</p>`;
  }
}

async function loadStarterPack() {
  setBusy(wizardResult, "Loading starter data...");
  try {
    const result = await api("/onboarding/starter-pack", "POST", {});
    wizardResult.innerHTML = `<p class="meta">Starter data loaded (${result.ingested} notes).</p>`;
    await refreshToday();
    await refreshOnboarding();
  } catch (error) {
    wizardResult.innerHTML = `<p class="meta">Starter load failed: ${escapeHtml(error.message)}</p>`;
  }
}

loadStarterPackBtn.addEventListener("click", loadStarterPack);
wizardLoadStarterBtn.addEventListener("click", loadStarterPack);

wizardAskFirstBtn.addEventListener("click", async () => {
  const query = "What changed recently?";
  document.getElementById("question").value = query;
  await runSearch(query);
  wizardResult.innerHTML = `<p class="meta">Step 2 complete. You ran your first search.</p>`;
});

wizardAdviceFirstBtn.addEventListener("click", async () => {
  setBusy(wizardResult, "Generating first advice...");
  try {
    const result = await api("/coach/next-step", "POST", { persona: "general" });
    coachResult.innerHTML = renderNextStep(result);
    wizardResult.innerHTML = `<p class="meta">Step 3 complete. Your first next-step recommendation is ready.</p>`;
    await refreshToday();
  } catch (error) {
    wizardResult.innerHTML = `<p class="meta">Advice failed: ${escapeHtml(error.message)}</p>`;
  }
});

refreshTodayBtn.addEventListener("click", refreshToday);
refreshOnboardingBtn.addEventListener("click", refreshOnboarding);

runTemporalQueryBtn.addEventListener("click", async () => {
  setBusy(temporalResult, "Running...");
  try {
    const rows = await api("/query/temporal", "POST", {
      at_time: timestampFromLocal(document.getElementById("atDate").value),
      entity: document.getElementById("entity").value || null
    });
    temporalResult.innerHTML = renderCards(
      rows,
      (row) => `
        <article class="memory-card">
          <p><strong>${escapeHtml(row.subject_label || row.subject)} ${escapeHtml(row.relation)} ${escapeHtml(row.object_label || row.object)}</strong></p>
          <p class="meta">${new Date(row.valid_from).toLocaleString()}</p>
        </article>
      `,
      "No timeline results."
    );
  } catch (error) {
    temporalResult.innerHTML = `<p class="meta">Timeline failed: ${escapeHtml(error.message)}</p>`;
  }
});

function weeklyPayload() {
  return {
    persona: document.getElementById("persona").value,
    focus: document.getElementById("weeklyFocus").value || null,
    days: Number(document.getElementById("weeklyDays").value || "7")
  };
}

runWeeklySummaryBtn.addEventListener("click", async () => {
  setBusy(weeklyResult, "Generating...");
  try {
    const result = await api("/summary/weekly", "POST", weeklyPayload());
    weeklyResult.innerHTML = `
      ${renderCards(
        [
          { title: "Highlights", items: result.highlights || [] },
          { title: "Wins", items: result.wins || [] },
          { title: "Risks", items: result.risks || [] }
        ],
        (section) => `
          <article class="memory-card">
            <p><strong>${escapeHtml(section.title)}</strong></p>
            <p class="meta">${section.items.map(escapeHtml).join("<br>")}</p>
          </article>
        `
      )}
    `;
  } catch (error) {
    weeklyResult.innerHTML = `<p class="meta">Weekly summary failed: ${escapeHtml(error.message)}</p>`;
  }
});

async function refreshQuality() {
  setBusy(qualityResult, "Loading...");
  try {
    const result = await api("/quality/dashboard");
    qualityResult.innerHTML = `
      ${renderCards(
        [
          ["Onboarding", `${((result.onboarding_progress || 0) * 100).toFixed(0)}%`],
          ["Advice useful", `${((result.advice_useful_rate || 0) * 100).toFixed(1)}%`],
          ["Retrieval queries", `${result.retrieval_queries || 0}`],
          ["Avg retrieval latency", `${((result.latency_ms_avg || {}).retrieval_ms || 0).toFixed(1)} ms`]
        ],
        (row) => `
          <article class="memory-card">
            <p><strong>${escapeHtml(row[0])}</strong></p>
            <p>${escapeHtml(row[1])}</p>
          </article>
        `
      )}
      <p class="meta">${(result.recommendations || []).map(escapeHtml).join("<br>")}</p>
    `;
  } catch (error) {
    qualityResult.innerHTML = `<p class="meta">Quality load failed: ${escapeHtml(error.message)}</p>`;
  }
}

refreshQualityBtn.addEventListener("click", refreshQuality);

runEvaluationBtn.addEventListener("click", async () => {
  setBusy(evaluationResult, "Running benchmark...");
  try {
    const topK = Number(document.getElementById("evaluationTopK").value || "3");
    const result = await api("/evaluation/run", "POST", { top_k: topK, dataset: "default" });
    evaluationResult.innerHTML = `
      ${renderCards(
        [
          ["Hybrid Hit@" + result.top_k, `${((result.hybrid_hit_at_k || 0) * 100).toFixed(1)}%`],
          ["Vector Hit@" + result.top_k, `${((result.vector_hit_at_k || 0) * 100).toFixed(1)}%`],
          ["Gain", `${(result.gain_over_vector || 0).toFixed(3)}`]
        ],
        (row) => `
          <article class="memory-card">
            <p><strong>${escapeHtml(row[0])}</strong></p>
            <p>${escapeHtml(row[1])}</p>
          </article>
        `
      )}
      <p class="meta">${(result.notes || []).map(escapeHtml).join("<br>")}</p>
    `;
    await refreshQuality();
  } catch (error) {
    evaluationResult.innerHTML = `<p class="meta">Benchmark failed: ${escapeHtml(error.message)}</p>`;
  }
});

refreshInsightsBtn.addEventListener("click", async () => {
  setBusy(insightResult, "Loading...");
  try {
    const result = await api("/insights/summary");
    insightResult.innerHTML = `
      ${renderCards(
        [
          ["Contradictions", `${((result.contradiction_rate || 0) * 100).toFixed(1)}%`],
          ["Deduplication", `${((result.deduplication_rate || 0) * 100).toFixed(1)}%`],
          ["Recurring Topics", (result.recurring_topics || []).slice(0, 5).map((r) => r.label).join(", ") || "None"]
        ],
        (row) => `
          <article class="memory-card">
            <p><strong>${escapeHtml(row[0])}</strong></p>
            <p class="meta">${escapeHtml(row[1])}</p>
          </article>
        `
      )}
    `;
  } catch (error) {
    insightResult.innerHTML = `<p class="meta">Insights failed: ${escapeHtml(error.message)}</p>`;
  }
});

refreshPersonasBtn.addEventListener("click", async () => {
  setBusy(personaResult, "Loading...");
  try {
    const personas = await api("/coach/personas");
    personaResult.innerHTML = renderCards(
      personas,
      (item) => `
        <article class="memory-card">
          <p><strong>${escapeHtml(item.persona)}</strong></p>
          <p class="meta">Cadence: ${escapeHtml(item.cadence)}</p>
        </article>
      `
    );
  } catch (error) {
    personaResult.innerHTML = `<p class="meta">Templates failed: ${escapeHtml(error.message)}</p>`;
  }
});

refreshToday();
refreshOnboarding();
refreshQuality();

const noteField = document.getElementById("noteText");
const reflectionField = document.getElementById("reflection");
const savedNoteDraft = localStorage.getItem(DRAFT_NOTE_KEY);
const savedReflectionDraft = localStorage.getItem(DRAFT_REFLECTION_KEY);

if (savedNoteDraft && !noteField.value) {
  noteField.value = savedNoteDraft;
}
if (savedReflectionDraft && !reflectionField.value) {
  reflectionField.value = savedReflectionDraft;
}

noteField.addEventListener("input", () => {
  localStorage.setItem(DRAFT_NOTE_KEY, noteField.value);
});

reflectionField.addEventListener("input", () => {
  localStorage.setItem(DRAFT_REFLECTION_KEY, reflectionField.value);
});

suggestionButtons.forEach((button) => {
  button.addEventListener("click", async () => {
    const query = button.dataset.querySuggestion || "";
    if (!query) {
      return;
    }
    document.getElementById("question").value = query;
    await runSearch(query);
  });
});
