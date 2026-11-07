const form = document.querySelector("#chat-form");
const messageField = document.querySelector("#message");
const temperatureField = document.querySelector("#temperature");
const submitButton = document.querySelector("#submit-button");
const spinner = document.querySelector("#spinner");
const statusRegion = document.querySelector("#status");
const answerRegion = document.querySelector("#answer");
const requestIdRegion = document.querySelector("#request-id");

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  submitButton.disabled = true;
  spinner.hidden = false;
  statusRegion.textContent = "Waiting for the server…";
  answerRegion.textContent = "";
  requestIdRegion.hidden = true;
  requestIdRegion.textContent = "";

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: messageField.value,
        temperature: Number(temperatureField.value),
      }),
    });

    const data = await response.json().catch(() => null);
    if (!response.ok) {
      statusRegion.textContent = data?.detail?.error || `Request failed (${response.status}). Try again.`;
      showRequestId(data?.request_id || data?.detail?.request_id);
      return;
    }

    if (
      !data
      || typeof data !== "object"
      || typeof data.response !== "string"
      || !data.response.trim()
    ) {
      statusRegion.textContent = "The server returned an invalid response. Try again.";
      showRequestId(data?.request_id);
      return;
    }

    answerRegion.textContent = data.response;
    statusRegion.textContent = "Answer received.";
    showRequestId(data.request_id);
  } catch (error) {
    statusRegion.textContent = error instanceof TypeError
      ? "Network error. Check that the backend is running, then try again."
      : error.message;
  } finally {
    submitButton.disabled = false;
    spinner.hidden = true;
  }
});

function showRequestId(requestId) {
  if (!requestId) return;
  requestIdRegion.textContent = `Request ID: ${requestId}`;
  requestIdRegion.hidden = false;
}
