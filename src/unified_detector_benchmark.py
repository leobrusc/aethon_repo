"""Leakage-free detector-only B0-B4 benchmark and paper exports."""
from __future__ import annotations
import hashlib,json,platform,subprocess,time
from pathlib import Path
import numpy as np,pandas as pd,joblib,sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from aethon_heuristic import batch_detect
from aethon_calibrated_cascade import ValidationCalibrator,select_threshold,operational_decision
from dataset_loader import load_dataset,get_dataset_metadata
DATASET_ROLES={'train':['prompt_injections_train'],'validation':['prompt_injections_test'],'final_test':['prompt_injection_core','jailbreakbench_behaviors','cyberseceval_prompt_injection','notinject']}
CONDITIONS=['B0','B1','B2','B3','B4']
def _hash(x): return hashlib.sha256(str(x).encode()).hexdigest()
def train_and_calibrate(method='sigmoid',seed=42):
 tr=load_dataset(DATASET_ROLES['train'][0]); va=load_dataset(DATASET_ROLES['validation'][0]); vec=TfidfVectorizer(max_features=5000); X=vec.fit_transform(tr.prompt_text); lr=LogisticRegression(max_iter=1000,random_state=seed).fit(X,tr.label); q=lr.predict_proba(vec.transform(va.prompt_text))[:,1]; cal=ValidationCalibrator(method).fit(q,va.label); p=cal.predict(q); tau=select_threshold(p,va.label); return vec,lr,cal,tau,{'method':method,'tau':tau,'validation_count':len(va),'brier_before':float(np.mean((q-va.label)**2)),'brier_after':float(np.mean((p-va.label)**2))}
def evaluate_smoke(output_root='results',method='sigmoid',limit=20,seed=42,run_id='smoke'):
 vec,lr,cal,tau,cal_report=train_and_calibrate(method,seed); frames=[]
 for ds in DATASET_ROLES['final_test']:
  f=load_dataset(ds).copy();f['dataset']=ds;frames.append(f.groupby('dataset',group_keys=False).head(limit))
 final=pd.concat(frames,ignore_index=True); q=lr.predict_proba(vec.transform(final.prompt_text))[:,1];p=cal.predict(q);h=np.asarray(batch_detect(final.prompt_text.tolist()),int);s,d=operational_decision(h,p,tau); rows=[]
 for i,r in enumerate(final.itertuples(index=False)):
  for c in CONDITIONS:
   if c=='B0': score=None;dec=0
   elif c=='B1':score=float(h[i]);dec=int(h[i])
   elif c=='B2':score=float(p[i]);dec=int(p[i]>=tau)
   else:score=float(s[i]);dec=int(d[i])
   rows.append({'prompt_id':str(r.prompt_id),'source':str(r.source),'dataset':r.dataset,'ground_truth':int(r.label),'condition':c,'heuristic_H':int(h[i]),'raw_probability_q':float(q[i]),'calibrated_probability_p':float(p[i]),'cascade_score_s':score,'threshold_tau':tau,'decision':dec,'latency_ms':None,'calibration_method':method,'epsilon':1.2,'run_id':run_id})
 out=Path(output_root);tab=out/'tables'/run_id;tab.mkdir(parents=True,exist_ok=True);agg=out/'aggregated';agg.mkdir(parents=True,exist_ok=True);pd.DataFrame(rows).to_csv(tab/'per_prompt.csv',index=False)
 metrics=[]
 for c,g in pd.DataFrame(rows).groupby('condition'):
  vals=[]
  for ds,x in g.groupby('dataset'):
   y=x.ground_truth.to_numpy(); z=x.decision.to_numpy(); score=x.cascade_score_s.to_numpy() if c in {'B3','B4'} else x.calibrated_probability_p.to_numpy() if c=='B2' else None
   pos=y.sum();neg=len(y)-pos; vals.append({'dataset':ds,'tpr':float(((z==1)&(y==1)).sum()/pos) if pos else None,'fpr':float(((z==1)&(y==0)).sum()/neg) if neg else None,'auroc':float(roc_auc_score(y,score)) if score is not None and pos and neg else None})
  metrics.append({'condition':c,'tpr':np.nanmean([v['tpr'] for v in vals if v['tpr'] is not None]),'fpr':np.nanmean([v['fpr'] for v in vals if v['fpr'] is not None]),'fpr_notinject':next((v['fpr'] for v in vals if v['dataset']=='notinject'),None),'auroc':np.nanmean([v['auroc'] for v in vals if v['auroc'] is not None]) if any(v['auroc'] is not None for v in vals) else None})
 m=pd.DataFrame(metrics);m.to_csv(agg/'paper_metrics.csv',index=False);json.dump({'publication_ready':False,'dataset_roles':DATASET_ROLES,'calibration':cal_report,'conditions':m.to_dict('records')},(agg/'paper_metrics.json').open('w'),indent=2)
 pd.DataFrame([cal_report]).to_csv(tab/'calibration_report.csv',index=False);json.dump(cal_report,(tab/'calibration_report.json').open('w'),indent=2)
 for name,cols in [('b0_b4_ablation.tex',['condition','tpr','fpr','fpr_notinject','auroc']),('tpr_by_dataset.tex',['condition'])]:
  (tab/name).write_text(m.to_latex(index=False,escape=True))
 return m,cal_report
