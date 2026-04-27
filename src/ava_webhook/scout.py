import os
import json
import logging
from typing import Annotated, TypedDict, List
from operator import add
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langfuse import Langfuse
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv

# Setup logging
logger = logging.getLogger(__name__)

# Load env for standalone testing
load_dotenv()

# --- Constants ---
MIN_RELEVANCE_SCORE = 70

# --- Structured Output Models ---

class JobScore(BaseModel):
    """Relevance score for a single job."""
    job_index: int = Field(description="The index of the job in the provided list (0-based)")
    score: int = Field(description="Relevance score from 0 to 100", ge=0, le=100)
    reason: str = Field(description="One-sentence explanation for the score")

class RankingResult(BaseModel):
    """Result of scoring a batch of jobs."""
    scores: List[JobScore]

# --- State Definition ---

class ScoutState(TypedDict):
    # Input
    jobs: List[dict]
    profile: dict
    applied_companies: List[str] # List of companies already applied to
    applied_history: List[dict]   # List of specific (role, company) pairs already applied to
    success_patterns: dict       # Interview-proven success factors
    
    # Internal
    scored_jobs: Annotated[List[dict], add]  # Accumulates scored jobs across batches
    
    # Output
    top_jobs: List[dict]

# --- Agent Implementation ---

class AvaScout:
    def __init__(self, config_path="config.json", db_path="jobs.db", profile_path="research/data/profile.json", applied_path="research/data/applied_companies.json", patterns_path="research/data/success_patterns.json", history_path="research/data/applied_history.json"):
        self.profile_path = profile_path
        self.applied_path = applied_path
        self.patterns_path = patterns_path
        self.history_path = history_path
        
        # 0. Load Config
        self.config = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    self.config = json.load(f)
            except Exception as e:
                logger.error(f"Error loading config in scout: {e}")
        
        models_config = self.config.get("models", {})
        self.scouting_model = models_config.get("scouting", "gemma4:31b")
        
        self.db_path = db_path
        self.ollama_api_key = os.getenv("OLLAMA_AUX2_API_KEY")
        self.cloud_url = os.getenv("OLLAMA_CLOUD_URL", "https://ollama.com")
        self.desktop_url = os.getenv("DESKTOP_OLLAMA_URL", "http://127.0.0.1:11434")

        # Initial default LLM
        self.llm = self._init_llm(self.scouting_model)
        self.structured_llm = self.llm.with_structured_output(RankingResult)
        
        self.workflow = self._build_graph()
        self.langfuse = Langfuse()

    def _init_llm(self, model_name: str, **kwargs) -> ChatOllama:
        """Initializes ChatOllama with appropriate base URL and auth."""
        if self.ollama_api_key:
            return ChatOllama(
                model=model_name,
                base_url=self.cloud_url,
                client_kwargs={"headers": {"Authorization": f"Bearer {self.ollama_api_key}"}},
                **kwargs
            )
        else:
            return ChatOllama(
                model="llama3.2:3b", # Smaller model for local dev
                base_url=self.desktop_url,
                **kwargs
            )

    def _get_llm_with_config(self, model_name: str, config: dict):
        """Returns a ChatOllama instance with parameters from Langfuse config."""
        params = {}
        if "temperature" in config:
            params["temperature"] = float(config["temperature"])
        if "num_predict" in config:
            params["num_predict"] = int(config["num_predict"])
        if "top_p" in config:
            params["top_p"] = float(config["top_p"])
            
        return self._init_llm(model_name, **params)

    def _build_graph(self) -> StateGraph:
        builder = StateGraph(ScoutState)
        
        # Define Nodes
        builder.add_node("load_profile", self._load_profile)
        builder.add_node("score_jobs", self._score_jobs)
        builder.add_node("select_top_25", self._select_top_25)
        
        # Define Edges
        builder.add_edge(START, "load_profile")
        builder.add_edge("load_profile", "score_jobs")
        builder.add_edge("score_jobs", "select_top_25")
        builder.add_edge("select_top_25", END)
        
        return builder.compile()

    # --- Nodes ---

    def _load_profile(self, state: ScoutState):
        """Loads the candidate profile, applied history, and success patterns."""
        profile = {}
        applied = []
        patterns = {}
        
        if os.path.exists(self.profile_path):
            with open(self.profile_path, 'r') as f:
                profile = json.load(f)
        
        if os.path.exists(self.applied_path):
            with open(self.applied_path, 'r') as f:
                applied = json.load(f)

        if os.path.exists(self.patterns_path):
            with open(self.patterns_path, 'r') as f:
                patterns = json.load(f)
        
        history = []
        if os.path.exists(self.history_path):
            with open(self.history_path, 'r') as f:
                data = json.load(f)
                # Handle Google Sheets export format
                if "values" in data:
                    rows = data["values"]
                    if len(rows) > 0:
                        header = rows[0]
                        try:
                            co_idx = header.index("Company")
                            ro_idx = header.index("Role")
                            for row in rows[1:]:
                                if len(row) > max(co_idx, ro_idx):
                                    history.append({
                                        "company": row[co_idx],
                                        "role": row[ro_idx]
                                    })
                        except ValueError:
                            logger.error("Could not find 'Company' or 'Role' columns in applied_history.json")

        return {
            "profile": profile, 
            "applied_companies": applied, 
            "applied_history": history,
            "success_patterns": patterns
        }

    def _score_jobs(self, state: ScoutState):
        """Scores jobs in batches using the LLM."""
        jobs = state['jobs']
        profile = state['profile']
        applied_list = state.get('applied_companies', [])
        patterns = state.get('success_patterns', {})
        
        if not jobs or not profile:
            return {"scored_jobs": []}
        
        batch_size = 20
        all_scored_jobs = []
        
        # Limit history/patterns to avoid token bloat
        history_summary = ", ".join(applied_list[:50])
        
        # Success Pattern Context
        pattern_context = ""
        if patterns:
            pattern_context = f"""
INTERVIEW SUCCESS PATTERNS (CRITICAL):
Ava has successfully secured interviews for roles matching these patterns:
- Proven Titles: {', '.join(patterns.get('proven_titles', []))}
- Proven Industries: {', '.join(patterns.get('proven_industries', []))}
- Proven Keywords: {', '.join(patterns.get('proven_keywords', []))}
- Geography: {', '.join(patterns.get('geography', []))}
- Target Experience: {patterns.get('experience_level', {}).get('range', 'N/A')}

- BOOST: Give a +20 point bonus to any job that aligns with these patterns.
- REJECT/PENALIZE: Reject or give 0 points to any role requesting more than 2 years of experience. This is a STRICT constraint.
- REJECT: Give 0 points to any role that is an Internship, Temporary position, or Contract role.
- REASON: These factors are historically proven to work for Ava's resume/profile.
"""

        # Construct Profile Context
        profile_context = f"""
CANDIDATE PROFILE:
Name: {profile.get('name')}
Target Titles: {', '.join(profile.get('target_titles', []))}
Industry Interest: {', '.join(profile.get('industries_of_interest', []))}
Summary: {profile.get('professional_summary')}
Experience: {profile.get('experience_level')}
Industry Affinity: {json.dumps(profile.get('industry_affinity_scores', {}), indent=2)}

{pattern_context}

APPLIED HISTORY SIGNAL:
Ava has already applied to roles at these companies: {history_summary}
- NUDGE: If a job is at one of these companies, lower the score slightly (e.g. -10 points). 
- REASON: We want to surface NEW opportunities at NEW companies she hasn't engaged with yet. 

SCORING GUIDANCE:
- Score 0-100 based on fit. 
- BOOST if: {'; '.join(profile.get('scoring_guidance', {}).get('boost_for', []))}
- PENALIZE if: {'; '.join(profile.get('scoring_guidance', {}).get('penalize_for', []))}

CRITICAL INDUSTRY REJECTION (Score 0):
- Reject any roles in: Food Service, Hospitality, Construction, Manual Labor, or Retail Sales (unless for a major Entertainment brand).
- Reject if job requires > 2 years of experience.
- Reject any Internship, Temporary position, or Contract role.
- DO NOT be afraid to give a score of 0. Quality over quantity.
"""

        # Process in batches
        for i in range(0, len(jobs), batch_size):
            batch = jobs[i:i+batch_size]
            logger.info(f"Scoring batch {i//batch_size + 1} ({len(batch)} jobs)... [Heartbeat: System Active]")
            
            # Format batch for prompt
            job_list_str = ""
            for idx, job in enumerate(batch):
                job_list_str += f"[{idx}] Role: {job.get('role')} | Company: {job.get('company')} | Link: {job.get('link')}\n"
            
            # Fetch prompts from Langfuse
            prompt_obj_sys = self.langfuse.get_prompt("score-jobs-system", label="production")
            prompt_obj_human = self.langfuse.get_prompt("score-jobs", label="production")
            
            system_msg_content = prompt_obj_sys.compile()
            human_msg_content = prompt_obj_human.compile(
                name=profile.get('name'),
                target_titles=', '.join(profile.get('target_titles', [])),
                industries_of_interest=', '.join(profile.get('industries_of_interest', [])),
                summary=profile.get('professional_summary'),
                experience=profile.get('experience_level'),
                industry_affinity=json.dumps(profile.get('industry_affinity_scores', {}), indent=2),
                pattern_context=pattern_context,
                history_summary=history_summary,
                boost_for='; '.join(profile.get('scoring_guidance', {}).get('boost_for', [])),
                penalize_for='; '.join(profile.get('scoring_guidance', {}).get('penalize_for', [])),
                job_list_str=job_list_str
            )

            system_msg = SystemMessage(content=system_msg_content)
            human_msg = HumanMessage(content=human_msg_content)
            
            # Create a structured LLM with config from Langfuse (system prompt config)
            llm = self._get_llm_with_config(self.scouting_model, prompt_obj_sys.config)
            structured_llm = llm.with_structured_output(RankingResult)
            
            try:
                result = structured_llm.invoke([system_msg, human_msg])
                # Map scores back to job objects
                for score_item in result.scores:
                    if 0 <= score_item.job_index < len(batch):
                        job_copy = batch[score_item.job_index].copy()
                        job_copy['relevance_score'] = score_item.score
                        job_copy['relevance_reason'] = score_item.reason
                        all_scored_jobs.append(job_copy)
                # Log scores for transparency
                for job in all_scored_jobs:
                    logger.info(f"Scored: {job.get('role')} @ {job.get('company')} -> {job.get('relevance_score')} (Reason: {job.get('relevance_reason')})")
            except Exception as e:
                logger.error(f"Error scoring batch: {e}")
                # Add default scores for the batch to avoid losing them
                for job in batch:
                    job_copy = job.copy()
                    job_copy['relevance_score'] = 50
                    job_copy['relevance_reason'] = "Error during AI scoring"
                    all_scored_jobs.append(job_copy)

        return {"scored_jobs": all_scored_jobs}

    def _select_top_25(self, state: ScoutState):
        """Filters by MIN_RELEVANCE_SCORE, sorts by score, and returns top jobs."""
        scored = state.get('scored_jobs', [])
        
        # Filter by threshold first
        high_quality = [j for j in scored if j.get('relevance_score', 0) >= MIN_RELEVANCE_SCORE]
        
        logger.info(f"Filtering: {len(high_quality)} / {len(scored)} jobs passed threshold (>= {MIN_RELEVANCE_SCORE})")
        
        # Sort descending by score
        sorted_jobs = sorted(high_quality, key=lambda x: x.get('relevance_score', 0), reverse=True)
        # Take top 1 (or fewer if pool is smaller)
        top_25 = sorted_jobs[:25]
        return {"top_jobs": top_25}

    # --- Public API ---

    def rank(self, jobs: List[dict], limit=25) -> List[dict]:
        """Runs the ranking pipeline for the given jobs."""
        # Pre-load history for deduplication
        temp_state = self._load_profile({})
        history = temp_state.get('applied_history', [])
        
        def normalize(s):
            return "".join(s.lower().split())

        seen_set = set()
        for h in history:
            seen_set.add((normalize(h['company']), normalize(h['role'])))

        filtered_jobs = []
        for job in jobs:
            comp = normalize(job.get('company', ''))
            role = normalize(job.get('role', ''))
            if (comp, role) not in seen_set:
                filtered_jobs.append(job)
            else:
                logger.info(f"Filtering historically duplicate job: {job.get('role')} @ {job.get('company')}")

        initial_state = {
            "jobs": filtered_jobs,
            "profile": {},
            "applied_companies": [],
            "applied_history": [],
            "success_patterns": {},
            "scored_jobs": [],
            "top_jobs": []
        }
        
        final_state = self.workflow.invoke(initial_state)
        return final_state['top_jobs'][:limit]

if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    scout = AvaScout()
    test_jobs = [
        {"role": "Marketing Coordinator", "company": "Creative Artists Agency", "link": "http://test.com/1"},
        {"role": "Junior Accountant", "company": "Plumbing Inc", "link": "http://test.com/2"},
        {"role": "Social Media Assistant", "company": "MSG Entertainment", "link": "http://test.com/3"},
    ]
    ranked = scout.rank(test_jobs)
    for job in ranked:
        print(f"[{job['relevance_score']}] {job['role']} @ {job['company']} - {job['relevance_reason']}")
