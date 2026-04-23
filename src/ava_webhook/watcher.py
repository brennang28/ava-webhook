import os
import sqlite3
import json
import logging
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from jobspy import scrape_jobs
from .scout import AvaScout
from .generator import AvaGenerator
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, urlunparse


# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

class AvaWatcher:
    def __init__(self, config_path="config.json", db_path="jobs.db"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        self.db_path = db_path
        self.session_seen = set()
        self.applied_history_set = self._load_applied_history()
        self.playwright = None
        self.browser = None
        self._init_db()

    def _get_browser(self):
        if not self.browser:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=True)
        return self.browser

    def close(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def _load_applied_history(self):
        """Loads and normalizes applied_history.json for early filtering."""
        history_path = "research/data/applied_history.json"

        history_set = set()
        if os.path.exists(history_path):
            try:
                with open(history_path, 'r') as f:
                    data = json.load(f)
                    if "values" in data:
                        rows = data["values"]
                        if len(rows) > 0:
                            header = rows[0]
                            co_idx = header.index("Company") if "Company" in header else -1
                            ro_idx = header.index("Role") if "Role" in header else -1
                            
                            if co_idx != -1 and ro_idx != -1:
                                for row in rows[1:]:
                                    if len(row) > max(co_idx, ro_idx):
                                        comp = "".join(row[co_idx].lower().split())
                                        role = "".join(row[ro_idx].lower().split())
                                        history_set.add((comp, role))
            except Exception as e:
                logger.error(f"Error loading applied history in watcher: {e}")
        return history_set

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS jobs 
                           (job_id TEXT PRIMARY KEY, title TEXT, company TEXT, date_found TIMESTAMP)''')

    def _normalize_url(self, url):
        """Strips tracking parameters from job URLs."""
        if not url or not isinstance(url, str):
            return url
        try:
            parsed = urlparse(url)
            # Only keep the scheme, netloc, and path
            return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
        except Exception as e:
            logger.warning(f"Failed to normalize URL {url}: {e}")
            return url

    def is_new(self, job_id, title=None, company=None):
        """Checks if a job is new by ID or by Company/Role combination."""
        norm_id = self._normalize_url(job_id)
        if norm_id in self.session_seen:
            return False
            
        with sqlite3.connect(self.db_path) as conn:
            # 1. Check by normalized ID
            cursor = conn.execute("SELECT 1 FROM jobs WHERE job_id = ?", (norm_id,))
            if cursor.fetchone():
                return False
                
            # 2. Check by Company/Role collision if provided
            if title and company:
                cursor = conn.execute("SELECT 1 FROM jobs WHERE title = ? AND company = ?", (title, company))
                if cursor.fetchone():
                    logger.debug(f"Duplicate by Company/Role: {title} @ {company}")
                    return False
                    
        return True


    def save_job(self, job_id, title, company):
        norm_id = self._normalize_url(job_id)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO jobs (job_id, title, company, date_found) VALUES (?, ?, ?, ?)",
                         (norm_id, title, company, datetime.now()))


    def dispatch(self, job):
        if not WEBHOOK_URL or "script.google.com" not in WEBHOOK_URL:
            logger.warning("WEBHOOK_URL not set or invalid. Skipping dispatch.")
            return

        try:
            # Resiliency: Ensure job is a dict (handles pandas.Series if leaked into pool)
            if hasattr(job, 'to_dict'):
                job_data = job.to_dict()
            elif isinstance(job, dict):
                job_data = job.copy()
            else:
                job_data = dict(job)

            # Map common keys to expected webhook schema
            role = job_data.get('role') or job_data.get('title') or job_data.get('job_title') or 'Position'
            company = job_data.get('company') or job_data.get('company_name') or 'Unknown'
            
            # Finalize payload
            payload = job_data
            payload['role'] = role
            payload['company'] = company

            response = requests.post(WEBHOOK_URL, json=payload, timeout=15)
            if response.status_code == 200:
                logger.info(f"Dispatched: {role} @ {company}")
            else:
                logger.error(f"Failed to dispatch (HTTP {response.status_code}): {response.text}")
        except Exception as e:
            logger.error(f"Error sending webhook for {job.get('company', 'Unknown')}: {e}", exc_info=True)

    def scrape_general(self):
        logger.info("Starting general job board scrape (LinkedIn/Indeed)...")
        filters = self.config['filters']
        max_age_hours = filters.get('max_age_days', 14) * 24
        all_found = []
        
        for title in filters['titles']:
            try:
                jobs = scrape_jobs(
                    site_name=["linkedin", "indeed"],
                    search_term=title,
                    location=filters['location'],
                    results_wanted=15,
                    hours_old=max_age_hours,
                )
                
                for _, row in jobs.iterrows():
                    raw_url = row['job_url']
                    company = row['company'] if str(row['company']) != 'nan' else 'Unknown'
                    title_val = row['title'] if str(row['title']) != 'nan' else 'Position'
                    salary = row['salary_source'] if str(row['salary_source']) != 'nan' else ''
                    
                    if self.is_new(raw_url, title_val, company):
                        norm_id = self._normalize_url(raw_url)
                        self.session_seen.add(norm_id)


                        if self._should_process_job(title_val, company) and self._verify_link(raw_url, company):
                            all_found.append({
                                "company": company,
                                "role": title_val,
                                "salary": salary,
                                "link": norm_id
                            })

                        elif not self._should_process_job(title_val, company):
                            logger.debug(f"Filtered role: {title_val}")
                        else:
                            logger.warning(f"Unverified link skipped: {job_id}")
            except Exception as e:
                logger.error(f"Error scraping {title}: {e}")
        return all_found

    def scrape_playbill(self):
        logger.info("Starting Playbill scrape...")
        url = "https://playbill.com/jobs"
        all_found = []
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Each job is inside an <a> tag with href containing '/job/'
            job_listings = soup.select('a[href*="/job/"]')
            
            for listing in job_listings:
                title_elem = listing.select_one('div.pb-tile-title')
                company_elem = listing.select_one('div.pb-tile-location')
                category_elem = listing.select_one('div.pb-tile-category')
                
                if not title_elem or not company_elem:
                    continue

                title = title_elem.get_text(separator=" ").strip()
                company = company_elem.get_text(separator="|").split('|')[0].strip()
                category = category_elem.get_text().strip() if category_elem else ""
                link = "https://playbill.com" + listing['href']
                
                config_pb = self.config['sources']['playbill']
                is_target_cat = any(cat.lower() in category.lower() for cat in config_pb['categories'])
                matches_kw = any(kw.lower() in title.lower() for kw in config_pb['keywords'])
                
                location_text = company_elem.get_text(separator=" ").strip()
                is_target_loc = self._is_target_location(location_text)

                if (is_target_cat or matches_kw) and is_target_loc and self.is_new(link, title, company):
                    if not self._should_process_job(title, company):
                        continue
                    if not self._verify_link(link, company):
                        logger.warning(f"Skipping unverified Playbill link: {link}")
                        continue
                    norm_link = self._normalize_url(link)
                    self.session_seen.add(norm_link)
                    all_found.append({"company": company, "role": title, "link": norm_link})

        except Exception as e:
            logger.error(f"Error scraping Playbill: {e}")
        return all_found

    def scrape_favorites(self):
        logger.info("Checking favorite companies...")
        all_found = []
        for comp in self.config['favorite_companies']:
            try:
                if comp['ats'] == 'greenhouse':
                    all_found.extend(self._check_greenhouse(comp))
                elif comp['ats'] == 'lever':
                    all_found.extend(self._check_lever(comp))
                else:
                    logger.warning(f"Unsupported ATS type '{comp.get('ats')}' for {comp['name']}")
            except Exception as e:
                logger.error(f"Failed processing {comp.get('name', 'Unknown')}: {e}")
        return all_found

    def _check_greenhouse(self, company):
        url = f"https://boards-api.greenhouse.io/v1/boards/{company['slug']}/jobs"
        try:
            response = requests.get(url, timeout=10).json()
        except Exception as e:
            logger.error(f"Failed to fetch Greenhouse for {company['name']}: {e}")
            return []
            
        found = []
        if isinstance(response, dict) and 'jobs' in response:
            for job in response['jobs']:
                title = job.get('title', '')
                location = job.get('location', {}).get('name', '')
                posted = job.get('updated_at', '')
                
                if (self._should_process_job(title, company['name']) 
                    and self._is_target_location(location) 
                    and self._is_recent(posted)
                    and self.is_new(str(job['id']), title, company['name'])
                    and self._verify_link(job['absolute_url'], company['name'])):
                    norm_url = self._normalize_url(job['absolute_url'])
                    found.append({
                        "id": str(job['id']),
                        "company": company['name'],
                        "role": title,
                        "link": norm_url
                    })

        return found

    def _check_lever(self, company):
        url = f"https://api.lever.co/v0/postings/{company['slug']}?group=team&scope=published"
        try:
            response = requests.get(url, timeout=10).json()
        except Exception as e:
            logger.error(f"Failed to fetch Lever for {company['name']}: {e}")
            return []

        found = []
        if not isinstance(response, list):
            logger.warning(f"Unexpected Lever response for {company['name']}: {response}")
            return []

        for job in response:
            title = job.get('text', '')
            location = job.get('categories', {}).get('location', '')
            # Lever uses millisecond epoch timestamps
            created_ms = job.get('createdAt', 0)
            posted = datetime.fromtimestamp(created_ms / 1000).isoformat() if created_ms else ''
            
            if (self._should_process_job(title, company['name']) 
                and self._is_target_location(location) 
                and self._is_recent(posted)
                and self.is_new(job['id'], title, company['name'])
                and self._verify_link(job['hostedUrl'], company['name'])):
                norm_url = self._normalize_url(job['hostedUrl'])
                found.append({
                    "id": job['id'],
                    "company": company['name'],
                    "role": title,
                    "link": norm_url
                })

        return found

    def _should_process_job(self, title, company=""):
        # 1. Check for manual exclusions (Blocklist)
        exclusions = self.config.get('exclusions', {})
        
        # Check blocked companies
        if company:
            blocked_cos = exclusions.get('blocked_companies', [])
            if any(bc.lower() in company.lower() for bc in blocked_cos):
                logger.info(f"Skipping blocked company: {company}")
                return False
                
        # Check blocked keywords in title
        blocked_kws = exclusions.get('blocked_keywords', [])
        if any(bk.lower() in title.lower() for bk in blocked_kws):
            logger.info(f"Skipping blocked keyword in role: {title}")
            return False

        # 2. Existing filters
        if "manager" in title.lower():
            logger.debug(f"Skipping manager role: {title}")
            return False
            
        titles = self.config['filters']['titles']
        return any(t.lower() in title.lower() for t in titles)

    def _verify_link(self, link, expected_company=None):
        """Verify the link is accurate by performing a browser-based visit
        to bypass bot detection and check page content."""
        try:
            browser = self._get_browser()
            context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
            page = context.new_page()
            
            # Navigate to the link with a timeout
            response = page.goto(link, wait_until="domcontentloaded", timeout=30000)
            
            if not response or response.status != 200:
                logger.warning(f"Link verification failed (status {response.status if response else 'N/A'}): {link}")
                context.close()
                return False
            
            if expected_company:
                # Give some time for JS to render
                page.wait_for_timeout(2000)
                content = page.content().lower()
                content_match = expected_company.lower() in content
                if not content_match:
                    logger.warning(f"Company mismatch for link: {link} (Expected: {expected_company})")
                    context.close()
                    return False
            
            context.close()
            return True
        except Exception as e:
            logger.warning(f"Error verifying link {link} with Playwright: {e}")
            return False

    def _is_recent(self, date_str):
        """Check if a job posting date is within max_age_days. 
        Returns True if no date provided (fail-open for sources without dates like Playbill)."""
        if not date_str:
            return True
        
        max_age = self.config['filters'].get('max_age_days', 14)
        cutoff = datetime.now() - timedelta(days=max_age)
        
        try:
            # Handle ISO format (Greenhouse) and epoch-converted strings (Lever)
            posted = datetime.fromisoformat(date_str.replace('Z', '+00:00').replace('+00:00', ''))
            is_fresh = posted >= cutoff
            if not is_fresh:
                logger.debug(f"Skipping stale job posted {date_str} (cutoff: {cutoff.isoformat()})")
            return is_fresh
        except (ValueError, TypeError):
            logger.warning(f"Could not parse date: {date_str}, allowing job through")
            return True

    def _is_target_location(self, location_str):
        if not location_str:
            return False
        
        loc_lower = location_str.lower()
        include = ["new york", "nyc", "brooklyn", "manhattan", "remote", "new york city"]
        exclude = ["long island city", "queens", "bronx", "staten island"]
        
        # Check exclusions first
        if any(ex in loc_lower for ex in exclude):
            return False
            
        # Check inclusions
        return any(inc in loc_lower for inc in include)

    def run_all(self):
        pool = []
        pool.extend(self.scrape_general())
        pool.extend(self.scrape_favorites())
        pool.extend(self.scrape_playbill())
        
        # Deduplicate pool by link
        seen_links = set()
        dedup_pool = []
        for job in pool:
            # Check link deduplication
            if job['link'] in seen_links:
                continue
            
            # Check historical deduplication (Role @ Company)
            comp_norm = "".join(job.get('company', '').lower().split())
            role_norm = "".join(job.get('role', '').lower().split())
            if (comp_norm, role_norm) in self.applied_history_set:
                logger.info(f"Skipping historical duplicate early: {job.get('role')} @ {job.get('company')}")
                continue

            dedup_pool.append(job)
            seen_links.add(job['link'])
        
        if not dedup_pool:
            logger.info("No new jobs found to rank.")
            return

        logger.info(f"Total pool for ranking: {len(dedup_pool)} jobs")
        
        scout = AvaScout()
        generator = AvaGenerator()
        try:
            top_jobs = scout.rank(dedup_pool, limit=25)
            logger.info(f"Scout selected {len(top_jobs)} relevant opportunities. Starting fulfillment...")
            
            # Use generator to handle document creation and webhook dispatch
            generator.workflow.invoke({"jobs": top_jobs, "results": []})
            
            # Save to local DB for tracking
            for job in top_jobs:
                db_id = job.get('id') or job.get('link')
                self.save_job(db_id, job['role'], job['company'])
                
        except Exception as e:
            logger.error(f"Fulfillment pipeline failed: {e}")
            logger.info("Falling back to basic dispatch for first 25 jobs.")
            for job in dedup_pool[:25]:
                self.dispatch(job)
                db_id = job.get('id') or job.get('link')
                role = job.get('role') or job.get('title') or 'Position'
                company = job.get('company', 'Unknown')
                self.save_job(db_id, role, company)

if __name__ == "__main__":
    watcher = AvaWatcher()
    try:
        watcher.run_all()
    finally:
        watcher.close()
