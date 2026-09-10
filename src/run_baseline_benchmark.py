"""Shared-protocol evaluation for approved external detectors (CPU, batch=1)."""
from __future__ import annotations
import argparse, hashlib, json, platform, sys
from pathlib import Path
import pandas as pd
from sklearn.metrics import average_precision_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from baseline_detectors import PromptGuard22M, ProtectAIV2
from dataset_loader import load_dataset

DATASETS = ["prompt_injections_test","prompt_injection_core","jailbreakbench_behaviors","wildjailbreak_eval","notinject"]
PROV = {"prompt_injections_test":"source_ground_truth","prompt_injection_core":"source_ground_truth","jailbreakbench_behaviors":"source_ground_truth","wildjailbreak_eval":"source_ground_truth","notinject":"benchmark_policy_label"}
def sha(s): return hashlib.sha256(str(s).encode()).hexdigest()
def metrics(g):
 y=g.true_label.astype(int); p=g.prediction.astype(int); s=g.score.astype(float); pos=int(y.sum()); neg=len(y)-pos
 tn,fp,fn,tp=confusion_matrix(y,p,labels=[0,1]).ravel(); mixed=pos>0 and neg>0
 return dict(rows=len(g),benign=neg,adversarial=pos,auroc=roc_auc_score(y,s) if mixed else None,auprc=average_precision_score(y,s) if mixed else None,precision=precision_score(y,p,zero_division=0) if pos else None,recall=recall_score(y,p,zero_division=0) if pos else None,f1=f1_score(y,p,zero_division=0) if pos else None,fpr=fp/neg if neg else None,tp=tp,tn=tn,fp=fp,fn=fn)
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--output-root',default='results/revision/baselines'); ap.add_argument('--smoke',action='store_true'); args=ap.parse_args(); out=Path(args.output_root); out.mkdir(parents=True,exist_ok=True)
 detectors=[]; failures=[]
 for name,cls in [('Meta Prompt Guard 2 22M',PromptGuard22M),('ProtectAI v2',ProtectAIV2)]:
  try: detectors.append((name,cls()))
  except Exception as e: failures.append({'detector':name,'error':f'{type(e).__name__}: {e}'})
 if not detectors: (out/'baseline_manifest.json').write_text(json.dumps({'failures':failures},indent=2)); print(json.dumps({'failures':failures})); return 2
 rows=[]; datasets=DATASETS
 for name,d in detectors:
  sample=load_dataset('prompt_injections_test').head(20) if args.smoke else load_dataset('prompt_injections_test').head(20)
  d.warmup(sample.prompt_text.tolist())
  for ds in datasets:
   frame=load_dataset(ds); frame=frame.head(20) if args.smoke else frame
   for r in frame.itertuples(index=False):
    q=d.predict(str(r.prompt_text)); rows.append({'dataset':ds,'prompt_id':str(r.prompt_id),'prompt_sha256':sha(r.prompt_text),'true_label':int(r.label),'label_provenance':PROV[ds],'detector':name,'score':q.score,'prediction':q.prediction,'threshold':'argmax','latency_ms':q.latency_ms,'truncated':q.truncated,'token_count':q.token_count})
  print(name,'complete')
 df=pd.DataFrame(rows); df.to_csv(out/'baseline_per_prompt.csv',index=False)
 summary=[]
 for (det,ds),g in df.groupby(['detector','dataset']): summary.append({'detector':det,'dataset':ds,**metrics(g)})
 pd.DataFrame(summary).to_csv(out/'baseline_metrics_by_dataset.csv',index=False)
 manifest={'device':'cpu','dtype':'float32','batch_size':1,'warmup_prompts':20,'max_length':512,'truncation_policy':'tokenizer truncation at 512','python':sys.version,'torch':__import__('torch').__version__,'transformers':__import__('transformers').__version__,'failures':failures}
 (out/'baseline_manifest.json').write_text(json.dumps(manifest,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
