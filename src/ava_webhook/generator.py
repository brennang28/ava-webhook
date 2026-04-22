import operator
import os
import requests
import json
import re
import time
from typing import Annotated, TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OverallState(TypedDict):
    jobs: List[Dict[str, Any]]
    results: Annotated[List[Dict[str, Any]], operator.add]

class JobProcessState(TypedDict):
    job: Dict[str, Any]
    resume_text: str
    template_text: str
    job_analysis: Dict[str, Any]
    mapped_experience: List[Dict[str, Any]]
    final_cover_letter: str
    final_resume_draft: str
    revision_count: int
    critique: str
    folder_link: str

class AvaGenerator:
    def __init__(self, config_path="config.json"):
        # 0. Load Config
        self.config = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    self.config = json.load(f)
            except Exception as e:
                print(f"Error loading config in generator: {e}")
        
        models_config = self.config.get("models", {})
        reasoning_model = models_config.get("reasoning", "gemma4:26b")
        writing_model = models_config.get("writing", "qwen2.5vl:3b")

        # 1. Models
        desktop_url = os.getenv("DESKTOP_OLLAMA_URL", "http://127.0.0.1:11434")

        # Reasoning Model (Gemma 4 small)
        self.reasoning_llm = ChatOllama(
            model=reasoning_model,
            base_url=desktop_url
        )

        # Writing Model (Qwen 2.5 local)
        self.writing_llm = ChatOllama(
            model=writing_model,
            base_url=desktop_url
        )

        # 2. Context
        self.resume_text = self._load_context("assets/resume.txt")
        self.template_text = self._load_context("assets/template.txt")
        
        # 3. Main Workflow
        self.workflow = self._build_graph()
        
    def _load_context(self, path: str) -> str:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return f.read()
        return ""

    def _build_graph(self) -> StateGraph:
        builder = StateGraph(OverallState)
        # Sequential processing to respect free tier rate limits
        builder.add_node("process_jobs", self._process_jobs_sequentially)
        builder.add_node("send_webhooks", self._send_webhooks)
        
        builder.add_edge(START, "process_jobs")
        builder.add_edge("process_jobs", "send_webhooks")
        builder.add_edge("send_webhooks", END)
        return builder.compile()

    def _process_jobs_sequentially(self, state: OverallState):
        results = []
        for job in state["jobs"]:
            print(f"--- Processing {job.get('company')} sequentially ---")
            # Create a localized job process state
            job_state: JobProcessState = {
                "job": job,
                "resume_text": self.resume_text,
                "template_text": self.template_text,
                "revision_count": 0,
                "job_analysis": {},
                "mapped_experience": [],
                "final_cover_letter": "",
                "final_resume_draft": "",
                "critique": "",
                "folder_link": ""
            }
            
            # Run the mini-workflow for this job manually to ensure sequence
            job_state.update(self._analyze_job(job_state))
            job_state.update(self._map_experience(job_state))
            
            # Loop for revisions
            while job_state["revision_count"] < 2:
                job_state.update(self._draft_sections(job_state))
                job_state.update(self._critique_review(job_state))
                if "EXCELLENT" in job_state.get("critique", "").upper():
                    break
            
            # Finalize
            job_state.update(self._finalize_job(job_state))
            results.extend(job_state.get("results", []))
            
            # Small cooldown to prevent rate-limit bursts
            time.sleep(2)
            
        return {"results": results}

    # --- Utility ---
    def _parse_json(self, text: str) -> Any:
        clean_text = re.sub(r'```json\s*|\s*```', '', text).strip()
        try:
            return json.loads(clean_text)
        except:
            match = re.search(r'(\{.*\}|\[.*\])', clean_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass
        return {"raw": text}

    # --- Worker Nodes ---

    def _analyze_job(self, state: JobProcessState):
        job = state["job"]
        print(f"--- [Node: Analyze Job] starting for {job.get('company')} ---")
        prompt = f"Analyze this job description for Ava Aschettino:\nRole: {job.get('role')}\nCompany: {job.get('company')}\nDescription: {job.get('description', 'No description provided')}\n\nIdentify:\n1. Top 3-4 core requirements (technical or soft skills).\n2. The company 'vibe' (e.g., creative, corporate, mission-driven).\n3. The primary problem this role solves for the team.\n\nReturn as a concise JSON object with 'requirements', 'vibe', and 'problem'."
        
        res = self.reasoning_llm.invoke([SystemMessage(content="You are a requirement analyst."), HumanMessage(content=prompt)])
        analysis = self._parse_json(res.content)
        return {"job_analysis": analysis}

    def _map_experience(self, state: JobProcessState):
        analysis = state["job_analysis"]
        resume = state["resume_text"]
        print(f"--- [Node: Map Experience] mapping requirements to STAR evidence ---")
        
        prompt = f"Map Ava's specific experience to these job requirements:\nJob Requirements: {analysis.get('requirements')}\nVibe: {analysis.get('vibe')}\n\nResume:\n{resume}\n\nFor each requirement, find the single most relevant bullet point or achievement from Ava's resume. Rephrase it using the STAR method if possible, emphasizing metrics.\nReturn as a list of 'mapping' objects: {{\"requirement\": \"...\", \"evidence\": \"...\"}}."

        res = self.reasoning_llm.invoke([SystemMessage(content="You are a strategic career matcher."), HumanMessage(content=prompt)])
        mapping = self._parse_json(res.content)
        return {"mapped_experience": mapping}

    def _draft_sections(self, state: JobProcessState):
        job = state["job"]
        analysis = state["job_analysis"]
        mapping = state["mapped_experience"]
        template = state["template_text"]
        print(f"--- [Node: Draft Sections] generating letter (Revision: {state['revision_count']}) ---")
        
        prompt = f"Draft a 3-paragraph cover letter following this template strictly:\nTemplate:\n{template}\n\nContext:\nJob: {job.get('role')} at {job.get('company')}\nKey Needs: {analysis}\nEvidence to leverage: {mapping}\n\nInstructions:\n1. Paragraph 1: Mention passion for {job.get('company')}'s mission and hook them.\n2. Paragraph 2: Bridge the needs with the specific evidence from the mapping.\n3. Paragraph 3: Call to action and proactive closing.\n4. STRICTLY MAINTAIN 3 PARAGRAPHS.\n\nReturn the full text of the cover letter."

        res = self.writing_llm.invoke([SystemMessage(content="You are a persuasive career writer."), HumanMessage(content=prompt)])
        return {"final_cover_letter": res.content}

    def _critique_review(self, state: JobProcessState):
        letter = state["final_cover_letter"]
        analysis = state["job_analysis"]
        print(f"--- [Node: Critique Review] evaluating round {state['revision_count']} ---")
        
        prompt = f"Critically review this cover letter for quality.\nLetter:\n{letter}\n\nGoals:\n- Only 3 paragraphs?\n- Authentic to Ava Aschettino's brand (NYC, NYU, marketing focus)?\n\nIf it needs improvements, list specifically what to change. If it is already excellent, return 'EXCELLENT'."

        res = self.reasoning_llm.invoke([SystemMessage(content="You are a senior hiring editor."), HumanMessage(content=prompt)])
        return {"revision_count": state["revision_count"] + 1, "critique": res.content}

    def _finalize_job(self, state: JobProcessState):
        print(f"--- [Node: Finalize Job] uploading to drive ---")
        job = state["job"]
        
        # Format the mapped experience into a readable resume tailoring draft
        resume_draft = "AVA ASCHETTINO - RESUME TAILORING DRAFT\n"
        resume_draft += f"Job: {job.get('role')} at {job.get('company')}\n"
        resume_draft += "="*40 + "\n\n"
        for item in state.get("mapped_experience", []):
            resume_draft += f"REQUIREMENT: {item.get('requirement')}\n"
            resume_draft += f"EVIDENCE (STAR): {item.get('evidence')}\n\n"
        
        # Save both
        folder_link = self._upload_to_drive(
            job.get("company", "Unknown"), 
            job.get("role", "Unknown"), 
            state["final_cover_letter"],
            resume_draft
        )
        
        processed_job = job.copy()
        processed_job["cover_letter_text"] = state["final_cover_letter"]
        processed_job["resume_draft_text"] = resume_draft
        processed_job["folder_link"] = folder_link
        
        return {"results": [processed_job]}

    def _upload_to_drive(self, company: str, role: str, cover_content: str, resume_content: str) -> str:
        parent_folder_id = "1sonKNR4S-OGhKc2Szg54k2L0EtoOjK1Z" # 'Ava Job Drafts' folder
        token_path = 'token.json'
        
        # Local backup path
        backup_dir = "drafts"
        os.makedirs(backup_dir, exist_ok=True)
        local_cover_path = os.path.join(backup_dir, f"{company.replace(' ', '_')}_CoverLetter.txt")
        local_resume_path = os.path.join(backup_dir, f"{company.replace(' ', '_')}_ResumeDraft.txt")
        
        try:
            with open(local_cover_path, "w") as f:
                f.write(cover_content)
            with open(local_resume_path, "w") as f:
                f.write(resume_content)
        except Exception as e:
            print(f"Local backup failed: {e}")
        
        if not os.path.exists(token_path):
            return f"Saved locally only (token.json missing): {local_cover_path}"
            
        try:
            # Use token.json for User Authentication (utilizes 5TB quota)
            creds = Credentials.from_authorized_user_file(token_path, ['https://www.googleapis.com/auth/drive.file'])
            drive_service = build('drive', 'v3', credentials=creds)
            
            # 1. Create Folder inside the personal parent
            folder_metadata = {
                'name': f"{company} - {role}",
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id]
            }
            folder = drive_service.files().create(body=folder_metadata, fields='id, webViewLink').execute()
            folder_id = folder.get('id')
            
            # 2. Create Cover Letter Doc inside folder
            cv_metadata = {
                'name': f'Cover Letter - {company}',
                'mimeType': 'application/vnd.google-apps.document',
                'parents': [folder_id]
            }
            cv_media = MediaInMemoryUpload(cover_content.encode('utf-8'), mimetype='text/plain', resumable=True)
            drive_service.files().create(body=cv_metadata, media_body=cv_media, fields='id').execute()

            # 3. Create Resume Draft Doc inside folder
            rs_metadata = {
                'name': f'Resume Tailoring Draft - {company}',
                'mimeType': 'application/vnd.google-apps.document',
                'parents': [folder_id]
            }
            rs_media = MediaInMemoryUpload(resume_content.encode('utf-8'), mimetype='text/plain', resumable=True)
            drive_service.files().create(body=rs_metadata, media_body=rs_media, fields='id').execute()
            
            return folder.get('webViewLink', "No link generated")
            
            return folder.get('webViewLink', "No link generated")
        except Exception as e:
            return f"Saved locally! Drive error: {str(e)}"

    def _send_webhooks(self, state: OverallState):
        webhook_url = os.getenv("WEBHOOK_URL")
        if not webhook_url:
             return {}
            
        print(f"--- [Node: Send Webhooks] sending {len(state['results'])} responses ---")
        for job in state["results"]:
            try:
                # Ensure job is a dict (handles pandas.Series if leaked into results)
                if hasattr(job, 'to_dict'):
                    job_data = job.to_dict()
                elif isinstance(job, dict):
                    job_data = job
                else:
                    job_data = dict(job)

                payload = {
                    "company": job_data.get("company", "Unknown"),
                    "role": job_data.get("role") or job_data.get("title") or "Position",
                    "salary": job_data.get("salary", "N/A"),
                    "link": job_data.get("link", ""),
                    "folder_link": job_data.get("folder_link", "")
                }
                
                requests.post(webhook_url, json=payload, timeout=15)
                logger.info(f"Dispatched: {payload['role']} @ {payload['company']}")
            except Exception as e:
                logger.error(f"Error sending webhook: {e}")
        return {}
