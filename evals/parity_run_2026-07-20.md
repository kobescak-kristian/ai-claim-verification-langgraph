# P3 official eval-parity run — 2026-07-20

Run id: `p3-official-2026-07-20`. Model: `claude-sonnet-4-6`. Frozen inputs
(dataset, ground_truth.json, eval_config.yaml), existing scorer
(`evals/run_parity.py`, same matching rule and metric definitions as the
origin's `evals/run_eval.py`), frozen gate (precision >= 0.95 AND recall
>= 0.90, positive class CONTRADICTED). Tracing on (LangSmith, EU project),
per decisions/0003. Per-task ceiling $1.50; hard bound $18.00 (12 x $1.50)
not approached.

## Result: GATE PASS

| Metric | Value | Threshold |
|---|---|---|
| Precision | **1.0000** (8/8) | >= 0.95 |
| Recall | **1.0000** (8/8) | >= 0.90 |
| Overall verdict accuracy (secondary, not gated) | 1.0000 (35/35) | — |
| Gate | **PASS** | — |

Total spend: **$0.6332** across 12 cases (each case well under the $1.50
per-task ceiling, min $0.0442 / max $0.0609). No case capped (turn or
budget ceiling). Matches the origin's frozen eval result of precision
1.00 / recall 1.00 (run `eval-05fbe4ee`) — same system, same gate, held
under LangGraph.

## Per-case table

| case_id | claims | cost | turns | trace run id |
|---|---|---|---|---|
| case_01_supported_wireless_earbuds | 3/3 | $0.0494 | 4/20 | `f1c8baa3-6d08-4ccc-a76f-b625fca61092` |
| case_02_contradicted_price_laptop | 3/3 | $0.0606 | 5/20 | `7ab049a4-f114-41b1-9c20-848d7941ac42` |
| case_03_contradicted_storage_phone | 3/3 | $0.0481 | 4/20 | `3829d71d-d566-4fd6-b157-d036cdea4772` |
| case_04_contradicted_release_date_camera | 3/3 | $0.0494 | 4/20 | `f93874fa-3f08-4c10-a825-90a5cf17a4a7` |
| case_05_unverifiable_warranty_monitor | 3/3 | $0.0533 | 4/20 | `57e8a6d8-42f7-4d7f-a283-7139cd37b29d` |
| case_06_unverifiable_availability_speaker | 3/3 | $0.0562 | 4/20 | `651b89b7-e281-4a7f-8d37-9abc32349712` |
| case_07_adversarial_near_match_battery_earbuds | 2/2 | $0.0448 | 4/20 | `bc47b280-5abd-4c81-9a81-7c79733ca734` |
| case_08_adversarial_rephrased_price_tablet | 2/2 | $0.0442 | 4/20 | `10ebb6b6-1001-48f2-a285-2b8103368279` |
| case_09_mixed_multi_claim_router | 4/4 | $0.0600 | 4/20 | `2ab7dee0-3801-40dc-a49f-dd7edbee7b28` |
| case_10_supported_specs_bundle_keyboard | 4/4 | $0.0580 | 4/20 | `4cea85ec-7a69-49fb-8fcf-81aed7eb8342` |
| case_11_contradicted_availability_gpu | 3/3 | $0.0609 | 5/20 | `13ceaf8e-3dcd-4eff-b875-84c0b42b3671` |
| case_12_adversarial_authoritative_conflict_smartwatch | 2/2 | $0.0482 | 4/20 | `2f5f074c-ec8e-4ed1-868e-554025a834f3` |
| **Total** | **35/35** | **$0.6332** | — | — |

Trace archive: `evals/traces/p3_official_2026-07-20/` — one JSON file per
case (parent + all child runs), per decisions/0003 Ruling 1. See that
directory's README.md for the evidentiary framing (attested export, not
independently hosted) and the LangSmith dashboard's ~14-day retention.

## Per-claim detail

### case_01_supported_wireless_earbuds
| match | true | predicted | claim |
|---|---|---|---|
| Y | SUPPORTED | SUPPORTED | The SoundWave Pro X2 is priced at $129.99. |
| Y | SUPPORTED | SUPPORTED | It features 30 hours of total battery life with the charging case. |
| Y | SUPPORTED | SUPPORTED | Released on March 1, 2024. |

