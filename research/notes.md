# Webhook to Google Sheets Technical Research

## Workflow Overview
The objective is to create a "Job Application Pipeline" that automatically populates a Google Sheet with job links for quick application.

### 1. Webhook Receiver (The Sink)
**Technology:** Google Apps Script (GAS)
- **Why:** Free, hosted by Google, native access to Google Sheets, zero infrastructure management.
- **Implementation:** 
  - Deploy a `doPost(e)` function as a Web App.
  - Set "Execute as: Me" and "Access: Anyone".
  - Script logic: Parse JSON payload and use `sheet.appendRow()`.

### 2. Event Trigger (The Source)
**Option A: Automated Scraper (Fastest)**
- **Tool:** Python with `python-jobspy`.
- **Logic:** Periodically search LinkedIn/Indeed, filter for new jobs, and `POST` to the GAS URL.
- **Deployment:** Local cron job or a tiny GitHub Action.

**Option B: Manual "Clipper" (Most Precise)**
- **Tool:** Chrome Extension or Bookmarklet.
- **Logic:** User browsing job boards clicks "Save to Ava". Extension grabs URL/Title and sends to Webhook.

**Option C: Low-Code Integration**
- **Tools:** Zapier or Make.com.
- **Logic:** Connects existing RSS feeds or email alerts to Google Sheets.

### 3. Data Schema
Recommended headers for the Google Sheet:
1. Date Captured
2. Job Title
3. Company
4. Link (Clickable)
5. Status (Applied/Interested/Rejected)
6. Notes

## Technical Constraints & Security
- **Security:** Since GAS Web Apps for "Anyone" are public, we should include a `secret_token` in the webhook payload and verify it in the script.
- **Rate Limits:** Google Apps Script has quotas (approx. 20k-90k executions/day), which is more than enough for job hunting.
- **Blocking:** Job boards (LinkedIn) block scrapers. Using `jobspy` with proxies or a browser-based Clipper is safer.
