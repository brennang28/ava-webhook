from jobspy import scrape_jobs
import pandas as pd
import json

def test_scrape():
    try:
        jobs = scrape_jobs(
            site_name=["linkedin"],
            search_term="Coordinator",
            location="New York, NY",
            results_wanted=1,
            hours_old=24,
        )
        print("Columns found in jobspy output:")
        print(jobs.columns.tolist())
        
        # Display the first row as a dictionary
        if not jobs.empty:
            print("\nFirst job data (as dict):")
            print(json.dumps(jobs.iloc[0].to_dict(), indent=2, default=str))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_scrape()
