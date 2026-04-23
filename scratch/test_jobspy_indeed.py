from jobspy import scrape_jobs
import pandas as pd

def test_jobspy_more():
    jobs = scrape_jobs(
        site_name=["indeed"],
        search_term="Marketing Assistant",
        location="New York, NY",
        results_wanted=3,
    )
    if not jobs.empty:
        for i, row in jobs.iterrows():
            print(f"--- Job {i} ---")
            print("Title:", row.get('title'))
            print("Description length:", len(str(row.get('description', ''))) if row.get('description') else 0)
            print("Salary:", row.get('salary_source'))
            if row.get('description'):
                print("Description snippet:", str(row['description'])[:200])

if __name__ == "__main__":
    test_jobspy_more()
