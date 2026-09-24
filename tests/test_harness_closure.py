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
