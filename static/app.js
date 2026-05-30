/* =============================================
   Disaster Management System -- App Logic
   ============================================= */

const API_BASE = "http://localhost:5000";
let currentSessionId = null;

// --- Pipeline Execution ---
async function runPipeline() {
    const location = document.getElementById("location-input").value.trim();
    if (!location) { alert("Please enter a location."); return; }

    const btn = document.getElementById("analyze-btn");
    btn.disabled = true;
    btn.textContent = "Analyzing...";

    // Show progress
    showPanel("progress-panel");
    resetSteps();
    showPanel("loading-bar", true, "active");
    hidePanel("results-grid");
    hidePanel("assessment-panel");
    hidePanel("alert-panel");
    hidePanel("result-banner");

    // Animate steps
    await animateSteps([1, 2, 3, 4, 5, 6]);

    try {
        const resp = await fetch(`${API_BASE}/api/run`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ location }),
        });

        const data = await resp.json();
        if (data.error) { throw new Error(data.error); }

        currentSessionId = data.session_id;
        const state = data.state;

        // Mark steps 1-6 as done
        markStepsDone([1, 2, 3, 4, 5, 6]);
        markStepActive(7);

        // Display results
        displayWeather(state.weather_data);
        displayForecast(state.forecast);
        displayPrediction(state.disaster_prediction);
        displayNews(state.news_context);
        displayAssessment(state.severity, state.department, state.iteration);
        displayAlert(state.alert_message);

        showPanel("results-grid");
        showPanel("assessment-panel");
        showPanel("alert-panel");

        hidePanel("loading-bar");

    } catch (err) {
        alert("Pipeline error: " + err.message);
        hidePanel("loading-bar");
    }

    btn.disabled = false;
    btn.textContent = "Analyze";
}

// --- Human Decision ---
function showRejectForm() {
    document.getElementById("feedback-form").style.display = "block";
    document.getElementById("decision-panel").style.display = "none";
}

async function submitDecision(decision) {
    const feedback = document.getElementById("feedback-input")?.value || "";

    if (decision === "reject" && !feedback.trim()) {
        alert("Please provide feedback explaining why you're rejecting.");
        return;
    }

    const btns = document.querySelectorAll(".btn");
    btns.forEach(b => b.disabled = true);

    try {
        if (decision === "reject") {
            markStepActive(8);
            showPanel("loading-bar", true, "active");
        }

        const resp = await fetch(`${API_BASE}/api/decide`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: currentSessionId,
                decision: decision,
                feedback: feedback,
            }),
        });

        const data = await resp.json();
        if (data.error) { throw new Error(data.error); }

        hidePanel("loading-bar");

        if (data.status === "approved") {
            markStepsDone([7]);
            showResult("approved", "Alert Approved & Dispatched (Dry-Run Mode)");
            hidePanel("alert-panel");

        } else if (data.status === "rejected") {
            currentSessionId = data.session_id;
            const state = data.state;

            markStepsDone([8]);
            markStepActive(7);

            // Update alert and assessment with new data
            displayAssessment(state.severity, state.department, state.iteration);
            displayAlert(state.alert_message);

            // Show decision buttons again
            document.getElementById("decision-panel").style.display = "flex";
            document.getElementById("feedback-form").style.display = "none";
            document.getElementById("feedback-input").value = "";

            // Update insights
            loadInsights();

            showResult("rejected",
                `Self-improvement complete (Iteration ${state.iteration}). New insight: "${data.new_insight || 'N/A'}". Review the updated alert below.`
            );
        }

    } catch (err) {
        alert("Decision error: " + err.message);
    }

    btns.forEach(b => b.disabled = false);
}

// --- Display Functions ---
function displayWeather(w) {
    if (!w) return;
    document.getElementById("weather-data").innerHTML = `
        <div class="data-row"><span class="label">Location</span><span class="value">${w.location || "N/A"}</span></div>
        <div class="data-row"><span class="label">Temperature</span><span class="value">${w.temperature_c}&deg;C</span></div>
        <div class="data-row"><span class="label">Humidity</span><span class="value">${w.humidity_pct}%</span></div>
        <div class="data-row"><span class="label">Wind Speed</span><span class="value">${w.wind_speed_kmh} km/h</span></div>
        <div class="data-row"><span class="label">Rainfall</span><span class="value">${w.rainfall_mm} mm</span></div>
        <div class="data-row"><span class="label">Pressure</span><span class="value">${w.pressure_hpa} hPa</span></div>
        <div class="data-row"><span class="label">Conditions</span><span class="value">${w.description || "N/A"}</span></div>
        <div class="data-row"><span class="label">Source</span><span class="value">${w.source || "N/A"}</span></div>
    `;
}

