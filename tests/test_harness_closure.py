import json
from pathlib import Path
def test_baseline_status_schema():
 p=Path('results/aggregated/baseline_status.json')
 if p.exists():
  d=json.loads(p.read_text());assert set(d)>= {'llama_prompt_guard','protectai_deberta'}
def test_readiness_smoke_is_false():
 p=Path('results/aggregated/detector_publication_readiness.json')
 if p.exists(): assert json.loads(p.read_text()).get('publication_ready') is False
def test_existing_duplicate_summary_has_pair_fields():
 p=Path('results/diagnostics/cross_split_duplicate_summary.json')
 if p.exists():
  d=json.loads(p.read_text());assert 'collision_pair_rows' in d and 'unique_colliding_hashes' in d
def test_near_duplicate_summary_schema():
 p=Path('results/diagnostics/cross_split_near_duplicate_summary.json')
 if p.exists():
  d=json.loads(p.read_text()); assert d['threshold']>=.98; assert d['pair_rows']>=d['unique_prompt_pairs']
def test_latency_artifact_schema():
 p=Path('results/tables/smoke_complete/latency_summary.csv')
 if p.exists():
  import pandas as pd
  d=pd.read_csv(p); assert set(['B1','B2','B3','B4'])<=set(d.condition); assert {'p50_ms','p95_ms','p99_ms'}<=set(d)
def test_telemetry_arithmetic():
 p=Path('results/tables/smoke_complete/telemetry_overhead.json')
 if p.exists():
  d=json.loads(p.read_text()); assert abs(d['delta_p50_ms']-(d['B4_p50_ms']-d['B3_p50_ms']))<1e-9; assert abs(d['delta_p99_ms']-(d['B4_p99_ms']-d['B3_p99_ms']))<1e-9
def test_scientific_report_disclaimer():
 p=Path('results/diagnostics/smoke_scientific_interpretation.md')
 if p.exists(): assert 'SMOKE TEST' in p.read_text() and 'NOT FOR PUBLICATION' in p.read_text()
def test_readiness_contains_harness_flag():
 p=Path('results/aggregated/detector_publication_readiness.json')
 if p.exists(): assert 'harness_ready_for_full_benchmark' in json.loads(p.read_text())
def test_latency_percentile_ordering():
 import pandas as pd
 p=Path('results/tables/smoke_complete/latency_summary.csv')
 if p.exists():
  for _,r in pd.read_csv(p).iterrows(): assert r.p50_ms<=r.p95_ms<=r.p99_ms
def test_required_scientific_report_sections():
 p=Path('results/diagnostics/smoke_scientific_interpretation.md')
 if p.exists():
  text=p.read_text(); assert 'SMOKE TEST' in text
def test_near_duplicate_rows_threshold():
 import pandas as pd
 p=Path('results/diagnostics/cross_split_near_duplicates.csv')
 if p.exists() and p.stat().st_size>0: assert (pd.read_csv(p).cosine_similarity>=.98).all()
def test_baseline_status_nonrun_no_claims():
 p=Path('results/aggregated/baseline_status.json')
 if p.exists():
  d=json.loads(p.read_text()); assert all(v.get('status') in {'not_run','gated','unavailable','load_failed','available','sanity_passed'} for v in d.values())
def test_domain_shift_artifact_if_present():
 p=Path('results/diagnostics/benign_domain_shift.csv')
 if p.exists(): assert {'prompt_injections_test','prompt_injection_core','jailbreakbench_behaviors','notinject'}<=set(__import__('pandas').read_csv(p).dataset)
