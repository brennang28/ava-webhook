---
name: tests
description: "Skill for the Tests area of ava-webhook. 31 symbols across 11 files."
---

# Tests

31 symbols | 11 files | Cohesion: 80%

## When to Use

- Working with code in `tests/`
- Understanding how test_variants_contain_expected, test_empty_name_returns_single_empty_string, test_original_lowercase_always_present work
- Modifying tests-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `tests/test_company_variants.py` | test_variants_contain_expected, test_empty_name_returns_single_empty_string, test_original_lowercase_always_present, test_stripped_version_present_for_suffixed_name, test_ampersand_variants_present (+7) |
| `tests/test_generator.py` | test_generator_initialization, test_generator_fan_out, test_document_generation, MockLLM, test_drive_upload_called (+1) |
| `src/ava_webhook/watcher.py` | _company_name_variants, AvaWatcher, dispatch |
| `tests/test_scrape.py` | MockWatcher, test_scrape |
| `src/ava_webhook/generator.py` | AvaGenerator, _send_webhooks |
| `tests/test_dispatch.py` | manual_test |
| `tests/test_closed_detection.py` | setUp |
| `scratch/test_single_job_find.py` | test_find_one_job |
| `scratch/test_dedup.py` | setUp |
| `scratch/inspect_payload.py` | test_payload_inspection |

## Entry Points

Start here when exploring this area:

- **`test_variants_contain_expected`** (Function) — `tests/test_company_variants.py:56`
- **`test_empty_name_returns_single_empty_string`** (Function) — `tests/test_company_variants.py:63`
- **`test_original_lowercase_always_present`** (Function) — `tests/test_company_variants.py:67`
- **`test_stripped_version_present_for_suffixed_name`** (Function) — `tests/test_company_variants.py:71`
- **`test_ampersand_variants_present`** (Function) — `tests/test_company_variants.py:75`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `MockWatcher` | Class | `tests/test_scrape.py` | 6 |
| `AvaWatcher` | Class | `src/ava_webhook/watcher.py` | 34 |
| `MockLLM` | Class | `tests/test_generator.py` | 16 |
| `AvaGenerator` | Class | `src/ava_webhook/generator.py` | 43 |
| `test_variants_contain_expected` | Function | `tests/test_company_variants.py` | 56 |
| `test_empty_name_returns_single_empty_string` | Function | `tests/test_company_variants.py` | 63 |
| `test_original_lowercase_always_present` | Function | `tests/test_company_variants.py` | 67 |
| `test_stripped_version_present_for_suffixed_name` | Function | `tests/test_company_variants.py` | 71 |
| `test_ampersand_variants_present` | Function | `tests/test_company_variants.py` | 75 |
| `test_trademark_symbols_removed` | Function | `tests/test_company_variants.py` | 80 |
| `test_punctuation_stripped_variant` | Function | `tests/test_company_variants.py` | 85 |
| `test_no_duplicate_variants` | Function | `tests/test_company_variants.py` | 89 |
| `test_suffix_with_comma` | Function | `tests/test_company_variants.py` | 93 |
| `test_co_suffix_stripped` | Function | `tests/test_company_variants.py` | 97 |
| `test_ltd_suffix_stripped` | Function | `tests/test_company_variants.py` | 101 |
| `test_llc_suffix_stripped` | Function | `tests/test_company_variants.py` | 105 |
| `test_scrape` | Function | `tests/test_scrape.py` | 12 |
| `manual_test` | Function | `tests/test_dispatch.py` | 6 |
| `setUp` | Function | `tests/test_closed_detection.py` | 5 |
| `test_find_one_job` | Function | `scratch/test_single_job_find.py` | 9 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Run_all → _company_name_variants` | cross_community | 4 |
| `Scrape_playbill → _company_name_variants` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Ava_webhook | 6 calls |
| Scratch | 1 calls |

## How to Explore

1. `gitnexus_context({name: "test_variants_contain_expected"})` — see callers and callees
2. `gitnexus_query({query: "tests"})` — find related execution flows
3. Read key files listed above for implementation details
