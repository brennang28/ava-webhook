---
name: ava-webhook
description: "Skill for the Ava_webhook area of ava-webhook. 52 symbols across 14 files."
---

# Ava_webhook

52 symbols | 14 files | Cohesion: 83%

## When to Use

- Working with code in `src/`
- Understanding how test_should_process_job, is_new, save_job work
- Modifying ava_webhook-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `src/ava_webhook/watcher.py` | _get_browser, _normalize_url, is_new, save_job, scrape_general (+12) |
| `src/ava_webhook/generator.py` | _finalize_job, _lookup_company_address, _write_to_template, _is_header_line, _upload_to_drive (+11) |
| `src/ava_webhook/scout.py` | AvaScout, _load_profile, rank, normalize, __init__ (+1) |
| `tests/test_write_to_template_standalone.py` | test_preserve_closing_and_replace_placeholders, test_filter_duplicate_headers, test_resume_spacing |
| `tests/test_filtering.py` | test_should_process_job |
| `scratch/upload_fixed_wme.py` | upload_fixed_wme |
| `scratch/upload_all_fixed.py` | upload_all_fixed |
| `scratch/test_flagging.py` | test_flagging |
| `scratch/test_accuracy.py` | test_accuracy_logic |
| `scratch/regenerate_wme.py` | regenerate_wme |

## Entry Points

Start here when exploring this area:

- **`test_should_process_job`** (Function) — `tests/test_filtering.py:32`
- **`is_new`** (Function) — `src/ava_webhook/watcher.py:100`
- **`save_job`** (Function) — `src/ava_webhook/watcher.py:122`
- **`scrape_general`** (Function) — `src/ava_webhook/watcher.py:160`
- **`scrape_playbill`** (Function) — `src/ava_webhook/watcher.py:207`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `AvaScout` | Class | `src/ava_webhook/scout.py` | 50 |
| `test_should_process_job` | Function | `tests/test_filtering.py` | 32 |
| `is_new` | Function | `src/ava_webhook/watcher.py` | 100 |
| `save_job` | Function | `src/ava_webhook/watcher.py` | 122 |
| `scrape_general` | Function | `src/ava_webhook/watcher.py` | 160 |
| `scrape_playbill` | Function | `src/ava_webhook/watcher.py` | 207 |
| `scrape_favorites` | Function | `src/ava_webhook/watcher.py` | 261 |
| `run_all` | Function | `src/ava_webhook/watcher.py` | 514 |
| `test_preserve_closing_and_replace_placeholders` | Function | `tests/test_write_to_template_standalone.py` | 52 |
| `test_filter_duplicate_headers` | Function | `tests/test_write_to_template_standalone.py` | 100 |
| `test_resume_spacing` | Function | `tests/test_write_to_template_standalone.py` | 143 |
| `upload_fixed_wme` | Function | `scratch/upload_fixed_wme.py` | 9 |
| `upload_all_fixed` | Function | `scratch/upload_all_fixed.py` | 10 |
| `test_flagging` | Function | `scratch/test_flagging.py` | 10 |
| `test_accuracy_logic` | Function | `scratch/test_accuracy.py` | 18 |
| `regenerate_wme` | Function | `scratch/regenerate_wme.py` | 10 |
| `test_relevance` | Function | `scripts/verify_relevance.py` | 8 |
| `test_filters` | Function | `scripts/verify_filters.py` | 7 |
| `test_scout_init` | Function | `scratch/test_scout_direct.py` | 9 |
| `find_one_full_pipeline` | Function | `scratch/test_find_one.py` | 15 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Run_all → _normalize_url` | intra_community | 4 |
| `Run_all → _get_browser` | intra_community | 4 |
| `Run_all → Close` | cross_community | 4 |
| `Run_all → _company_name_variants` | cross_community | 4 |
| `Run_all → _should_process_job` | intra_community | 4 |
| `Run_all → _is_target_location` | intra_community | 4 |
| `Run_all → _is_recent` | intra_community | 4 |
| `Scrape_favorites → _normalize_url` | intra_community | 4 |
| `Regenerate_wme → _parse_json` | intra_community | 3 |
| `Regenerate_wme → _normalize_mapped_experience` | intra_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tests | 10 calls |
| Scratch | 2 calls |

## How to Explore

1. `gitnexus_context({name: "test_should_process_job"})` — see callers and callees
2. `gitnexus_query({query: "ava_webhook"})` — find related execution flows
3. Read key files listed above for implementation details
