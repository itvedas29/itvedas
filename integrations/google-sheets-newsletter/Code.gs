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

  if (payload.type === "quiz") {
    return appendQuizResult(payload);
  }

  const email = typeof payload.email === "string" ? payload.email.trim().toLowerCase() : "";
  if (email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return jsonOutput({ success: false, code: "invalid_email" });
  }

  const lock = LockService.getScriptLock();
  if (!lock.tryLock(10000)) {
    return jsonOutput({ success: false, code: "temporarily_unavailable" });
  }

  try {
    const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    if (!spreadsheet) {
      console.error("Newsletter spreadsheet is unavailable.");
      return jsonOutput({ success: false, code: "not_configured" });
    }

    let sheet = spreadsheet.getSheetByName("Newsletter Subscribers");
    if (!sheet) {
      sheet = spreadsheet.insertSheet("Newsletter Subscribers");
    }
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(["Subscribed at (UTC)", "Email", "Source", "Consent", "Status"]);
    }

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
    sheet.appendRow([
      new Date().toISOString(),
      email,
      "homepage-newsletter",
      "yes",
      "subscribed"
    ]);
    return jsonOutput({ success: true });
  } catch (error) {
    console.error("Newsletter sheet write failed: " + error);
    return jsonOutput({ success: false, code: "write_failed" });
  } finally {
    lock.releaseLock();
  }
}

const QUIZ_LEVELS = ["beginner", "intermediate", "advanced"];

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
    const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    if (!spreadsheet) {
      console.error("Quiz spreadsheet is unavailable.");
      return jsonOutput({ success: false, code: "not_configured" });
    }
    let sheet = spreadsheet.getSheetByName("Quiz Participants");
    if (!sheet) {
      sheet = spreadsheet.insertSheet("Quiz Participants");
    }
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(["Submitted at (UTC)", "Name", "Email", "Level", "Score", "Topic breakdown", "Consent"]);
    }
    sheet.getRange("C:C").setNumberFormat("@");
    sheet.appendRow([new Date().toISOString(), name, email, level, score, topics, "yes"]);
    return jsonOutput({ success: true });
  } catch (error) {
    console.error("Quiz sheet write failed: " + error);
    return jsonOutput({ success: false, code: "write_failed" });
  } finally {
    lock.releaseLock();
  }
}

function jsonOutput(value) {
  return ContentService
    .createTextOutput(JSON.stringify(value))
    .setMimeType(ContentService.MimeType.JSON);
}
