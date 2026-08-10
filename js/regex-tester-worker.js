// js/regex-tester-worker.js
//
// Runs regex matching off the main thread so a catastrophic-backtracking
// pattern can never freeze the page. tools/regex-tester.html also races
// this worker against a timeout and terminates it if it doesn't respond —
// that's the actual ReDoS defense; this file just does the matching.

self.onmessage = function (e) {
  const { pattern, flags, testString, replacement } = e.data;

  let re;
  try {
    re = new RegExp(pattern, flags.includes('g') ? flags : flags + 'g');
  } catch (err) {
    self.postMessage({ error: err.message });
    return;
  }

  const matches = [];
  let match;
  let lastIndex = -1;
  const MAX_MATCHES = 1000;

  while ((match = re.exec(testString)) !== null && matches.length < MAX_MATCHES) {
    matches.push({
      match: match[0],
      index: match.index,
      groups: match.slice(1),
      namedGroups: match.groups || null
    });
    // Guard against zero-length matches causing an infinite loop
    if (match.index === lastIndex) {
      re.lastIndex++;
    }
    lastIndex = match.index;
    if (!re.global) break;
  }

  let replaced = null;
  if (typeof replacement === 'string') {
    try {
      const replaceRe = new RegExp(pattern, flags.includes('g') ? flags : flags + 'g');
      replaced = testString.replace(replaceRe, replacement);
    } catch (err) {
      replaced = null;
    }
  }

  self.postMessage({ matches, truncated: matches.length >= MAX_MATCHES, replaced });
};
