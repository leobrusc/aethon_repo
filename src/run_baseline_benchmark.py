"""Production-safe resumable baseline runner."""
from __future__ import annotations
import argparse,hashlib,json,signal,sys
from pathlib import Path
import pandas as pd
from baseline_detectors import ProtectAIV2
from baseline_reliability import fingerprint,append_checkpoint,load_checkpoint,write_state,atomic_write
from dataset_loader import load_dataset
DS=['prompt_injections_test','prompt_injection_core','jailbreakbench_behaviors','wildjailbreak_eval','notinject'];PROV={d:'source_ground_truth' for d in DS};PROV['notinject']='benchmark_policy_label'
STOP=False
def select_batch_size(probe, candidates):
    """Return highest-throughput successful candidate; probe(batch)->seconds."""
    import torch
    results=[]
    for size in candidates:
        try:
            elapsed=float(probe(size)); results.append((size,elapsed))
        except (torch.cuda.OutOfMemoryError, MemoryError):
            if torch.cuda.is_available(): torch.cuda.empty_cache()
    if not results: raise RuntimeError('no auto-batch candidate succeeded')
    return max(results,key=lambda x:x[0]/x[1])[0], results
def _signal(*_):
 global STOP; STOP=True
def run_records(df,detector,run,run_id,fp,batch_size,checkpoint_every,smoke=False):
 ck=run/'checkpoint'/'predictions.jsonl'; st=run/'state.json'; done=load_checkpoint(ck); pending=[]
 def flush(status='PARTIAL'):
  nonlocal done,pending
  if pending: append_checkpoint(ck,pending); pending=[]
  done=load_checkpoint(ck); write_state(st,{'run_id':run_id,'status':status,'expected_unique_records':len(df),'completed_unique_records':len(done),'remaining_records':len(df)-len(done),'duplicates':0,'fingerprint':fp,'last_checkpoint':str(ck)})
 for ds,g in df.groupby('dataset'):
  missing=[]
  for r in g.itertuples(index=False):
   h=hashlib.sha256(str(r.prompt_text).encode()).hexdigest(); key=(ds,str(r.prompt_id),h,'ProtectAI v2')
   if key not in done: missing.append((r,h))
  for i in range(0,len(missing),batch_size):
   if STOP: flush(); return False
   batch=missing[i:i+batch_size]; vals=detector.predict_batch([str(x[0].prompt_text) for x in batch])
   for (r,h),v in zip(batch,vals): pending.append({'run_id':run_id,'dataset':ds,'prompt_id':str(r.prompt_id),'prompt_sha256':h,'true_label':int(r.label),'label_provenance':PROV[ds],'detector':'ProtectAI v2','score':v[0],'prediction':v[1],'binary_decision_method':'argmax_softmax','token_count':v[3],'truncated':bool(v[2]),'device':str(detector.device),'dtype':'float32','batch_size':batch_size})
   if len(pending)>=checkpoint_every: flush()
  flush()
 return True
def main():
 p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--output-root',default='results/revision/baselines');p.add_argument('--device',choices=['auto','cpu','cuda'],default='auto');p.add_argument('--batch-size',type=int,default=16);p.add_argument('--auto-batch',action='store_true');p.add_argument('--checkpoint-every',type=int,default=100);p.add_argument('--resume',action='store_true');p.add_argument('--smoke',action='store_true');a=p.parse_args(); run=Path(a.output_root)/'runs'/a.run_id
 for x in ('checkpoint','final','logs'): (run/x).mkdir(parents=True,exist_ok=True)
 frames=[]
 for dataset_name in DS:
  frame=load_dataset(dataset_name).copy(); frame['dataset']=dataset_name; frames.append(frame)
 df=pd.concat(frames,ignore_index=True)
 required={'prompt_id','prompt_text','label','source','dataset'}
 missing=required-set(df.columns)
 if missing: raise ValueError(f'dataset schema missing required columns: {sorted(missing)}')
 if a.smoke: df=df.groupby('dataset',group_keys=False).head(20).reset_index(drop=True)
 cfg={'detector':'protectai/deberta-v3-base-prompt-injection-v2','model_revision':'main','tokenizer_revision':'main','datasets':DS,'prompt_count':len(df),'label_mapping':PROV,'decision_semantics':'argmax softmax','max_length':512,'truncation':'truncate'}; fp=fingerprint(cfg)
 if a.resume:
  if not (run/'manifest.json').exists(): raise SystemExit('--resume requires existing run-id')
  old=json.loads((run/'manifest.json').read_text());
  if old.get('fingerprint')!=fp: raise SystemExit('incompatible scientific fingerprint; refusing resume')
 elif (run/'manifest.json').exists(): raise SystemExit('run-id exists; use --resume')
 else: (run/'manifest.json').write_text(json.dumps({**cfg,'run_id':a.run_id,'fingerprint':fp},indent=2)); write_state(run/'state.json',{'run_id':a.run_id,'status':'CREATED','expected_unique_records':len(df),'completed_unique_records':0,'remaining_records':len(df),'duplicates':0,'fingerprint':fp,'last_checkpoint':None})
 signal.signal(signal.SIGINT,_signal); signal.signal(signal.SIGTERM,_signal)
 try: d=ProtectAIV2(device=a.device); done=load_checkpoint(run/'checkpoint'/'predictions.jsonl'); print(f'[RESUME] total={len(df)} completed={len(done)} remaining={len(df)-len(done)}'); write_state(run/'state.json',{'run_id':a.run_id,'status':'RUNNING','expected_unique_records':len(df),'completed_unique_records':len(done),'remaining_records':len(df)-len(done),'duplicates':0,'fingerprint':fp,'last_checkpoint':None}); ok=run_records(df,d,run,a.run_id,fp,a.batch_size,a.checkpoint_every,a.smoke)
 except KeyboardInterrupt: raise
 except Exception as exc:
  done=load_checkpoint(run/'checkpoint'/'predictions.jsonl'); write_state(run/'state.json',{'run_id':a.run_id,'status':'FAILED','expected_unique_records':len(df),'completed_unique_records':len(done),'remaining_records':len(df)-len(done),'duplicates':0,'fingerprint':fp,'last_checkpoint':str(run/'checkpoint'/'predictions.jsonl'),'error':f'{type(exc).__name__}: {exc}'}); raise
 if not ok:return 143
 rows=list(load_checkpoint(run/'checkpoint'/'predictions.jsonl').values()); keys={(r['dataset'],r['prompt_id'],r['prompt_sha256'],r['detector']) for r in rows}
 if len(rows)!=len(df) or len(keys)!=len(df): write_state(run/'state.json',{'run_id':a.run_id,'status':'FAILED','expected_unique_records':len(df),'completed_unique_records':len(rows),'remaining_records':max(0,len(df)-len(rows)),'duplicates':len(rows)-len(keys),'fingerprint':fp,'last_checkpoint':str(run/'checkpoint'/'predictions.jsonl')}); raise SystemExit('finalization integrity failure')
 atomic_write(run/'final'/'baseline_per_prompt.csv',pd.DataFrame(rows).to_csv(index=False)); write_state(run/'state.json',{'run_id':a.run_id,'status':'COMPLETE','expected_unique_records':len(df),'completed_unique_records':len(rows),'remaining_records':0,'duplicates':0,'fingerprint':fp,'last_checkpoint':str(run/'checkpoint'/'predictions.jsonl')})
if __name__=='__main__':main()
