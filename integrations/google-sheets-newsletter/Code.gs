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

function jsonOutput(value) {
  return ContentService
    .createTextOutput(JSON.stringify(value))
    .setMimeType(ContentService.MimeType.JSON);
}
