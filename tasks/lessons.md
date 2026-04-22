# Lessons & Patterns

## Communication
- **Caveman lite** communication style enabled. Concise, technical, no filler.

## Architecture
- **LangGraph for Ranking**: Use a stateful, agentic approach for job ranking instead of deterministic filters.
- **Top 25 Constraint**: The user's girlfriend (the end-user) requested exactly the top 25 most relevant jobs.
- **Hybrid Inference**: Ollama Cloud (31B models) for reasoning, local Ollama (4B models) for dev/testing.
- **No Gemini**: User explicitly requested the removal of Gemini API keys. Stick to Ollama/Ollama Cloud.

## Data Handling
- **Resumes as Ground Truth**: Use `.docx` resume data to build `profile.json` (ground truth for ranker).
- **Sheet History as Signal**: Completed applications in the Google Sheet should be used to down-score jobs at those companies to surface new opportunities.
- **Deduplication**: Job pool must be deduplicated by URL before ranking.
- **Save State**: Only save jobs to the local DB if they are actually dispatched (top 25). This ensures rejected but high-potential jobs can stay in the pool for future runs if the scraper finds them again.

## Persistence (WSL2)
- **Clock Drift**: WSL2 time drifts when host sleeps. `systemd-timesyncd` fixes on wake.
- **Persistent Timers**: Use `systemd` user timers with `Persistent=true` instead of `cron` to catch up on missed runs while the machine was asleep.
- **Environment Isolation**: User-level services need `EnvironmentFile` pointing to the absolute path of `.env`.