function displayForecast(f) {
    if (!f) return;
    const h24 = f.forecast_24h || {};
    const h48 = f.forecast_48h || {};
    document.getElementById("forecast-data").innerHTML = `
        <div style="font-weight:600;margin-bottom:6px;color:var(--text-primary);">Peak Values (48h)</div>
        <div class="data-row"><span class="label">Temperature</span><span class="value">${f.temperature_c}&deg;C</span></div>
        <div class="data-row"><span class="label">Humidity</span><span class="value">${f.humidity_pct}%</span></div>
        <div class="data-row"><span class="label">Wind Speed</span><span class="value">${f.wind_speed_kmh} km/h</span></div>
        <div class="data-row"><span class="label">Rainfall (cum.)</span><span class="value">${f.rainfall_mm} mm</span></div>
        <div class="data-row"><span class="label">Min Pressure</span><span class="value">${f.pressure_hpa} hPa</span></div>
        <div style="margin-top:8px;font-size:11px;color:var(--text-muted);">Model: Holt-Winters Exponential Smoothing</div>
    `;
}

function displayPrediction(p) {
    if (!p) return;
    const probs = p.probabilities || {};
    const sorted = Object.entries(probs).sort((a, b) => b[1] - a[1]);

    let barsHtml = "";
    const colors = {
        "Flood": "#3b82f6", "Hurricane": "#a855f7", "Heatwave": "#f97316",
        "Thunderstorm": "#f59e0b", "No Disaster": "#22c55e",
    };

    for (const [name, prob] of sorted) {
        const color = colors[name] || "#6b7280";
        barsHtml += `
            <div class="prob-bar-container">
                <div class="prob-bar-label">
                    <span>${name}</span><span>${prob.toFixed(1)}%</span>
                </div>
                <div class="prob-bar">
                    <div class="prob-bar-fill" style="width:${prob}%;background:${color};"></div>
                </div>
            </div>
        `;
    }

    document.getElementById("prediction-data").innerHTML = `
        <div style="font-size:18px;font-weight:700;color:var(--text-primary);margin-bottom:4px;">${p.predicted_disaster}</div>
        <div style="font-size:12px;color:var(--text-muted);margin-bottom:12px;">Confidence: ${p.confidence_pct}% | Model: ${p.model_type}</div>
        ${barsHtml}
    `;
}

function displayNews(news) {
    if (!news) return;
    const formatted = news.replace(/\n/g, "<br>");
    document.getElementById("news-data").innerHTML = `<div style="max-height:200px;overflow-y:auto;">${formatted}</div>`;
}

function displayAssessment(severity, department, iteration) {
    const sevBadge = document.getElementById("severity-badge");
    sevBadge.textContent = severity;
    sevBadge.className = `badge severity-badge severity-${severity}`;

    const deptBadge = document.getElementById("dept-badge");
    deptBadge.textContent = department.replace(/_/g, " ");
    deptBadge.className = "badge dept-badge";

    const iterBadge = document.getElementById("iteration-badge");
    if (iteration > 0) {
        iterBadge.textContent = `Iteration ${iteration + 1}`;
        iterBadge.style.display = "inline-block";
    } else {
        iterBadge.style.display = "none";
    }
}

function displayAlert(alertText) {
    document.getElementById("alert-content").textContent = alertText;
}

// --- Step Animation ---
async function animateSteps(stepNums) {
    for (const n of stepNums) {
        markStepActive(n);
        await sleep(300);
    }
}

function markStepActive(n) {
    const step = document.querySelector(`.step[data-step="${n}"]`);
    if (step) { step.className = "step active"; }
}

function markStepsDone(stepNums) {
    for (const n of stepNums) {
        const step = document.querySelector(`.step[data-step="${n}"]`);
        if (step) { step.className = "step done"; }
    }
}

function resetSteps() {
    document.querySelectorAll(".step").forEach(s => s.className = "step");
}

// --- Insights ---
async function loadInsights() {
    try {
        const resp = await fetch(`${API_BASE}/api/insights`);
        const data = await resp.json();
        const list = document.getElementById("insights-list");
        const count = document.getElementById("insight-count");

        count.textContent = data.count;
        list.innerHTML = "";

        if (data.insights.length === 0) {
            list.innerHTML = '<li class="empty">No insights yet. Reject an alert to trigger the self-improving loop.</li>';
        } else {
            for (const insight of data.insights) {
                const li = document.createElement("li");
                li.textContent = insight;
                list.appendChild(li);
            }
        }
    } catch (e) {
        // Silently fail if server not ready
    }
}

// --- Utility ---
function showPanel(id, inline, extraClass) {
    const el = document.getElementById(id);
    if (el) {
        el.style.display = inline ? "block" : (el.classList.contains("results-grid") ? "grid" : "block");
        if (id === "results-grid") el.style.display = "grid";
        if (extraClass) el.classList.add(extraClass);
    }
}

function hidePanel(id) {
    const el = document.getElementById(id);
    if (el) {
        el.style.display = "none";
        el.classList.remove("active");
    }
}

function showResult(type, message) {
    const banner = document.getElementById("result-banner");
    banner.style.display = "block";
    banner.className = `panel result-banner ${type}`;
    document.getElementById("result-message").textContent = message;
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// --- Init ---
document.addEventListener("DOMContentLoaded", () => {
    loadInsights();
    // Enter key triggers analysis
    document.getElementById("location-input").addEventListener("keydown", (e) => {
        if (e.key === "Enter") runPipeline();
    });
});
