/**
 * Webhook Receiver for Ava Job Tracker
 * 
 * Instructions:
 * 1. In your Google Sheet, go to Extensions > Apps Script.
 * 2. Paste this code into the editor.
 * 3. Click 'Deploy' > 'New Deployment'.
 * 4. Select Type: 'Web App'.
 * 5. Execute As: 'Me'.
 * 6. Who has access: 'Anyone'. (Note: This is required for the webhook to reach the script).
 * 7. Copy the 'Web App URL' and paste it into your .env file in the ava-webhook directory.
 */

function doPost(e) {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    var payload = JSON.parse(e.postData.contents);
    var jobLink = payload.link || "";
    
    // 1. Search for existing job link in Column H (Index 8)
    var data = sheet.getDataRange().getValues();
    var existingRowIndex = -1;
    
    if (jobLink) {
      for (var i = 1; i < data.length; i++) { // Skip header
        if (data[i][7] === jobLink) { // Column H is index 7
          existingRowIndex = i + 1; // 1-based indexing for sheets
          break;
        }
      }
    }

    if (existingRowIndex !== -1) {
      // 2. Update existing row's Column I with folder_link
      if (payload.folder_link) {
        sheet.getRange(existingRowIndex, 9).setValue(payload.folder_link); // Column I is 9
      }
      return ContentService.createTextOutput(JSON.stringify({ "status": "updated", "row": existingRowIndex }))
        .setMimeType(ContentService.MimeType.JSON);
    } else {
      // 3. Append new row if not found
      var row = [
        payload.company || "",        // Column A: Company
        payload.role || payload.title, // Column B: Role
        payload.salary || "",         // Column C: Salary
        "No",                         // Column D: Applied?
        "",                           // Column E: Date Applied
        "",                           // Column F: Who did you reach out to?
        "To Apply",                   // Column G: Status
        jobLink,                      // Column H: Application Link
        payload.folder_link || ""     // Column I: Drive Folder Link
      ];
      sheet.appendRow(row);
      return ContentService.createTextOutput(JSON.stringify({ "status": "appended" }))
        .setMimeType(ContentService.MimeType.JSON);
    }
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ "status": "error", "message": err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
