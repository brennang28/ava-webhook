import logging
import json
from scout import AvaScout

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_relevance():
    scout = AvaScout()
    
    test_jobs = [
        {
            "role": "Marketing Coordinator", 
            "company": "Netflix", 
            "link": "https://netflix.com/jobs/1",
            "description": "Work on entertainment marketing campaigns for global series."
        },
        {
            "role": "Grill Master", 
            "company": "Burger King", 
            "link": "https://bk.com/jobs/2",
            "description": "Responsibility for grilling meat and maintaining hygiene."
        },
        {
            "role": "Sales Associate", 
            "company": "Gap Inc", 
            "link": "https://gap.com/jobs/3",
            "description": "Retail sales and customer service on the floor."
        },
        {
            "role": "Publicity Assistant", 
            "company": "A24", 
            "link": "https://a24.com/jobs/4",
            "description": "Support films and television projects' publicity efforts."
        }
    ]
    
    logger.info(f"Ranking {len(test_jobs)} test jobs...")
    ranked = scout.rank(test_jobs)
    
    print("\n--- RANKING RESULTS ---")
    returned_roles = [j['role'] for j in ranked]
    for job in ranked:
        print(f"[{job['relevance_score']}] {job['role']} @ {job['company']}")
        print(f"Reason: {job['relevance_reason']}\n")

    # Assertions
    assert "Marketing Coordinator" in returned_roles, "Marketing Coordinator should be included"
    assert "Publicity Assistant" in returned_roles, "Publicity Assistant should be included"
    assert "Grill Master" not in returned_roles, "Grill Master should be FILTERED OUT"
    assert "Sales Associate" not in returned_roles, "Sales Associate should be FILTERED OUT"
    
    logger.info("Verification passed: Only high-relevance jobs returned.")

if __name__ == "__main__":
    test_relevance()
