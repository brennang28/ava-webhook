import logging
from jobspy import scrape_jobs
import pandas as pd

logging.basicConfig(level=logging.INFO)

def test_scrape():
    try:
        jobs = scrape_jobs(
            site_name=["linkedin"],
            search_term="Marketing Coordinator",
            location="New York, NY",
            results_wanted=5,
            hours_old=72,
        )
        print("Columns returned by jobspy:")
        print(jobs.columns.tolist())
        print("\nFirst 2 rows (truncated):")
        print(jobs.head(2).to_dict('records'))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_scrape()
