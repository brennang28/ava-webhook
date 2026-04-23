from jobspy import scrape_jobs
import pandas as pd

def test_jobspy():
    jobs = scrape_jobs(
        site_name=["linkedin"],
        search_term="Marketing Coordinator",
        location="New York, NY",
        results_wanted=1,
    )
    print("Columns:", jobs.columns.tolist())
    if not jobs.empty:
        print("First row keys:", jobs.iloc[0].to_dict().keys())
        print("Description sample:", str(jobs.iloc[0].get('description', 'N/A'))[:100])
        print("Salary sample:", jobs.iloc[0].get('salary_source', 'N/A'))

if __name__ == "__main__":
    test_jobspy()