### case_02_contradicted_price_laptop
| match | true | predicted | claim |
|---|---|---|---|
| Y | CONTRADICTED | CONTRADICTED | Priced at $899. |
| Y | SUPPORTED | SUPPORTED | Comes with 16GB RAM. |
| Y | SUPPORTED | SUPPORTED | Ships with Windows 11 Home. |

### case_03_contradicted_storage_phone
| match | true | predicted | claim |
|---|---|---|---|
| Y | CONTRADICTED | CONTRADICTED | Comes with 256GB of storage. |
| Y | SUPPORTED | SUPPORTED | Has a 6.5-inch display. |
| Y | SUPPORTED | SUPPORTED | Weighs 189 grams. |

### case_04_contradicted_release_date_camera
| match | true | predicted | claim |
|---|---|---|---|
| Y | CONTRADICTED | CONTRADICTED | Released on September 10, 2023. |
| Y | SUPPORTED | SUPPORTED | Features a 24MP sensor. |
| Y | SUPPORTED | SUPPORTED | Supports 4K video recording at 60fps. |

### case_05_unverifiable_warranty_monitor
| match | true | predicted | claim |
|---|---|---|---|
| Y | UNVERIFIABLE | UNVERIFIABLE | Comes with a 3-year manufacturer warranty. |
| Y | SUPPORTED | SUPPORTED | Has a 27-inch 4K display. |
| Y | SUPPORTED | SUPPORTED | Supports HDR10. |

### case_06_unverifiable_availability_speaker
| match | true | predicted | claim |
|---|---|---|---|
| Y | UNVERIFIABLE | UNVERIFIABLE | Currently in stock at all major retailers. |
| Y | SUPPORTED | SUPPORTED | Weighs 540 grams. |
| Y | SUPPORTED | SUPPORTED | Waterproof rating of IPX7. |

### case_07_adversarial_near_match_battery_earbuds
| match | true | predicted | claim |
|---|---|---|---|
| Y | CONTRADICTED | CONTRADICTED | Battery life of 12 hours per charge. |
| Y | SUPPORTED | SUPPORTED | Bluetooth 5.3 connectivity. |

### case_08_adversarial_rephrased_price_tablet
| match | true | predicted | claim |
|---|---|---|---|
| Y | SUPPORTED | SUPPORTED | Starts at $499 for the base model. |
| Y | SUPPORTED | SUPPORTED | Has a 10.9-inch display. |

### case_09_mixed_multi_claim_router
| match | true | predicted | claim |
|---|---|---|---|
| Y | SUPPORTED | SUPPORTED | Supports Wi-Fi 6 (802.11ax). |
| Y | CONTRADICTED | CONTRADICTED | Priced at $249.99. |
| Y | UNVERIFIABLE | UNVERIFIABLE | Includes a 2-year warranty. |
| Y | CONTRADICTED | CONTRADICTED | Has 8 LAN ports. |

### case_10_supported_specs_bundle_keyboard
| match | true | predicted | claim |
|---|---|---|---|
| Y | SUPPORTED | SUPPORTED | Uses hot-swappable mechanical switches. |
| Y | SUPPORTED | SUPPORTED | Connects via USB-C and Bluetooth 5.0. |
| Y | SUPPORTED | SUPPORTED | Priced at $89.99. |
| Y | SUPPORTED | SUPPORTED | Weighs approximately 950 grams. |

### case_11_contradicted_availability_gpu
| match | true | predicted | claim |
|---|---|---|---|
| Y | CONTRADICTED | CONTRADICTED | Currently in stock and shipping immediately. |
| Y | SUPPORTED | SUPPORTED | Has 12GB of GDDR6X memory. |
| Y | SUPPORTED | SUPPORTED | TDP rated at 200 watts. |

### case_12_adversarial_authoritative_conflict_smartwatch
| match | true | predicted | claim |
|---|---|---|---|
| Y | CONTRADICTED | CONTRADICTED | Battery lasts up to 7 days on a single charge. |
| Y | SUPPORTED | SUPPORTED | Water resistant up to 50 meters (5 ATM). |

## Run protocol note (decisions/0003 Ruling 4)

This is the first and only official run executed this session — no rerun
was needed. Published as scored, per the unchanged 2026-07-18 eval-parity
contract: this result stands regardless of verdict.
