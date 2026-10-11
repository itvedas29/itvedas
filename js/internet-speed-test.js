(() => {
  const DOWNLOAD_URL = 'https://speed.cloudflare.com/__down';
  const UPLOAD_URL = 'https://speed.cloudflare.com/__up';
  const DOWNLOAD_BYTES = 10_000_000;
  const UPLOAD_BYTES = 2_000_000;
  const TRIALS = 5;
  const TEST_TIMEOUT_MS = 180_000;

  const startButton = document.getElementById('start-test');
  const cancelButton = document.getElementById('cancel-test');
  const status = document.getElementById('test-status');
  const error = document.getElementById('test-error');
  const visual = document.getElementById('test-visual');
  const phaseLabel = document.getElementById('test-phase');
  const elapsedLabel = document.getElementById('test-elapsed');
  const phaseSteps = Array.from(document.querySelectorAll('[data-phase]'));
  const latencyResult = document.getElementById('latency-result');
  const downloadResult = document.getElementById('download-result');
  const uploadResult = document.getElementById('upload-result');
  let activeController = null;
  const phases = ['latency', 'download', 'upload'];

  function testUrl(endpoint, bytes) {
    const params = new URLSearchParams({ bytes: String(bytes), cache: String(Date.now() + Math.random()) });
    return `${endpoint}?${params}`;
  }

  async function fetchResponse(url, options) {
    const response = await fetch(url, options);
    if (!response.ok) {
      throw new Error(`Speed-test server returned HTTP ${response.status}.`);
    }
    return response;
  }

  async function measureLatency(signal) {
    const samples = [];
    for (let i = 0; i < TRIALS; i += 1) {
      setPhase('latency', `Measuring latency… (${i + 1} of ${TRIALS})`);
      const startedAt = performance.now();
      const response = await fetchResponse(testUrl(DOWNLOAD_URL, 0), {
        cache: 'no-store',
        mode: 'cors',
        signal
      });
      await response.arrayBuffer();
      samples.push(performance.now() - startedAt);
    }
    return median(samples);
  }

  async function measureDownload(signal) {
    const startedAt = performance.now();
    const response = await fetchResponse(testUrl(DOWNLOAD_URL, DOWNLOAD_BYTES), {
      cache: 'no-store',
      mode: 'cors',
      signal
    });

    let bytesReceived = 0;
    if (response.body) {
      const reader = response.body.getReader();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        bytesReceived += value.byteLength;
      }
    } else {
      bytesReceived = (await response.arrayBuffer()).byteLength;
    }

    const durationMs = performance.now() - startedAt;
    if (bytesReceived === 0 || durationMs <= 0) {
      throw new Error('The download test did not receive any data.');
    }
    return { bytes: bytesReceived, durationMs };
  }

  async function measureUpload(signal) {
    const payload = new Uint8Array(UPLOAD_BYTES);
    const startedAt = performance.now();
    const response = await fetchResponse(UPLOAD_URL, {
      method: 'POST',
      body: payload,
      cache: 'no-store',
      mode: 'cors',
      signal
    });
    await response.arrayBuffer();

    const durationMs = performance.now() - startedAt;
    if (durationMs <= 0) {
      throw new Error('The upload test did not complete successfully.');
    }
    return { bytes: payload.byteLength, durationMs };
  }

  function speedMbps(bytes, durationMs) {
    return (bytes * 8) / (durationMs * 1000);
  }

  function median(values) {
    const sorted = [...values].sort((a, b) => a - b);
    const middle = Math.floor(sorted.length / 2);
    return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
  }

  function formatElapsed(durationMs) {
    const totalSeconds = Math.floor(durationMs / 1000);
    const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, '0');
    const seconds = String(totalSeconds % 60).padStart(2, '0');
    return `${minutes}:${seconds}`;
  }

  function setPhase(phase, message) {
    const activeIndex = phases.indexOf(phase);
    visual.classList.add('is-running');
    phaseLabel.textContent = phase.toUpperCase();
    status.textContent = message;
    phaseSteps.forEach((step, index) => {
      step.classList.toggle('is-active', index === activeIndex);
      step.classList.toggle('is-complete', index < activeIndex);
      if (index === activeIndex) step.setAttribute('aria-current', 'step');
      else step.removeAttribute('aria-current');
    });
  }

  function finishProgress(label, completed = false) {
    visual.classList.remove('is-running');
    phaseLabel.textContent = label;
    phaseSteps.forEach(step => {
      step.classList.remove('is-active');
      step.classList.toggle('is-complete', completed);
      step.removeAttribute('aria-current');
    });
  }

  function setBusy(isBusy) {
    startButton.disabled = isBusy;
    cancelButton.hidden = !isBusy;
  }

  async function runTest() {
    if (!navigator.onLine) {
      error.textContent = 'Your browser reports that it is offline. Reconnect and try again.';
      error.classList.add('visible');
      return;
    }

    const controller = new AbortController();
    activeController = controller;
    let timedOut = false;
    const startedAt = performance.now();
    elapsedLabel.textContent = '00:00';
    const elapsedInterval = window.setInterval(() => {
      elapsedLabel.textContent = formatElapsed(performance.now() - startedAt);
    }, 1000);
    const timeoutId = window.setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, TEST_TIMEOUT_MS);

    error.textContent = '';
    error.classList.remove('visible');
    latencyResult.textContent = '--';
    downloadResult.textContent = '--';
    uploadResult.textContent = '--';
    finishProgress('READY');
    setBusy(true);

    try {
      const latency = await measureLatency(controller.signal);

      const downloadSamples = [];
      for (let i = 0; i < TRIALS; i += 1) {
        setPhase('download', `Measuring download speed… (${i + 1} of ${TRIALS})`);
        const result = await measureDownload(controller.signal);
        downloadSamples.push(speedMbps(result.bytes, result.durationMs));
      }

      const uploadSamples = [];
      for (let i = 0; i < TRIALS; i += 1) {
        setPhase('upload', `Measuring upload speed… (${i + 1} of ${TRIALS})`);
        const result = await measureUpload(controller.signal);
        uploadSamples.push(speedMbps(result.bytes, result.durationMs));
      }

      latencyResult.textContent = latency.toFixed(0);
      downloadResult.textContent = median(downloadSamples).toFixed(1);
      uploadResult.textContent = median(uploadSamples).toFixed(1);
      finishProgress('DONE', true);
      status.textContent = 'Test complete. Results are estimates for your connection to Cloudflare.';
    } catch (testError) {
      if (controller.signal.aborted) {
        finishProgress(timedOut ? 'TIMEOUT' : 'CANCELLED');
        status.textContent = timedOut ? 'The test timed out. Try again when your connection is more stable.' : 'Test cancelled.';
      } else {
        finishProgress('ERROR');
        status.textContent = 'The speed test could not be completed.';
        error.textContent = `${testError.message} Check your connection and allow requests to speed.cloudflare.com, then try again.`;
        error.classList.add('visible');
      }
    } finally {
      elapsedLabel.textContent = formatElapsed(performance.now() - startedAt);
      window.clearInterval(elapsedInterval);
      window.clearTimeout(timeoutId);
      if (activeController === controller) activeController = null;
      setBusy(false);
    }
  }

  startButton.addEventListener('click', runTest);
  cancelButton.addEventListener('click', () => {
    if (activeController) {
      activeController.abort();
    }
  });
})();
