def simulate_row_construction(company, role, job_link, folder_link, salary=""):
    # New logic
    row = [
        f'=HYPERLINK("{job_link}", "{company}")', # Column A
        role,                                     # Column B
        salary,                                   # Column C
        "No",                                     # Column D
        "",                                       # Column E
        "",                                       # Column F
        "To Apply",                               # Column G
        folder_link                               # Column H
    ]
    return row

def simulate_matching(target_company, target_role, sheet_data):
    # normalize
    norm_company = target_company.lower().replace(" ", "")
    norm_role = target_role.lower().replace(" ", "")
    
    for i, row in enumerate(sheet_data):
        # row[0] is company (visible text if hyperlinked)
        row_company = str(row[0]).lower().replace(" ", "")
        row_role = str(row[1]).lower().replace(" ", "")
        
        if row_company == norm_company and row_role == norm_role:
            return i + 1 # 1-indexed row
    return -1

# Test Cases
test_sheet = [
    ["Google", "Software Engineer"], # Pre-existing manually hyperlinked (text matches)
    ["Meta", "Product Manager"]
]

print("--- NEW ROW CONSTRUCTION ---")
new_row = simulate_row_construction("Netflix", "Senior Designer", "https://netflix.com/job", "https://drive.com/folder")
print(f"Generated Row: {new_row}")
assert new_row[0] == '=HYPERLINK("https://netflix.com/job", "Netflix")'
assert new_row[7] == "https://drive.com/folder"
assert len(new_row) == 8

print("\n--- MATCHING EXISTING (MANUAL HYPERLINK) ---")
match = simulate_matching("Google", "Software Engineer", test_sheet)
print(f"Match found at row: {match}")
assert match == 1

print("\n--- MATCHING NON-EXISTENT ---")
match = simulate_matching("Apple", "CEO", test_sheet)
print(f"Match found: {match}")
assert match == -1

print("\nAll simulations passed!")
