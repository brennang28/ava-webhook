import json

bad_list = [
    ("Animal Care Centers of NYC", "Community Cat Coordinator"),
    ("Ameriwell Care", "Supports Agency Intake, Outreach And Operations Coordinator NJDDD"),
    ("Centers Health Care", "Admissions Coordinator"),
    ("Legends Global", "Staffing Coordinator, Yankee Stadium"),
    ("Cooper Electric", "Return Goods Coordinator- Cranbury, NJ"),
    ("Cooper Electric", "Inventory Control Coordinator- Cranbury, NJ"),
    ("Unknown", "Home Care Scheduling Coordinator"),
    ("Amazon.com", "Creator Events & Commerce Coordinator"),
    ("Bridgepoint Collective Inc.", "Sales Training Associate"),
    ("Skechers", "Retail Sales Associate"),
    ("Burlington Stores", "Cashier Associate - Part Time"),
    ("Mathnasium", "Associate Center Director"),
    ("Walgreens", "Customer Service Associate"),
    ("Claire's", "Sales Associate"),
    ("Amazon.com", "Email & App Marketing Associate"),
    ("Amazon.com", "Associate Corporate Counsel"),
    ("Krug Orthodontics", "Registered Dental Assistant"),
    ("Zays Plates", "Catering Assistant/Grill Master"),
    ("NYB CPA PC", "Accounting Assistant"),
    ("Mindify Wellness and Care", "Medical Assistant")
]

def normalize(text):
    return "".join(text.lower().split())

with open('scratch/full_sheet.json', 'r') as f:
    data = json.load(f)

values = data.get('values', [])
indices_to_delete = []

for i, row in enumerate(values):
    if len(row) < 2:
        # Check for A or B as single columns
        if len(row) == 1 and row[0] in ["A", "B"]:
             indices_to_delete.append(i)
        continue
    
    comp, role = row[0], row[1]
    norm_comp = normalize(comp)
    norm_role = normalize(role)
    
    for b_comp, b_role in bad_list:
        if normalize(b_comp) in norm_comp and normalize(b_role) in norm_role:
            indices_to_delete.append(i)
            break
        # Also check if role contains the bad role
        if normalize(b_role) in norm_role and normalize(b_comp) == "":
             indices_to_delete.append(i)
             break

print(json.dumps(indices_to_delete))
