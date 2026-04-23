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
    var company = payload.company || "";
    var role = payload.role || payload.title || "";
    
    var data = sheet.getDataRange().getValues();
    var existingRowIndex = -1;
    
    // 1. Search for existing job link in Column H (Index 7)
    if (jobLink) {
      for (var i = 1; i < data.length; i++) { // Skip header
        if (data[i][7] === jobLink) { 
          existingRowIndex = i + 1;
          break;
        }
      }
    }

    // 2. Fallback: Search by Company (Col A) AND Role (Col B) if no link match
    if (existingRowIndex === -1 && company && role) {
      var normCompany = company.toLowerCase().replace(/\s+/g, '');
      var normRole = role.toLowerCase().replace(/\s+/g, '');
      
      for (var i = 1; i < data.length; i++) {
        var rowCompany = (data[i][0] || "").toString().toLowerCase().replace(/\s+/g, '');
        var rowRole = (data[i][1] || "").toString().toLowerCase().replace(/\s+/g, '');
        
        if (rowCompany === normCompany && rowRole === normRole) {
          existingRowIndex = i + 1;
          break;
        }
      }
    }

    if (existingRowIndex !== -1) {
      // 3. Update existing row's Column I with folder_link if provided
      if (payload.folder_link) {
        sheet.getRange(existingRowIndex, 9).setValue(payload.folder_link); 
      }
      // Also update the link if it was missing or different
      if (jobLink && !data[existingRowIndex-1][7]) {
        sheet.getRange(existingRowIndex, 8).setValue(jobLink);
      }
      
      return ContentService.createTextOutput(JSON.stringify({ "status": "updated", "row": existingRowIndex }))
        .setMimeType(ContentService.MimeType.JSON);
    } else {
      // 4. Append new row if not found
      var row = [
        company,                      // Column A: Company
        role,                         // Column B: Role
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
