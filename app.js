const form = document.querySelector("#garden-form");
const submitButton = document.querySelector("#submit-button");
const statusBox = document.querySelector("#status");
const resultBox = document.querySelector("#result");

function showStatus(message, isError = false) {
  statusBox.textContent = message;
  statusBox.classList.toggle("error", isError);
  statusBox.hidden = false;
}

function addTextElement(parent, tagName, className, text) {
  const element = document.createElement(tagName);
  element.className = className;
  element.textContent = text;
  parent.append(element);
  return element;
}

function renderPlan(plan) {
  resultBox.replaceChildren();
  addTextElement(resultBox, "div", "result-topline", "Your garden field note");
  addTextElement(resultBox, "h2", "", plan.headline);
  addTextElement(resultBox, "p", "planting-window", plan.planting_window);

  const activities = document.createElement("ol");
  activities.className = "activity-list";
  for (const item of plan.outdoor_plan) {
    const activity = document.createElement("li");
    activity.className = "activity";
    addTextElement(activity, "span", "activity-time", `${item.duration_minutes} MIN`);
    const description = document.createElement("div");
    addTextElement(description, "h3", "", item.title);
    addTextElement(description, "p", "", item.instructions);
    activity.append(description);
    activities.append(activity);
  }
  resultBox.append(activities);
  addTextElement(resultBox, "p", "result-note", plan.notes);
  resultBox.hidden = false;
  resultBox.scrollIntoView({ behavior: "smooth", block: "start" });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  statusBox.hidden = true;
  resultBox.hidden = true;
  submitButton.disabled = true;
  submitButton.textContent = "Planning with your local model…";

  const formData = new FormData(form);
  const payload = {
    location: formData.get("location").trim(),
    last_frost_date: formData.get("last_frost_date"),
    plants: formData.get("plants").trim(),
  };

  try {
    const response = await fetch("/api/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || `The local planner returned HTTP ${response.status}.`);
    }
    renderPlan(data);
  } catch (error) {
    showStatus(error.message || "Could not reach the local planner. Check that the app and Ollama are running.", true);
  } finally {
    submitButton.disabled = false;
    submitButton.innerHTML = 'Plan my outside time <span aria-hidden="true">↗</span>';
  }
});
