import json
import os

def analyze():
    history_file = 'research/applied_history.json'
    if not os.path.exists(history_file):
        print(f"Error: {history_file} not found")
        return

    with open(history_file, 'r') as f:
        data = json.load(f)

    values = data.get('values', [])
    if not values:
        print("No values found in spreadsheet data")
        return

    headers = values[0]
    print(f"Headers: {headers}")
    rows = values[1:]

    interviews = []
    statuses = set()
    for row in rows:
        if len(row) > 6:
            status = row[6].strip()
            statuses.add(status)
            if 'interview' in status.lower() or 'offer' in status.lower() or 'round' in status.lower():
                interviews.append({
                    'company': row[0] if len(row) > 0 else 'N/A',
                    'role': row[1] if len(row) > 1 else 'N/A',
                    'salary': row[2] if len(row) > 2 else 'N/A',
                    'link': row[7] if len(row) > 7 else 'N/A',
                    'status': status
                })

    output = {
        'total_rows': len(rows),
        'interview_count': len(interviews),
        'interviews': interviews,
        'all_statuses': list(statuses)
    }

    with open('research/interview_patterns_raw.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nAnalyzed {len(rows)} rows. Found {len(interviews)} interviews/offers.")
    for i in interviews:
        print(f"- {i['company']}: {i['role']} | Status: {i['status']} | Link: {i['link']}")

if __name__ == "__main__":
    analyze()
