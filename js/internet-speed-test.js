(() => {
  const DOWNLOAD_URL = 'https://speed.cloudflare.com/__down';
  const UPLOAD_URL = 'https://speed.cloudflare.com/__up';
  const DOWNLOAD_BYTES = 10_000_000;
  const UPLOAD_BYTES = 1_000_000;
  const TRIALS = 2;
  const TEST_TIMEOUT_MS = 45_000;

  const startButton = document.getElementById('start-test');
  const cancelButton = document.getElementById('cancel-test');
  const status = document.getElementById('test-status');
  const error = document.getElementById('test-error');
  const latencyResult = document.getElementById('latency-result');
  const downloadResult = document.getElementById('download-result');
  const uploadResult = document.getElementById('upload-result');
  let activeController = null;

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
    for (let i = 0; i < 3; i += 1) {
      const startedAt = performance.now();
      const response = await fetchResponse(testUrl(DOWNLOAD_URL, 0), {
        cache: 'no-store',
        mode: 'cors',
        signal
      });
      await response.arrayBuffer();
      samples.push(performance.now() - startedAt);
    }
    return samples.reduce((total, sample) => total + sample, 0) / samples.length;
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

  function formatMbps(bytes, durationMs) {
    return ((bytes * 8) / (durationMs / 1000) / 1_000_000).toFixed(1);
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
    const timeoutId = window.setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, TEST_TIMEOUT_MS);

    error.textContent = '';
    error.classList.remove('visible');
    latencyResult.textContent = '--';
    downloadResult.textContent = '--';
    uploadResult.textContent = '--';
    setBusy(true);

    try {
      status.textContent = 'Measuring latency…';
      const latency = await measureLatency(controller.signal);

      let downloadBytes = 0;
      let downloadDurationMs = 0;
      for (let i = 0; i < TRIALS; i += 1) {
        status.textContent = `Measuring download speed… (${i + 1} of ${TRIALS})`;
        const result = await measureDownload(controller.signal);
        downloadBytes += result.bytes;
        downloadDurationMs += result.durationMs;
      }

      let uploadBytes = 0;
      let uploadDurationMs = 0;
      for (let i = 0; i < TRIALS; i += 1) {
        status.textContent = `Measuring upload speed… (${i + 1} of ${TRIALS})`;
        const result = await measureUpload(controller.signal);
        uploadBytes += result.bytes;
        uploadDurationMs += result.durationMs;
      }

      latencyResult.textContent = latency.toFixed(0);
      downloadResult.textContent = formatMbps(downloadBytes, downloadDurationMs);
      uploadResult.textContent = formatMbps(uploadBytes, uploadDurationMs);
      status.textContent = 'Test complete. Results are estimates for your connection to Cloudflare.';
    } catch (testError) {
      if (controller.signal.aborted) {
        status.textContent = timedOut ? 'The test timed out. Try again when your connection is more stable.' : 'Test cancelled.';
      } else {
        status.textContent = 'The speed test could not be completed.';
        error.textContent = `${testError.message} Check your connection and allow requests to speed.cloudflare.com, then try again.`;
        error.classList.add('visible');
      }
    } finally {
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
