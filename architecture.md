# AI Job Scout System Architecture

The Ava Job Pipeline is an automated discovery, ranking, and tracking system for job opportunities. It leverages browser automation (Playwright) for resilience and LLMs (Ollama) for intelligent ranking.

## System Flow

```mermaid
graph TD
    subgraph Trigger
        A[Cron / run.sh]
    end

    subgraph Ingestion ["1. Data Ingestion (watcher.py)"]
        B1[General: LinkedIn / Indeed]
        B2[Favorites: Greenhouse / Lever]
        B3[Service: Playbill]
        B1 & B2 & B3 --> C{New Job?}
    end

    subgraph Verification ["2. Playwright Verification"]
        C -- Yes --> D[Playwright Browser]
        D --> D1[Bypass Bot Blocks]
        D1 --> D2[Verify Company Name]
        D2 --> E{Valid?}
    end

    subgraph Storage ["3. Storage & Deduplication"]
        E -- Yes --> F[(jobs.db SQLite)]
        F --> G[Job Pool]
    end

    subgraph Intelligence ["4. AI Scout (scout.py)"]
        G --> H[LangGraph Orchestrator]
        H --> I[Profile.json]
        H -- Batches --> J[Ollama Inference]
        J1["Local (Gemma)"]
        J2["Cloud (Gemma 31b)"]
        J --> J1
        J --> J2
        J1 & J2 --> K[Rank & Select Top 25]
    end

    subgraph Fulfillment ["5. AI fulfillment (generator.py)"]
        K --> L[LangGraph Send API]
        L -- Fan-out 25x --> M[Tailor Resume & Cover Letter]
        M --> N[Google Drive API]
        N --> O[Create Folder & Docs]
    end

    subgraph Output ["6. Tracking"]
        O -- Webhook --> P[Google Sheets]
        P --> Q[Pre-filled Tracker + Drive Links]
    end

    E -- No --> X[Discard]
    C -- No --> X
```

## Key Components

### 1. Ingestion Layer (`watcher.py`)
- **JobSpy**: Orchestrates search terms across LinkedIn and Indeed.
- **API Clients**: Direct integration with Greenhouse and Lever public APIs.
- **Playwright Subprocess**: Ensures we aren't chasing "ghost" links or mismatched data.

### 2. Intelligence Layer (`scout.py`)
- **LangGraph**: Manages state during the ranking process.
- **Hybrid Inference**:
    - **Cloud**: used for expert-level ranking and complex role alignment.
    - **Local**: used for high-volume initial filtering (latency optimization).

### 3. Persistence Layer (`jobs.db`)
- Tracks unique `job_id` and `link` signatures to ensure Ava never applies to the same job twice.
