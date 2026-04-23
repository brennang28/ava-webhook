import operator
import os
import requests
import json
import re
import time
import io
import logging
from typing import Annotated, TypedDict, List, Dict, Any
from docx import Document
from docx.shared import RGBColor
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    accuracy_report: str
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
        cloud_url = os.getenv("OLLAMA_CLOUD_URL")
        desktop_url = os.getenv("DESKTOP_OLLAMA_URL", "http://127.0.0.1:11434")
        api_key = os.getenv("OLLAMA_API_KEY")

        # Reasoning Model
        if ":cloud" in reasoning_model and cloud_url:
            logger.info(f"Using Ollama Cloud for reasoning ({reasoning_model})")
            self.reasoning_llm = ChatOllama(
                model=reasoning_model,
                base_url=cloud_url,
                headers={"Authorization": f"Bearer {api_key}"} if api_key else {}
            )
        else:
            self.reasoning_llm = ChatOllama(
                model=reasoning_model,
                base_url=desktop_url
            )

        # Writing Model
        if ":cloud" in writing_model and cloud_url:
            self.writing_llm = ChatOllama(
                model=writing_model,
                base_url=cloud_url,
                headers={"Authorization": f"Bearer {api_key}"} if api_key else {}
            )
        else:
            self.writing_llm = ChatOllama(
                model=writing_model,
                base_url=desktop_url
            )

        # 2. Context paths
        self.resume_path = "assets/Aschettino, Ava- Resume.docx"
        self.template_path = "assets/Aschettino, Ava - Cover Letter Template.docx"
        
        # Load text for LLM
        self.resume_text = self._load_context(self.resume_path)
        self.template_text = self._load_context(self.template_path)
        
        # 3. Main Workflow
        self.workflow = self._build_graph()
        
    def _load_context(self, path: str) -> str:
        if not os.path.exists(path):
            return ""
        
        if path.endswith(".docx"):
            try:
                doc = Document(path)
                return "\n".join([p.text for p in doc.paragraphs])
            except Exception as e:
                print(f"Error extracting text from docx: {e}")
                return ""
        else:
            with open(path, 'r') as f:
                return f.read()

    def _build_graph(self) -> StateGraph:
        builder = StateGraph(OverallState)
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
            
            job_state.update(self._analyze_job(job_state))
            job_state.update(self._map_experience(job_state))
            
            while job_state["revision_count"] < 2:
                job_state.update(self._draft_sections(job_state))
                job_state.update(self._verify_accuracy(job_state))
                job_state.update(self._critique_review(job_state))
                if "EXCELLENT" in job_state.get("critique", "").upper():
                    break
            
            job_state.update(self._finalize_job(job_state))
            results.extend(job_state.get("results", []))
            time.sleep(2)
            
        return {"results": results}

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

    def _analyze_job(self, state: JobProcessState):
        job = state["job"]
        print(f"--- [Node: Analyze Job] starting for {job.get('company')} ---")
        prompt = f"Analyze this job description for Ava Aschettino:\nRole: {job.get('role')}\nCompany: {job.get('company')}\nDescription: {job.get('description', 'No description provided')}\n\nIdentify:\n1. Top 3-4 core requirements.\n2. Company vibe.\n3. Primary problem to solve.\n\nReturn JSON: 'requirements', 'vibe', 'problem'."
        
        res = self.reasoning_llm.invoke([SystemMessage(content="You are a requirement analyst."), HumanMessage(content=prompt)])
        analysis = self._parse_json(res.content)
        return {"job_analysis": analysis}

    def _map_experience(self, state: JobProcessState):
        analysis = state["job_analysis"]
        resume = state["resume_text"]
        print(f"--- [Node: Map Experience] mapping to STAR evidence ---")
        prompt = f"Map Ava's experience to requirements: {analysis.get('requirements')}\nResume:\n{resume}\nReturn JSON list of 'mapping' objects: {{\"requirement\": \"...\", \"evidence\": \"...\"}}."

        res = self.reasoning_llm.invoke([SystemMessage(content="You are a career matcher."), HumanMessage(content=prompt)])
        mapping = self._parse_json(res.content)
        return {"mapped_experience": mapping}

    def _draft_sections(self, state: JobProcessState):
        job = state["job"]
        analysis = state["job_analysis"]
        mapping = state["mapped_experience"]
        template = state["template_text"]
        print(f"--- [Node: Draft Sections] Revision: {state['revision_count']} ---")
        prompt = (
            f"Draft a 3-paragraph cover letter strictly following this template context:\n{template}\n\n"
            f"CONTEXT:\n"
            f"- Candidate: Ava Aschettino (EXTERNAL applicant)\n"
            f"- Current Role: Marketing & Partnerships Assistant at The Paley Center for Media\n"
            f"- Target Role: {job.get('role')} at {job.get('company')}\n\n"
            f"INSTRUCTIONS:\n"
            f"1. Ava does NOT currently work at {job.get('company')}. Do not claim she does.\n"
            f"2. Use ONLY the following evidence for factual claims: {mapping}\n"
            f"3. Maintain a professional, persuasive tone consistent with the NYU/NYC brand.\n"
            f"4. MANDATORY: If you are not 100% confident in a specific claim or if it is a calculated inference, wrap that exact phrase in <verify>...</verify> tags.\n\n"
            f"Return the full letter text."
        )

        res = self.writing_llm.invoke([SystemMessage(content="Persuasive career writer with a focus on factual accuracy."), HumanMessage(content=prompt)])
        return {"final_cover_letter": res.content}

    def _verify_accuracy(self, state: JobProcessState):
        letter = state["final_cover_letter"]
        resume = state["resume_text"]
        job = state["job"]
        print(f"--- [Node: Verify Accuracy] cross-referencing claims ---")
        
        prompt = (
            f"Analyze this cover letter for factual accuracy against the candidate's resume.\n"
            f"RESUME GROUND TRUTH:\n{resume}\n\n"
            f"COVER LETTER:\n{letter}\n\n"
            f"TARGET JOB: {job.get('role')} at {job.get('company')}\n\n"
            f"CHECKLIST:\n"
            f"1. Does the letter claim she currently works at {job.get('company')}? (FAIL if yes)\n"
            f"2. Are there any roles, dates, or metrics mentioned that are NOT in the resume? (FAIL if yes)\n"
            f"3. Does it misrepresent her relationship to the target company?\n\n"
            f"Return JSON: 'status' (PASS/FAIL), 'hallucinations' (list of identified lies/inaccuracies)."
        )
        
        res = self.reasoning_llm.invoke([SystemMessage(content="Strict factual auditor."), HumanMessage(content=prompt)])
        report = self._parse_json(res.content)
        return {"accuracy_report": json.dumps(report)}

    def _critique_review(self, state: JobProcessState):
        letter = state["final_cover_letter"]
        accuracy = state.get("accuracy_report", "{}")
        print(f"--- [Node: Critique Review] round {state['revision_count']} ---")
        
        prompt = (
            f"Review this cover letter for NYU/NYC brand, length, and accuracy.\n"
            f"ACCURACY REPORT: {accuracy}\n"
            f"LETTER:\n{letter}\n\n"
            f"If accuracy is 'FAIL' or there are hallucinations, you MUST list them as required improvements.\n"
            f"If everything is perfect and accurate, return 'EXCELLENT'."
        )
        res = self.reasoning_llm.invoke([SystemMessage(content="Senior hiring editor focused on brand and integrity."), HumanMessage(content=prompt)])
        return {"revision_count": state["revision_count"] + 1, "critique": res.content}

    def _finalize_job(self, state: JobProcessState):
        print(f"--- [Node: Finalize Job] generating buffers ---")
        job = state["job"]
        resume_draft = "AVA ASCHETTINO - TAILORED DRAFT\n"
        resume_draft += f"Job: {job.get('role')} at {job.get('company')}\n"
        resume_draft += "="*40 + "\n\n"
        for item in state.get("mapped_experience", []):
            resume_draft += f"REQ: {item.get('requirement')}\nSTAR: {item.get('evidence')}\n\n"
        
        cover_letter_buffer = self._write_to_template(self.template_path, state["final_cover_letter"], True, job)
        resume_draft_buffer = self._write_to_template(self.resume_path, resume_draft, False, job)

        folder_link = self._upload_to_drive(
            job.get("company", "Unknown"), 
            job.get("role", "Unknown"), 
            cover_letter_buffer,
            resume_draft_buffer
        )
        
        processed_job = job.copy()
        processed_job["cover_letter_text"] = state["final_cover_letter"]
        processed_job["resume_draft_text"] = resume_draft
        processed_job["folder_link"] = folder_link
        return {"results": [processed_job]}

    def _write_to_template(self, template_path: str, content: str, is_cover_letter: bool, job: Dict) -> io.BytesIO:
        doc = Document(template_path)
        
        if is_cover_letter:
            start_index = 0
            for i, p in enumerate(doc.paragraphs):
                if any(x in p.text for x in ["[Date]", "[Hiring Manager Name]", "Dear"]):
                    start_index = i
                    break
            
            placeholders = {
                "[Date]": time.strftime("%B %d, %Y"),
                "[Hiring Manager Name]": "Hiring Manager",
                "[Company Name]": job.get("company", "the team"),
            }
            
            for p in doc.paragraphs[:start_index+1]:
                for key, val in placeholders.items():
                    if key in p.text:
                        p.text = p.text.replace(key, val)
            
            body_start = start_index + 1
            while len(doc.paragraphs) > body_start:
                p = doc.paragraphs[-1]
                p._element.getparent().remove(p._element)
            
            for line in content.split("\n"):
                if line.strip():
                    p = doc.add_paragraph()
                    # Parse <verify> tags
                    parts = re.split(r'(<verify>.*?</verify>)', line)
                    for part in parts:
                        if part.startswith("<verify>") and part.endswith("</verify>"):
                            text = part.replace("<verify>", "").replace("</verify>", "")
                            run = p.add_run(text)
                            run.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)
                        else:
                            p.add_run(part)
        else:
            header_limit = 3
            while len(doc.paragraphs) > header_limit:
                p = doc.paragraphs[-1]
                p._element.getparent().remove(p._element)
            
            for line in content.split("\n"):
                if line.strip():
                    p = doc.add_paragraph()
                    # Parse <verify> tags
                    parts = re.split(r'(<verify>.*?</verify>)', line)
                    for part in parts:
                        if part.startswith("<verify>") and part.endswith("</verify>"):
                            text = part.replace("<verify>", "").replace("</verify>", "")
                            run = p.add_run(text)
                            run.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)
                        else:
                            p.add_run(part)
        
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer

    def _upload_to_drive(self, company: str, role: str, cover_buffer: io.BytesIO, resume_buffer: io.BytesIO) -> str:
        parent_folder_id = "1sonKNR4S-OGhKc2Szg54k2L0EtoOjK1Z"
        token_path = 'token.json'
        backup_dir = "drafts"
        os.makedirs(backup_dir, exist_ok=True)
        sanitized_company = company.replace(' ', '_').replace('/', '_')
        local_cover_path = os.path.join(backup_dir, f"{sanitized_company}_CoverLetter.docx")
        local_resume_path = os.path.join(backup_dir, f"{sanitized_company}_ResumeDraft.docx")
        
        try:
            with open(local_cover_path, "wb") as f:
                f.write(cover_buffer.getvalue())
            with open(local_resume_path, "wb") as f:
                f.write(resume_buffer.getvalue())
        except Exception as e:
            logger.error(f"Local backup failed: {e}")
        
        else:
            if not os.path.exists(token_path):
                return f"Saved locally only (token.json missing): {local_cover_path}"
                
            try:
                creds = Credentials.from_authorized_user_file(token_path, ['https://www.googleapis.com/auth/drive.file'])
                drive_service = build('drive', 'v3', credentials=creds)
                
                folder_metadata = {
                    'name': f"{company} - {role}",
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [parent_folder_id]
                }
                folder = drive_service.files().create(body=folder_metadata, fields='id, webViewLink').execute()
                folder_id = folder.get('id')
                
                cv_metadata = {
                    'name': f'Cover Letter - {company}',
                    'mimeType': 'application/vnd.google-apps.document',
                    'parents': [folder_id]
                }
                cv_media = MediaInMemoryUpload(
                    cover_buffer.getvalue(), 
                    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                    resumable=True
                )
                drive_service.files().create(body=cv_metadata, media_body=cv_media, fields='id').execute()

                rs_metadata = {
                    'name': f'Resume Tailoring Draft - {company}',
                    'mimeType': 'application/vnd.google-apps.document',
                    'parents': [folder_id]
                }
                rs_media = MediaInMemoryUpload(
                    resume_buffer.getvalue(), 
                    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                    resumable=True
                )
                drive_service.files().create(body=rs_metadata, media_body=rs_media, fields='id').execute()
                
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
                payload = {
                    "company": job.get("company", "Unknown"),
                    "role": job.get("role") or job.get("title") or "Position",
                    "salary": job.get("salary", "N/A"),
                    "link": job.get("link", ""),
                    "folder_link": job.get("folder_link", "")
                }
                requests.post(webhook_url, json=payload, timeout=15)
                logger.info(f"Dispatched: {payload['role']} @ {payload['company']}")
            except Exception as e:
                logger.error(f"Error sending webhook: {e}")
        return {}
