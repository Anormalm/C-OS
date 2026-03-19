const ingestForm = document.getElementById("ingestForm");
const retrieveForm = document.getElementById("retrieveForm");
const temporalForm = document.getElementById("temporalForm");
const ingestResult = document.getElementById("ingestResult");
const retrieveResult = document.getElementById("retrieveResult");
const temporalResult = document.getElementById("temporalResult");
const insightResult = document.getElementById("insightResult");
const coachResult = document.getElementById("coachResult");
const personaResult = document.getElementById("personaResult");
const loadSampleBtn = document.getElementById("loadSample");
const refreshInsightsBtn = document.getElementById("refreshInsights");
const coachAdviceBtn = document.getElementById("coachAdviceBtn");
const coachCheckinBtn = document.getElementById("coachCheckinBtn");
const refreshPersonasBtn = document.getElementById("refreshPersonas");

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
  target.innerHTML = `<p class="meta">${text}</p>`;
}

function timestampFromLocal(value) {
  if (!value) {
    return null;
  }
  return new Date(value).toISOString();
}

function renderCards(rows, rowRenderer, emptyText = "No results yet.") {
  if (!rows || rows.length === 0) {
    return `<p class="meta">${emptyText}</p>`;
  }
  return `<div class="card-list">${rows.map(rowRenderer).join("")}</div>`;
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll("\"", "&quot;")
    .replaceAll("'", "&#039;");
}

loadSampleBtn.addEventListener("click", () => {
  document.getElementById("source").value = "personal-notes";
  document.getElementById("noteText").value = [
    "2025-01-02 Atlas is active.",
    "Atlas uses Neo4j.",
    "Atlas requires GPU infrastructure.",
    "2025-03-01 Atlas is paused."
  ].join("\n");
});

ingestForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  ingestResult.textContent = "Saving thought into memory...";
  try {
    const payload = {
      text: document.getElementById("noteText").value,
      source_type: "note",
      source_uri: document.getElementById("source").value || "web-ui://manual-entry",
      valid_from: timestampFromLocal(document.getElementById("validFrom").value),
      metadata: { ui: "non-technical-workspace" }
    };
    const result = await api("/ingest/text", "POST", payload);
    ingestResult.textContent =
      `Saved.\n` +
      `- Chunks processed: ${result.chunk_count}\n` +
      `- Facts extracted: ${result.triple_count}\n` +
      `- Statements stored: ${result.statement_count}\n` +
      `- Contradictions tracked: ${result.contradictions}`;
    refreshInsights();
  } catch (error) {
    ingestResult.textContent = `Could not save thought: ${error.message}`;
  }
});

retrieveForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setBusy(retrieveResult, "Searching memory...");
  try {
    const payload = {
      query: document.getElementById("question").value,
      query_type: document.getElementById("mode").value,
      top_k: 7
    };
    const rows = await api("/query/retrieve", "POST", payload);
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
            <p><strong>${line}</strong></p>
            <p class="meta">Score: ${(row.score || 0).toFixed(3)} | ${row.explanation || ""}</p>
          </article>
        `;
      },
      "Nothing matched yet. Add more notes first."
    );
  } catch (error) {
    retrieveResult.innerHTML = `<p class="meta">Search failed: ${error.message}</p>`;
  }
});

temporalForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setBusy(temporalResult, "Checking timeline...");
  try {
    const payload = {
      at_time: timestampFromLocal(document.getElementById("atDate").value),
      entity: document.getElementById("entity").value || null
    };
    const rows = await api("/query/temporal", "POST", payload);
    temporalResult.innerHTML = renderCards(
      rows,
      (row) => `
        <article class="memory-card">
          <p><strong>${row.subject_label || row.subject} ${row.relation} ${row.object_label || row.object}</strong></p>
          <p class="meta">Valid from: ${new Date(row.valid_from).toLocaleString()}</p>
          <p class="meta">Source: ${row.source}</p>
        </article>
      `,
      "No facts were active at that time."
    );
  } catch (error) {
    temporalResult.innerHTML = `<p class="meta">Timeline check failed: ${error.message}</p>`;
  }
});

async function refreshInsights() {
  setBusy(insightResult, "Refreshing insights...");
  try {
    const result = await api("/insights/summary");
    const recurring = (result.recurring_topics || []).slice(0, 5);
    const abandoned = (result.abandoned_topics || []).slice(0, 5);
    insightResult.innerHTML = `
      <div class="card-list">
        <article class="memory-card">
          <p><strong>Contradiction Rate</strong></p>
          <p>${((result.contradiction_rate || 0) * 100).toFixed(1)}%</p>
        </article>
        <article class="memory-card">
          <p><strong>Deduplication Rate</strong></p>
          <p>${((result.deduplication_rate || 0) * 100).toFixed(1)}%</p>
        </article>
        <article class="memory-card">
          <p><strong>Recurring Topics</strong></p>
          <p class="meta">${recurring.map((r) => r.label).join(", ") || "None yet"}</p>
        </article>
        <article class="memory-card">
          <p><strong>Abandoned Topics</strong></p>
          <p class="meta">${abandoned.map((r) => r.label).join(", ") || "None yet"}</p>
        </article>
      </div>
    `;
  } catch (error) {
    insightResult.innerHTML = `<p class="meta">Insight refresh failed: ${error.message}</p>`;
  }
}

refreshInsightsBtn.addEventListener("click", refreshInsights);
refreshInsights();

function renderAdvice(adviceResponse, includeIngestion = null) {
  const rows = adviceResponse.advice || [];
  const cards = renderCards(
    rows,
    (item) => `
      <article class="memory-card">
        <p><strong>${escapeHtml(item.title)}</strong></p>
        <p>${escapeHtml(item.why)}</p>
        <p class="meta">Priority: ${escapeHtml(item.priority)} | Confidence: ${((item.confidence || 0) * 100).toFixed(0)}%</p>
        <p class="meta"><strong>Actions:</strong> ${item.actions.map(escapeHtml).join(" ")}</p>
        <p class="meta"><strong>Evidence:</strong> ${item.evidence.map(escapeHtml).join(" | ")}</p>
      </article>
    `,
    "No advice generated yet."
  );

  const ingestHeader = includeIngestion
    ? `<p class="meta">Reflection saved: ${includeIngestion.statement_count} statements, ${includeIngestion.contradictions} contradictions tracked.</p>`
    : "";

  return `
    ${ingestHeader}
    ${cards}
    <p class="meta">${escapeHtml(adviceResponse.caution || "")}</p>
  `;
}

function coachPayload() {
  return {
    persona: document.getElementById("persona").value,
    focus: document.getElementById("focusArea").value || null
  };
}

coachAdviceBtn.addEventListener("click", async () => {
  setBusy(coachResult, "Generating advice...");
  try {
    const result = await api("/coach/advice", "POST", coachPayload());
    coachResult.innerHTML = renderAdvice(result);
  } catch (error) {
    coachResult.innerHTML = `<p class="meta">Advice failed: ${escapeHtml(error.message)}</p>`;
  }
});

coachCheckinBtn.addEventListener("click", async () => {
  const reflection = document.getElementById("reflection").value.trim();
  if (!reflection) {
    coachResult.innerHTML = `<p class="meta">Add a short reflection first, then click again.</p>`;
    return;
  }
  setBusy(coachResult, "Saving reflection and generating advice...");
  try {
    const result = await api("/coach/checkin", "POST", { ...coachPayload(), reflection });
    coachResult.innerHTML = renderAdvice(result.advice, result.ingestion);
    refreshInsights();
  } catch (error) {
    coachResult.innerHTML = `<p class="meta">Check-in failed: ${escapeHtml(error.message)}</p>`;
  }
});

async function refreshPersonas() {
  setBusy(personaResult, "Loading templates...");
  try {
    const personas = await api("/coach/personas");
    personaResult.innerHTML = renderCards(
      personas,
      (item) => `
        <article class="memory-card">
          <p><strong>${escapeHtml(item.persona)}</strong></p>
          <p class="meta">Cadence: ${escapeHtml(item.cadence)}</p>
          <p class="meta">${escapeHtml(item.framing)}</p>
        </article>
      `,
      "No templates found."
    );
  } catch (error) {
    personaResult.innerHTML = `<p class="meta">Could not load templates: ${escapeHtml(error.message)}</p>`;
  }
}

refreshPersonasBtn.addEventListener("click", refreshPersonas);
refreshPersonas();
