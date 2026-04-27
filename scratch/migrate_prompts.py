import os
from langfuse import Langfuse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Langfuse client
# LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST must be in .env
langfuse = Langfuse()

prompts = [
    {
        "name": "analyze-job",
        "prompt": """Analyze this job description for Ava Aschettino:
Role: {{role}}
Company: {{company}}
Salary Hint: {{salary}}
Description: {{description}}

Identify:
1. Top 3-4 core requirements.
2. Company vibe.
3. Primary problem to solve.
4. Salary/Pay range. Look closely at the description. If found, format as '$Min - $Max' or similar. 
   If not found in description but Salary Hint exists and is valid, use Hint.
   If absolutely no info, return 'Not Listed'.

Return JSON only: {"requirements": [], "vibe": "", "problem": "", "salary": ""}""",
        "config": {
            "model": "gemma4:31b:cloud",
            "temperature": 0.0,
            "reasoning_policy": "standard"
        }
    },
    {
        "name": "map-experience",
        "prompt": "Map Ava's experience to requirements: {{requirements}}\nResume:\n{{resume}}\nReturn JSON list of 'mapping' objects: {\"requirement\": \"...\", \"evidence\": \"...\"}.",
        "config": {
            "model": "gemma4:31b:cloud",
            "temperature": 0.0,
            "reasoning_policy": "standard"
        }
    },
    {
        "name": "resolve-template",
        "prompt": """Analyze this cover letter template and the candidate's mapping evidence.
TEMPLATE:
{{template}}

EVIDENCE:
{{mapping}}

INSTRUCTIONS:
1. Identify all sections with bracketed options like [A / B / C].
2. For each, select the SINGLE best option that is supported by the evidence.
3. Return a clean version of the template with all brackets resolved and all placeholders like [Company Name] filled with '{{company}}'.""",
        "config": {
            "model": "gemma4:31b:cloud",
            "temperature": 0.0,
            "reasoning_policy": "standard"
        }
    },
    {
        "name": "write-cover-letter",
        "prompt": """Draft a 3-paragraph cover letter using this resolved template as your structure:
{{resolved_template}}

CONTEXT:
- Candidate: Ava Aschettino (EXTERNAL applicant)
- Target Role: {{role}} at {{company}}
- Company Vibe: {{vibe}}

INSTRUCTIONS:
1. Adapt the tone to match the Company Vibe (e.g. if luxury, use sophisticated language).
2. Use ONLY the following evidence for factual claims: {{mapping}}
3. MANDATORY: DO NOT include any brackets `[...]` or choices in the final output.
4. MANDATORY: If you are not 100% confident in a specific claim, wrap it in <verify>...</verify> tags.
5. CRITICAL: Output ONLY the 3-4 body paragraphs. DO NOT include the header (name, address, contact info, 'Hiring Manager', company name, address), the salutation ('Dear Hiring Manager,'), or the closing ('Sincerely, Ava Aschettino'). The template already contains these elements.

Return ONLY the body paragraphs.""",
        "config": {
            "model": "qwen2.5vl:3b",
            "temperature": 0.7,
            "reasoning_policy": "standard"
        }
    },
    {
        "name": "verify-accuracy",
        "prompt": """Analyze this cover letter for factual accuracy against the candidate's resume.
RESUME GROUND TRUTH:
{{resume}}

COVER LETTER:
{{letter}}

TARGET JOB: {{role}} at {{company}}

CHECKLIST:
1. Does the letter claim she currently works at {{company}}? (FAIL if yes)
2. Are there any roles, dates, or metrics mentioned that are NOT in the resume? (FAIL if yes)
3. Does it misrepresent her relationship to the target company?

Return JSON: 'status' (PASS/FAIL), 'hallucinations' (list of identified lies/inaccuracies).""",
        "config": {
            "model": "gemma4:31b:cloud",
            "temperature": 0.0,
            "reasoning_policy": "standard"
        }
    },
    {
        "name": "critique-review",
        "prompt": """Review this cover letter for NYU/NYC brand, length, and accuracy.
ACCURACY REPORT: {{accuracy}}
LETTER:
{{letter}}

If accuracy is 'FAIL' or there are hallucinations, you MUST list them as required improvements.
If everything is perfect and accurate, return 'EXCELLENT'.""",
        "config": {
            "model": "gemma4:31b:cloud",
            "temperature": 0.0,
            "reasoning_policy": "standard"
        }
    },
    {
        "name": "extract-address",
        "prompt": "Extract only the physical office address for {{company_name}} from this text. If multiple, pick the NYC one if present, otherwise HQ. Return ONLY the address string: {{context}}",
        "config": {
            "model": "gemma4:31b:cloud",
            "temperature": 0.0,
            "reasoning_policy": "standard"
        }
    },
    {
        "name": "score-jobs",
        "prompt": """CANDIDATE PROFILE:
Name: {{name}}
Target Titles: {{target_titles}}
Industry Interest: {{industries_of_interest}}
Summary: {{summary}}
Experience: {{experience}}
Industry Affinity: {{industry_affinity}}

{{pattern_context}}

APPLIED HISTORY SIGNAL:
Ava has already applied to roles at these companies: {{history_summary}}
- NUDGE: If a job is at one of these companies, lower the score slightly (e.g. -10 points). 
- REASON: We want to surface NEW opportunities at NEW companies she hasn't engaged with yet. 

SCORING GUIDANCE:
- Score 0-100 based on fit. 
- BOOST if: {{boost_for}}
- PENALIZE if: {{penalize_for}}

CRITICAL INDUSTRY REJECTION (Score 0):
- Reject any roles in: Food Service, Hospitality, Construction, Manual Labor, or Retail Sales (unless for a major Entertainment brand).
- Reject if job requires > 2 years of experience.
- Reject any Internship, Temporary position, or Contract role.
- DO NOT be afraid to give a score of 0. Quality over quantity.

JOB LIST TO RANK:
{{job_list_str}}

Assign a score to each of the jobs above.
""",
        "config": {
            "model": "gemma4:31b:cloud",
            "temperature": 0.0,
            "reasoning_policy": "standard"
        }
    }
]

# We also need the system prompt for score-jobs
prompts.append({
    "name": "score-jobs-system",
    "prompt": """You are an expert recruitment agent. 
Rank the provided jobs by relevance to the candidate profile. 
CRITICAL CONSTRAINTS:
1. Experience: Only select roles for 0-2 years of experience. If a role clearly requires 3+, 5+, or senior experience, give it a score of 0.
2. Role Type: Only select permanent roles. Give a score of 0 to any Internships, Temporary roles, or Contract positions.
2. Return Format: You MUST return a JSON object with a single key "scores" containing a list of job scores.
Example: {"scores": [{"job_index": 0, "score": 85, "reason": "..."}]}
Do not include any preamble or extra text.
Assign a score from 0-100 for each job based on the profile and success patterns provided.""",
    "config": {
        "model": "gemma4:31b:cloud",
        "temperature": 0.0,
        "reasoning_policy": "standard"
    }
})

for p_data in prompts:
    try:
        langfuse.create_prompt(
            name=p_data["name"],
            prompt=p_data["prompt"],
            config=p_data["config"],
            labels=["production"]
        )
        print(f"Successfully created/updated prompt: {p_data['name']}")
    except Exception as e:
        print(f"Error creating prompt {p_data['name']}: {e}")
