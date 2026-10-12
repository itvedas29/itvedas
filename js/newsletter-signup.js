const newsletterForm = document.getElementById("newsletterForm");

newsletterForm?.addEventListener("submit", async event => {
  event.preventDefault();

  const emailInput = document.getElementById("newsletterEmail");
  const consentInput = document.getElementById("newsletterConsent");
  const status = document.getElementById("newsletterStatus");
  const submitButton = newsletterForm.querySelector('button[type="submit"]');
  if (!emailInput || !consentInput || !status || !submitButton) return;

  status.textContent = "Submitting...";
  submitButton.disabled = true;

  try {
    const response = await fetch("/api/subscribe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: emailInput.value,
        consent: consentInput.checked
      })
    });
    const result = await response.json();
    if (!response.ok || result.success !== true) {
      throw new Error(result.message || "Unable to subscribe right now.");
    }

    status.textContent = "Thank you for subscribing to ITVedas!";
    newsletterForm.reset();
  } catch (error) {
    status.textContent = error instanceof Error
      ? error.message
      : "Unable to subscribe right now. Please try again later.";
  } finally {
    submitButton.disabled = false;
  }
});
