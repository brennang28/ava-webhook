import logging
import json
from scout import AvaScout

# Setup logging to see the filtering messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_filters():
    scout = AvaScout()
    
    # Test Data
    test_jobs = [
        # 1. Historical Duplicate (from applied_history.json)
        {"role": "Administrative Assistant, Finance", "company": "Universal Music Group", "link": "http://test.com/1"},
        
        # 2. Too much experience (should be penalized/rejected by LLM)
        {"role": "Senior Marketing Manager (5+ years exp)", "company": "Big Corp", "link": "http://test.com/2"},
        
        # 3. Valid entry-level role (should pass and rank well)
        {"role": "Marketing Coordinator (Entry Level)", "company": "New Startup", "link": "http://test.com/3"},
    ]
    
    print("\n--- RUNNING RANKING ---")
    ranked = scout.rank(test_jobs)
    
    print("\n--- RESULTS ---")
    found_roles = [job['role'] for job in ranked]
    
    # Check 1: Historical duplicate should NOT be in results
    if "Administrative Assistant, Finance" in found_roles:
        print("❌ FAILED: Historical duplicate was NOT filtered.")
    else:
        print("✅ PASSED: Historical duplicate was filtered.")
        
    # Check 2: Senior role should have very low score or be missing (if LLM gives 0)
    senior_role = next((j for j in ranked if "Senior" in j['role']), None)
    if senior_role:
        print(f"DEBUG: Senior role score: {senior_role['relevance_score']}")
        if senior_role['relevance_score'] > 20:
            print("❌ FAILED: Senior role scored too high.")
        else:
            print("✅ PASSED: Senior role penalized correctly.")
    else:
        print("✅ PASSED: Senior role filtered/rejected correctly.")

    # Check 3: Entry level role should be present
    if "Marketing Coordinator (Entry Level)" in found_roles:
        print("✅ PASSED: Entry level role was kept.")
    else:
        print("❌ FAILED: Entry level role was missing.")

if __name__ == "__main__":
    test_filters()
