# Ava Job Webhook

Modernized job-watching and application pipeline using LangGraph, Playwright, and `uv`.

## Quick Start

1.  **Install `uv`** (if not already installed).
2.  **Setup Environment**:
    ```bash
    ./setup.sh
    ```
3.  **Run Pipeline**:
    ```bash
    ./run.sh
    ```

## Project Structure (2026 Standards)

- `src/ava_webhook/`: Core logic (Watcher, Scout, Generator).
- `scripts/`: Automation and utility scripts.
- `research/`: Market research and application history.
- `assets/`: Document templates and static assets.
- `tests/`: Automated test suite.

## Modern Infrastructure
- **`src/` Layout**: Standard Python packaging.
- **`uv`**: High-performance dependency management.
- **`pyproject.toml`**: Unified tool configuration.
- **Path Portability**: Root-relative path resolution for all components.
