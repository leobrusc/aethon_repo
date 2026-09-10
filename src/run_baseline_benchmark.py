"""Batched CPU ProtectAI benchmark (effectiveness and request latency separated)."""
from __future__ import annotations
import argparse,hashlib,json,sys,time
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.metrics import *
from baseline_detectors import ProtectAIV2
from dataset_loader import load_dataset
DS=['prompt_injections_test','prompt_injection_core','jailbreakbench_behaviors','wildjailbreak_eval','notinject']; PROV={d:'source_ground_truth' for d in DS}; PROV['notinject']='benchmark_policy_label'
def main():
 p=argparse.ArgumentParser();p.add_argument('--output-root',default='results/revision/baselines');p.add_argument('--smoke',action='store_true');p.add_argument('--device',choices=['auto','cpu','cuda'],default='auto');p.add_argument('--auto-batch',action='store_true');p.add_argument('--resume',action='store_true');p.add_argument('--checkpoint-every',type=int,default=500);p.add_argument('--run-id',default='protectai');a=p.parse_args();o=Path(a.output_root);o.mkdir(parents=True,exist_ok=True)
 try:d=ProtectAIV2(device=a.device)
 except Exception as e:(o/'baseline_manifest.json').write_text(json.dumps({'failures':[{'detector':'ProtectAI v2','error':f'{type(e).__name__}: {e}'}]},indent=2));return 2
 fs={x:load_dataset(x) for x in DS}; allf=pd.concat([fs[x] for x in DS],ignore_index=True); d.warmup(fs['prompt_injections_test'].prompt_text.head(20).tolist()); sub=allf.head(100); base=d.predict_batch(sub.prompt_text.tolist()); inv=[]
 for bs in [1,4,8,16]:
  z=[]
  for i in range(0,len(sub),bs):z+=d.predict_batch(sub.prompt_text.iloc[i:i+bs].tolist())
  inv.append({'batch_size':bs,'prediction_identical':all(x[1]==y[1] for x,y in zip(base,z)),'max_abs_score_diff':max(abs(x[0]-y[0]) for x,y in zip(base,z)),'mean_abs_score_diff':float(np.mean([abs(x[0]-y[0]) for x,y in zip(base,z)]))})
 pd.DataFrame(inv).to_csv(o/'batch_invariance.csv',index=False); probe=[]; ps=allf.head(300).prompt_text.tolist()
 for bs in [4,8,16,32]:
  t=time.perf_counter()
  for i in range(0,len(ps),bs):d.predict_batch(ps[i:i+bs])
  w=time.perf_counter()-t;probe.append({'batch_size':bs,'wall_time_s':w,'prompts_per_second':len(ps)/w,'device':'cpu','threads':__import__('torch').get_num_threads()})
 pd.DataFrame(probe).to_csv(o/'cpu_batch_probe.csv',index=False);bs=int(pd.DataFrame(probe).sort_values('wall_time_s').iloc[0].batch_size); ev=allf.head(100) if a.smoke else allf; rec=[]
 for ds,g in ev.groupby('dataset'):
  v=[]
  for i in range(0,len(g),bs):v+=d.predict_batch(g.prompt_text.iloc[i:i+bs].tolist())
  for r,x in zip(g.itertuples(index=False),v):rec.append({'dataset':ds,'prompt_id':str(r.prompt_id),'prompt_sha256':hashlib.sha256(str(r.prompt_text).encode()).hexdigest(),'true_label':int(r.label),'label_provenance':PROV[ds],'detector':'ProtectAI v2','score':x[0],'prediction':x[1],'latency_mode':'batched_effectiveness','inference_batch_size':bs,'truncated':bool(x[2]),'token_count':x[3]})
 df=pd.DataFrame(rec);df.to_csv(o/('baseline_per_prompt.csv' if a.smoke else 'protectai_full_per_prompt.csv'),index=False);d.warmup(ev.prompt_text.head(20).tolist());r=ev.iloc[np.linspace(0,len(ev)-1,min(500,len(ev))).astype(int)]; l=[d.predict(str(x)).latency_ms for x in r.prompt_text];pd.DataFrame([{'detector':'ProtectAI v2','sample_count':len(l),'mean_latency_ms':np.mean(l),'median_latency_ms':np.median(l),'p95_latency_ms':np.percentile(l,95),'p99_latency_ms':np.percentile(l,99)}]).to_csv(o/'request_latency_protectai.csv',index=False);(o/'baseline_manifest.json').write_text(json.dumps({'device':'cpu','dtype':'float32','batch_size':bs,'warmup_prompts':20,'max_length':512,'python':sys.version,'torch':__import__('torch').__version__,'transformers':__import__('transformers').__version__},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
