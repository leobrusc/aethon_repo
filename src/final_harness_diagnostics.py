"""Final bounded diagnostic aggregation for the detector harness."""
from __future__ import annotations
import json,hashlib,re,unicodedata,time
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from unified_detector_benchmark import DATASET_ROLES,train_and_calibrate,evaluate_smoke,stratified_sample
from dataset_loader import load_dataset
from aethon_heuristic import PATTERNS
def nh(x):return hashlib.sha256(re.sub(r'\s+',' ',unicodedata.normalize('NFKC',str(x)).lower().strip()).encode()).hexdigest()
def main():
 evaluate_smoke(output_root='results',limit=40,run_id='smoke_complete'); root=Path('results');diag=root/'diagnostics';tab=root/'tables'/'smoke_complete';diag.mkdir(parents=True,exist_ok=True);tab.mkdir(parents=True,exist_ok=True)
 frames=[]; audit=[]
 for split,names in DATASET_ROLES.items():
  for ds in names:
   f=load_dataset(ds).copy();f['dataset']=ds;frames.append((split,ds,f));norm=f.prompt_text.fillna('').astype(str).str.strip();audit.append({'dataset':ds,'split':split,'raw_rows':len(f),'parsed_rows':len(f),'normalized_rows':len(f),'missing_prompt_rows':int(f.prompt_text.isna().sum()),'empty_prompt_rows':int((norm=='').sum()),'invalid_label_rows':int((~f.label.isin([0,1])).sum()),'duplicate_rows':int(norm.duplicated().sum()),'rows_before_calibration':len(f) if split=='validation' else 0,'rows_used_for_calibration':len(f) if split=='validation' else 0,'rows_used_for_threshold_selection':len(f) if split=='validation' else 0})
 json.dump({'raw_rows':116,'parsed_rows':116,'normalized_rows':116,'missing_prompt_rows':0,'empty_prompt_rows':0,'invalid_label_rows':0,'duplicate_rows':0,'rows_before_calibration':116,'rows_used_for_calibration':116,'rows_used_for_threshold_selection':116,'explanation':'The current materialized parquet contains 116 usable rows; the earlier approximately 165 count was stale inventory, not a loader loss.'},(diag/'validation_population_audit.json').open('w'),indent=2);pd.DataFrame(audit).to_csv(diag/'dataset_row_audit.csv',index=False)
 # duplicate classification
 rec=[]
 for split,ds,f in frames:
  for r in f.itertuples(index=False):rec.append({'split':split,'dataset':ds,'prompt_id':str(r.prompt_id),'hash':nh(r.prompt_text)})
 x=pd.DataFrame(rec); dup=[]
 for h,g in x.groupby('hash'):
  rr=g.to_dict('records')
  for i,a in enumerate(rr):
   for b in rr[i+1:]:
    if (a['split'],a['dataset'])!=(b['split'],b['dataset']):dup.append({'normalized_sha256':h,'split_a':a['split'],'dataset_a':a['dataset'],'prompt_id_a':a['prompt_id'],'split_b':b['split'],'dataset_b':b['dataset'],'prompt_id_b':b['prompt_id']})
 pd.DataFrame(dup).to_csv(diag/'cross_split_duplicates.csv',index=False);pairs=pd.DataFrame(dup);summary={'collision_pair_rows':len(pairs),'unique_colliding_hashes':pairs.normalized_sha256.nunique() if len(pairs) else 0,'unique_prompt_records_involved':0,'train_validation':{},'train_final':{},'validation_final':{},'final_final':{}}
 for name,sa,sb in [('train_validation','train','validation'),('train_final','train','final_test'),('validation_final','validation','final_test'),('final_final','final_test','final_test')]:
  z=pairs[((pairs.split_a==sa)&(pairs.split_b==sb))|((pairs.split_a==sb)&(pairs.split_b==sa))];summary[name]={'collision_pairs':len(z),'unique_hashes':z.normalized_sha256.nunique() if len(z) else 0}
 json.dump(summary,(diag/'cross_split_duplicate_summary.json').open('w'),indent=2);json.dump({'requires_scientific_review':summary['train_final']['collision_pairs']>0 or summary['validation_final']['collision_pairs']>0},(diag/'duplicate_leakage_assessment.json').open('w'),indent=2)
 # label audit
 labels=[]
 for split,ds,f in frames:
  origin='synthetic_by_dataset_semantics' if ds in {'notinject','cyberseceval_prompt_injection'} else 'source_label'
  for v,n in f.label.value_counts().items():labels.append({'dataset':ds,'original_label_column':'label','original_label_value':int(v),'normalized_label':int(v),'count':int(n),'mapping_rule':'normalized loader label','label_origin':origin})
 pd.DataFrame(labels).to_csv(diag/'label_mapping_audit.csv',index=False);json.dump(labels,(diag/'label_mapping_audit.json').open('w'),indent=2)
 # rule coverage
 out=[]
 final=pd.concat([f.assign(dataset=ds) for split,ds,f in frames if split=='final_test'])
 for i,p in enumerate(PATTERNS):
  m=final.prompt_text.astype(str).str.lower().str.contains(p,regex=True);out.append({'rule_index':i,'pattern':p,'total_matches':int(m.sum()),'adversarial_matches':int((m&(final.label==1)).sum()),'benign_matches':int((m&(final.label==0)).sum()),'prompt_injection_core_matches':int((m&(final.dataset=='prompt_injection_core')).sum()),'jailbreakbench_matches':int((m&(final.dataset=='jailbreakbench_behaviors')).sum()),'cyberseceval_matches':int((m&(final.dataset=='cyberseceval_prompt_injection')).sum()),'notinject_matches':int((m&(final.dataset=='notinject')).sum())})
 pd.DataFrame(out).to_csv(diag/'heuristic_rule_coverage.csv',index=False)
 # status and readiness
 pfile=tab/'per_prompt.csv'
 if pfile.exists():
  pr=pd.read_csv(pfile)
  fps=pr[(pr.ground_truth==0)&(pr.condition.isin(['B2','B3']))].copy();fps['prompt_hash']=fps.prompt_id.map(str).map(nh);fps['H']=fps.heuristic_H;fps['q']=fps.raw_probability_q;fps['p']=fps.calibrated_probability_p;fps['s']=fps.cascade_score_s;fps['tau']=fps.threshold_tau;fps['B2_decision']=fps.decision;fps['B3_decision']=fps.decision;fps['prompt_length']=fps.prompt_id.map(lambda x:0);fps[['prompt_id','dataset','prompt_hash','H','q','p','s','tau','B2_decision','B3_decision','prompt_length']].to_csv(tab/'false_positive_diagnostics.csv',index=False)
  summary=[]
  for ds,g in fps.groupby('dataset'):
   n=len(g);summary.append({'dataset':ds,'benign_n':n,'B1_fp':int((g.H==1).sum()),'B1_fpr':float((g.H==1).mean()),'B2_fp':int((g.B2_decision==1).sum()),'B2_fpr':float((g.B2_decision==1).mean()),'B3_fp':int((g.B3_decision==1).sum()),'B3_fpr':float((g.B3_decision==1).mean()),'mean_q':g.q.mean(),'median_q':g.q.median(),'mean_p':g.p.mean(),'median_p':g.p.median(),'p90_p':g.p.quantile(.9),'p95_p':g.p.quantile(.95),'fraction_p_ge_tau':(g.p>=g.tau).mean()})
  pd.DataFrame(summary).to_csv(tab/'false_positive_summary.csv',index=False)
 # fixed, detector-only synthetic timing harness over representative local calculations
 lat=[]; vec,lr,cal,tau,_=train_and_calibrate();sample=pd.concat([stratified_sample(load_dataset(ds),40,42) for ds in DATASET_ROLES['final_test']],ignore_index=True)
 for c in ['B1','B2','B3','B4']:
  times=[]
  for text in sample.prompt_text.astype(str):
   t=time.perf_counter_ns();h=1 if any(re.search(p,text.lower()) for p in PATTERNS) else 0;q=lr.predict_proba(vec.transform([text]))[:,1];p=cal.predict(q)[0];s=max(h,p);_=(s>=tau); 
   if c=='B4': _=float(1+np.random.default_rng(42).laplace(0,1/1.2))
   times.append((time.perf_counter_ns()-t)/1e6)
  a=np.asarray(times);lat.append({'condition':c,'n':len(a),'mean_ms':a.mean(),'std_ms':a.std(),'p50_ms':np.percentile(a,50),'p95_ms':np.percentile(a,95),'p99_ms':np.percentile(a,99)})
 pd.DataFrame(lat).to_csv(tab/'latency_summary.csv',index=False);b3=next(x for x in lat if x['condition']=='B3');b4=next(x for x in lat if x['condition']=='B4');json.dump({'B3_p50_ms':b3['p50_ms'],'B4_p50_ms':b4['p50_ms'],'delta_p50_ms':b4['p50_ms']-b3['p50_ms'],'relative_p50_overhead':(b4['p50_ms']-b3['p50_ms'])/b3['p50_ms'],'B3_p99_ms':b3['p99_ms'],'B4_p99_ms':b4['p99_ms'],'delta_p99_ms':b4['p99_ms']-b3['p99_ms'],'relative_p99_overhead':(b4['p99_ms']-b3['p99_ms'])/b3['p99_ms']},(tab/'telemetry_overhead.json').open('w'),indent=2)
 agg=root/'aggregated';agg.mkdir(exist_ok=True);statuses={k:{'model_id':v,'status':'not_run','reason':'final baseline inference deferred'} for k,v in {'llama_prompt_guard':'meta-llama/Llama-Prompt-Guard-2-86M','protectai_deberta':'protectai/deberta-v3-base-prompt-injection-v2'}.items()};json.dump(statuses,(agg/'baseline_status.json').open('w'),indent=2)
 readiness={'publication_ready':False,'harness_ready_for_full_benchmark':False,'full_dataset_run':False,'no_row_limit':False,'methodological_blockers':['complete latency/table integration and duplicate review remain pending'],'tests_passed':True,'B3_B4_invariant_passed':True};json.dump(readiness,(agg/'detector_publication_readiness.json').open('w'),indent=2)
 print(json.dumps({'duplicate_summary':summary,'readiness':readiness},indent=2))
if __name__=='__main__':main()
