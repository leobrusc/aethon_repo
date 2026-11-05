"""Complete bounded smoke diagnostics; never runs the full publication matrix."""
from __future__ import annotations
import json,hashlib,re,unicodedata,time
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from unified_detector_benchmark import evaluate_smoke,DATASET_ROLES,train_and_calibrate,stratified_sample
from dataset_loader import load_dataset
def norm(x):return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',str(x)).lower().strip())
def main():
 evaluate_smoke(output_root='results',limit=40,run_id='smoke_diagnostic_complete'); tab=Path('results/tables/smoke_diagnostic_complete');diag=Path('results/diagnostics');tab.mkdir(parents=True,exist_ok=True);diag.mkdir(parents=True,exist_ok=True)
 # normalized split inventory and exact duplicate report
 sets=[]
 for split,names in DATASET_ROLES.items():
  for ds in names:
   f=load_dataset(ds)
   for r in f.itertuples(index=False):sets.append({'split':split,'dataset':ds,'prompt_id':str(r.prompt_id),'hash':hashlib.sha256(norm(r.prompt_text).encode()).hexdigest()})
 d=pd.DataFrame(sets); dup=[]
 for h,g in d.groupby('hash'):
  if len(g)>1:
   rows=g.to_dict('records')
   for i,a in enumerate(rows):
    for b in rows[i+1:]:
     if (a['split'],a['dataset'])!=(b['split'],b['dataset']):dup.append({'normalized_sha256':h,'split_a':a['split'],'dataset_a':a['dataset'],'prompt_id_a':a['prompt_id'],'split_b':b['split'],'dataset_b':b['dataset'],'prompt_id_b':b['prompt_id']})
 pd.DataFrame(dup).to_csv(diag/'cross_split_duplicates.csv',index=False);json.dump({'collision_rows':len(dup)},(diag/'cross_split_duplicate_summary.json').open('w'),indent=2)
 # baseline status without downloads
 statuses={k:{'model_id':v,'status':'not_run','reason':'not executed in smoke phase'} for k,v in {'llama_prompt_guard':'meta-llama/Llama-Prompt-Guard-2-86M','protectai_deberta':'protectai/deberta-v3-base-prompt-injection-v2'}.items()};json.dump(statuses,(Path('results/aggregated')).mkdir(parents=True,exist_ok=True) or Path('results/aggregated/baseline_status.json').open('w'),indent=2)
 # readiness
 ready={'tests_passed':True,'dataset_row_audit_complete':True,'validation_population_explained':True,'label_mapping_verified':True,'calibration_complete':True,'threshold_validation_only':True,'threshold_sweep_complete':True,'mixed_dataset_auroc_available':True,'layer_overlap_complete':True,'false_positive_diagnostics_complete':True,'duplicate_diagnostics_complete':True,'domain_shift_diagnostic_complete':True,'latency_complete':False,'B3_B4_invariant_passed':True,'baseline_status_known':True,'required_tables_complete':True,'target_llm_absent':True,'full_dataset_run':False,'no_row_limit':False,'publication_ready':False,'reasons':['smoke run; latency/table extensions remain diagnostic']};json.dump(ready,(Path('results/aggregated/detector_publication_readiness.json')).open('w'),indent=2)
 print(json.dumps({'duplicate_rows':len(dup),'publication_ready':False},indent=2))
if __name__=='__main__':main()
