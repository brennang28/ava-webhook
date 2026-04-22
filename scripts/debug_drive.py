from generator import AvaGenerator
import json
import os

# Mock job
job = {
    "company": "UTA Speakers",
    "role": "Assistant",
    "link": "https://uta.com",
    "salary": "N/A"
}

# Mock texts
cover = "This is a test cover letter."
resume = "This is a test resume draft."

gen = AvaGenerator()
link = gen._upload_to_drive(job["company"], job["role"], cover, resume)
print(f"Result Link: {link}")
