const SPREADSHEET_ID = "17jo4PX9f0vIn5u9R4f23vcE6Z6148M8CW9KVzLmWCs4";
const QUIZ_LEVELS = ["beginner", "intermediate", "advanced"];

function doPost(event) {
  const properties = PropertiesService.getScriptProperties();
  const expectedSecret = properties.getProperty("NEWSLETTER_WEBHOOK_SECRET");
  if (!expectedSecret) {
    console.error("Newsletter webhook secret is not configured.");
    return jsonOutput({ success: false, code: "not_configured" });
  }

  let payload;
  try {
    payload = JSON.parse(event.postData.contents);
  } catch (error) {
    return jsonOutput({ success: false, code: "invalid_request" });
  }

  if (!payload || payload.secret !== expectedSecret) {
    return jsonOutput({ success: false, code: "unauthorized" });
  }

  if (payload.type === "quiz_start") {
    return appendQuizStart(payload);
  }
  if (payload.type === "quiz") {
    return appendQuizResult(payload);
  }

  return appendNewsletterSignup(payload);
}

function appendNewsletterSignup(payload) {
  const email = typeof payload.email === "string" ? payload.email.trim().toLowerCase() : "";
  if (email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return jsonOutput({ success: false, code: "invalid_email" });
  }

  const lock = LockService.getScriptLock();
  if (!lock.tryLock(10000)) {
    return jsonOutput({ success: false, code: "temporarily_unavailable" });
  }

  try {
    const spreadsheet = SpreadsheetApp.openById(SPREADSHEET_ID);
    const sheet = getOrCreateSheet(spreadsheet, "Newsletter Subscribers",
      ["Subscribed at (UTC)", "Email", "Source", "Consent", "Status"]);

    const lastRow = sheet.getLastRow();
    if (lastRow > 1) {
      const matches = sheet
        .getRange(2, 2, lastRow - 1, 1)
        .createTextFinder(email)
        .matchCase(false)
        .matchEntireCell(true)
        .findNext();
      if (matches) {
        return jsonOutput({ success: false, code: "already_subscribed" });
      }
    }

    sheet.getRange("B:B").setNumberFormat("@");
    sheet.appendRow([new Date().toISOString(), email, "homepage-newsletter", "yes", "subscribed"]);
    return jsonOutput({ success: true });
  } catch (error) {
    console.error("Newsletter sheet write failed: " + error);
    return jsonOutput({ success: false, code: "write_failed" });
  } finally {
    lock.releaseLock();
  }
}

function appendQuizStart(payload) {
  const name = typeof payload.name === "string" ? payload.name.trim() : "";
  const email = typeof payload.email === "string" ? payload.email.trim().toLowerCase() : "";
  if (!name || name.length > 100) {
    return jsonOutput({ success: false, code: "invalid_name" });
  }
  if (email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return jsonOutput({ success: false, code: "invalid_email" });
  }

  const lock = LockService.getScriptLock();
  if (!lock.tryLock(10000)) {
    return jsonOutput({ success: false, code: "temporarily_unavailable" });
  }

  try {
    const spreadsheet = SpreadsheetApp.openById(SPREADSHEET_ID);
    const sheet = getOrCreateSheet(spreadsheet, "Quiz Participants",
      ["Started at (UTC)", "Name", "Email", "Consent"]);
    sheet.getRange("C:C").setNumberFormat("@");
    sheet.appendRow([new Date().toISOString(), sheetText(name), email, "yes"]);
    return jsonOutput({ success: true });
  } catch (error) {
    console.error("Quiz start write failed: " + error);
    return jsonOutput({ success: false, code: "write_failed" });
  } finally {
    lock.releaseLock();
  }
}

function appendQuizResult(payload) {
  const name = typeof payload.name === "string" ? payload.name.trim() : "";
  const email = typeof payload.email === "string" ? payload.email.trim().toLowerCase() : "";
  const level = typeof payload.level === "string" ? payload.level : "";
  const score = Number(payload.score);
  const topics = typeof payload.topics === "string" ? payload.topics.slice(0, 1000) : "";

  if (!name || name.length > 100) {
    return jsonOutput({ success: false, code: "invalid_name" });
  }
  if (email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return jsonOutput({ success: false, code: "invalid_email" });
  }
  if (QUIZ_LEVELS.indexOf(level) === -1 || !Number.isInteger(score) || score < 0 || score > 10) {
    return jsonOutput({ success: false, code: "invalid_result" });
  }

  const lock = LockService.getScriptLock();
  if (!lock.tryLock(10000)) {
    return jsonOutput({ success: false, code: "temporarily_unavailable" });
  }

  try {
    const spreadsheet = SpreadsheetApp.openById(SPREADSHEET_ID);
    const sheet = getOrCreateSheet(spreadsheet, "Quiz Results",
      ["Submitted at (UTC)", "Name", "Email", "Level", "Score", "Topic breakdown", "Consent"]);
    sheet.getRange("C:C").setNumberFormat("@");
    sheet.appendRow([new Date().toISOString(), sheetText(name), email, level, score, sheetText(topics), "yes"]);
    return jsonOutput({ success: true });
  } catch (error) {
    console.error("Quiz sheet write failed: " + error);
    return jsonOutput({ success: false, code: "write_failed" });
  } finally {
    lock.releaseLock();
  }
}

// appendRow treats text starting with = + - @ (or a tab/CR) as a formula. A leading
// apostrophe makes Sheets store visitor-supplied text literally.
function sheetText(value) {
  return /^[=+\-@\t\r]/.test(value) ? "'" + value : value;
}

function getOrCreateSheet(spreadsheet, name, headers) {
  let sheet = spreadsheet.getSheetByName(name);
  if (!sheet) {
    sheet = spreadsheet.insertSheet(name);
  }
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(headers);
  }
  return sheet;
}

function jsonOutput(value) {
  return ContentService
    .createTextOutput(JSON.stringify(value))
    .setMimeType(ContentService.MimeType.JSON);
}
