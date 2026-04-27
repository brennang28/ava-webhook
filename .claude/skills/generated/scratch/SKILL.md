---
name: scratch
description: "Skill for the Scratch area of ava-webhook. 14 symbols across 9 files."
---

# Scratch

14 symbols | 9 files | Cohesion: 86%

## When to Use

- Working with code in `scratch/`
- Understanding how invoke, mock_post, test_model work
- Modifying scratch-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `scratch/fix_hallucinations.py` | get_draft_files, audit_draft, fix_draft, main |
| `tests/test_generator.py` | invoke, MockResponse, mock_post |
| `scratch/test_model_naming.py` | test_model |
| `scratch/test_fixed_client.py` | test_fixed_client |
| `tests/test_playwright.py` | test_playwright_verify |
| `scratch/test_playwright_extract.py` | test_extract |
| `scratch/query_jobs.py` | query_db |
| `src/ava_webhook/watcher.py` | close |
| `src/ava_webhook/render_viz.py` | render_html_to_png |

## Entry Points

Start here when exploring this area:

- **`invoke`** (Function) — `tests/test_generator.py:17`
- **`mock_post`** (Function) — `tests/test_generator.py:54`
- **`test_model`** (Function) — `scratch/test_model_naming.py:12`
- **`test_fixed_client`** (Function) — `scratch/test_fixed_client.py:12`
- **`get_draft_files`** (Function) — `scratch/fix_hallucinations.py:16`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `MockResponse` | Class | `tests/test_generator.py` | 18 |
| `invoke` | Function | `tests/test_generator.py` | 17 |
| `mock_post` | Function | `tests/test_generator.py` | 54 |
| `test_model` | Function | `scratch/test_model_naming.py` | 12 |
| `test_fixed_client` | Function | `scratch/test_fixed_client.py` | 12 |
| `get_draft_files` | Function | `scratch/fix_hallucinations.py` | 16 |
| `audit_draft` | Function | `scratch/fix_hallucinations.py` | 19 |
| `fix_draft` | Function | `scratch/fix_hallucinations.py` | 63 |
| `main` | Function | `scratch/fix_hallucinations.py` | 95 |
| `test_playwright_verify` | Function | `tests/test_playwright.py` | 6 |
| `test_extract` | Function | `scratch/test_playwright_extract.py` | 3 |
| `query_db` | Function | `scratch/query_jobs.py` | 3 |
| `close` | Function | `src/ava_webhook/watcher.py` | 51 |
| `render_html_to_png` | Function | `src/ava_webhook/render_viz.py` | 4 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Run_all → Close` | cross_community | 4 |
| `Main → MockResponse` | intra_community | 4 |
| `Scrape_playbill → Close` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tests | 1 calls |
| Ava_webhook | 1 calls |

## How to Explore

1. `gitnexus_context({name: "invoke"})` — see callers and callees
2. `gitnexus_query({query: "scratch"})` — find related execution flows
3. Read key files listed above for implementation details
