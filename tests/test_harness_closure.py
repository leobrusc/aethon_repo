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
def test_latency_validator_callable():
 from close_harness import validate_latency_summary
 p=Path('results/tables/smoke_complete/latency_summary.csv')
 if p.exists(): assert validate_latency_summary(p)
def test_telemetry_validator_callable():
 from close_harness import validate_telemetry_overhead
 p=Path('results/tables/smoke_complete/telemetry_overhead.json')
 if p.exists(): assert validate_telemetry_overhead(p)
def test_layer_summary_arithmetic():
 from close_harness import build_layer_overlap_summary
 p=Path('results/tables/smoke_complete/layer_overlap.csv')
 if p.exists(): assert 'total_both_hit' in build_layer_overlap_summary(p,Path('results/diagnostics/_test_layer.json'))
def test_false_positive_summary_callable():
 from close_harness import build_false_positive_summary
 p=Path('results/tables/smoke_complete/false_positive_summary.csv')
 if p.exists(): assert 'highest_B3_FPR_dataset' in build_false_positive_summary(p,Path('results/diagnostics/_test_fp.json'))
def test_readiness_function_all_flags():
 from close_harness import compute_harness_readiness
 assert compute_harness_readiness({'a':True,'b':True},Path('results/diagnostics/_test_ready.json'))['harness_ready_for_full_benchmark']
def test_layer_overlap_producer_synthetic(tmp_path):
 import pandas as pd
 from close_harness import build_layer_overlap_from_per_prompt
 rows=[]
 for i,(y,h,p) in enumerate([(1,1,.2),(1,0,.8),(1,1,.8),(1,0,.2),(0,1,.2),(0,0,.8),(0,1,.8),(0,0,.2)]):
  for c in ['B2','B3']: rows.append({'prompt_id':i,'dataset':'synthetic','ground_truth':y,'condition':c,'heuristic_H':h,'calibrated_probability_p':p,'threshold_tau':.5})
 out,s=build_layer_overlap_from_per_prompt(tmp_path/'p.csv',tmp_path/'o.csv',tmp_path/'s.json') if False else (None,None)
 pd.DataFrame(rows).to_csv(tmp_path/'p.csv',index=False);out,s=build_layer_overlap_from_per_prompt(tmp_path/'p.csv',tmp_path/'o.csv',tmp_path/'s.json');r=out.iloc[0];assert [r.L1_only_hits,r.L2_only_hits,r.both_hit,r.both_miss]==[1,1,1,1];assert r.delta_tp_B3_vs_B2==1 and r.delta_fp_B3_vs_B2==1
