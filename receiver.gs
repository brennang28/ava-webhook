/**
 * Ava Job Tracker Webhook Receiver (Updated for Hyperlinked Companies)
 * 
 * Instructions:
 * 1. In your Google Sheet, go to Extensions > Apps Script.
 * 2. Paste this code into the editor.
 * 3. Click 'Deploy' > 'New Deployment'.
 * 4. Select Type: 'Web App'.
 * 5. Execute As: 'Me'.
 * 6. Who has access: 'Anyone'.
 * 7. Click 'Deploy'. 
 * 8. IMPORTANT: Copy the 'Web App URL' and ensure it matches WEBHOOK_URL in .env.
 * 
 * Column Mapping (8 Columns):
 * A: Company (Hyperlinked)
 * B: Role
 * C: Salary
 * D: Applied?
 * E: Date Applied
 * F: Who did you reach out to?
 * G: Status
 * H: AI Generated Application Materials (Folder Link)
 */

function doPost(e) {
  try {
    var payload = JSON.parse(e.postData.contents);
    
    // LOGGING: Check your Apps Script "Executions" tab to see this output
    console.log("Received Webhook Payload:", JSON.stringify(payload, null, 2));
    
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    var jobLink = payload.link || "";
    var company = payload.company || "Unknown";
    var role = payload.role || payload.title || "Position";
    
    // Escape double quotes for Google Sheets formula
    var escapedCompany = company.replace(/"/g, '""');
    
    // 1. Search for existing entry to avoid duplicates (Company + Role)
    var data = sheet.getDataRange().getValues();
    var existingRowIndex = -1;
    
    if (company && role) {
      var normCompany = company.toLowerCase().replace(/\s+/g, '');
      var normRole = role.toLowerCase().replace(/\s+/g, '');
      
      for (var i = 1; i < data.length; i++) {
        var rowValA = (data[i][0] || "").toString();
        var rowCompanyText = rowValA;
        
        // Handle existing hyperlinked cells (extract plain text for comparison)
        if (rowValA.startsWith("=HYPERLINK")) {
          var match = rowValA.match(/",\s*"([^"]+)"\)/);
          if (match) rowCompanyText = match[1];
        }
        
        var rowCompany = rowCompanyText.toLowerCase().replace(/\s+/g, '');
        var rowRole = (data[i][1] || "").toString().toLowerCase().replace(/\s+/g, '');
        
        if (rowCompany === normCompany && rowRole === normRole) {
          existingRowIndex = i + 1;
          break;
        }
      }
    }

    if (existingRowIndex !== -1) {
      // 2. Update existing row's Column H (Column 8) with folder_link if provided
      if (payload.folder_link) {
        sheet.getRange(existingRowIndex, 8).setValue(payload.folder_link); 
      }
      return ContentService.createTextOutput(JSON.stringify({ "status": "updated", "row": existingRowIndex }))
        .setMimeType(ContentService.MimeType.JSON);
    } else {
      // 3. Append new row with Hyperlinked Company in Column A
      var row = [
        "=HYPERLINK(\"" + jobLink + "\", \"" + escapedCompany + "\")", // A: Company
        role,                         // B: Role
        payload.salary || "",         // C: Salary
        "No",                         // D: Applied?
        "",                           // E: Date Applied
        "",                           // F: Who did you reach out to?
        "To Apply",                   // G: Status
        payload.folder_link || ""     // H: Drive Folder Link
      ];
      
      sheet.appendRow(row);
      return ContentService.createTextOutput(JSON.stringify({ "status": "appended" }))
        .setMimeType(ContentService.MimeType.JSON);
    }
  } catch (err) {
    console.error("Webhook Error:", err.toString());
    return ContentService.createTextOutput(JSON.stringify({ "status": "error", "message": err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
