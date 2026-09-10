"""Crash-safe, resumable ProtectAI benchmark runner."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import pandas as pd
from baseline_detectors import ProtectAIV2
from baseline_reliability import fingerprint,append_checkpoint,load_checkpoint,write_state,atomic_write
from dataset_loader import load_dataset
DS=['prompt_injections_test','prompt_injection_core','jailbreakbench_behaviors','wildjailbreak_eval','notinject']; PROV={x:'source_ground_truth' for x in DS};PROV['notinject']='benchmark_policy_label'
def main():
 p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--output-root',default='results/revision/baselines');p.add_argument('--device',choices=['auto','cpu','cuda'],default='auto');p.add_argument('--batch-size',type=int,default=16);p.add_argument('--checkpoint-every',type=int,default=100);p.add_argument('--resume',action='store_true');p.add_argument('--smoke',action='store_true');a=p.parse_args();run=Path(a.output_root)/'runs'/a.run_id;ck=run/'checkpoint'/'predictions.jsonl'; mf=run/'manifest.json';st=run/'state.json';
 for x in [run/'checkpoint',run/'final',run/'logs']:x.mkdir(parents=True,exist_ok=True)
 fs={d:load_dataset(d) for d in DS};df=pd.concat(fs.values(),ignore_index=True);df=df.head(100) if a.smoke else df; cfg={'detector':'protectai/deberta-v3-base-prompt-injection-v2','model_revision':'main','tokenizer_revision':'main','datasets':DS,'prompt_count':len(df),'label_mapping':PROV,'decision_semantics':'argmax softmax','max_length':512,'truncation':'truncate'};fp=fingerprint(cfg)
 if a.resume:
  if not mf.exists():raise SystemExit('--resume requires existing run-id'); old=json.loads(mf.read_text());
  if old.get('fingerprint')!=fp:raise SystemExit('incompatible scientific fingerprint')
 elif mf.exists():raise SystemExit('run-id exists; use --resume')
 else:mf.write_text(json.dumps({**cfg,'run_id':a.run_id,'fingerprint':fp},indent=2));write_state(st,{'run_id':a.run_id,'status':'CREATED','expected_unique_records':len(df),'completed_unique_records':0,'remaining_records':len(df),'duplicates':0,'fingerprint':fp})
 done=load_checkpoint(ck);print(f'[RESUME] total={len(df)} completed={len(done)} remaining={len(df)-len(done)}');d=ProtectAIV2(device=a.device);pending=[]
 try:
  for ds,g in df.groupby('dataset'):
   for r in g.itertuples(index=False):
    key=(ds,str(r.prompt_id),hashlib.sha256(str(r.prompt_text).encode()).hexdigest(),'ProtectAI v2')
    if key in done:continue
    v=d.predict(str(r.prompt_text));pending.append({'run_id':a.run_id,'dataset':ds,'prompt_id':str(r.prompt_id),'prompt_sha256':key[2],'true_label':int(r.label),'label_provenance':PROV[ds],'detector':'ProtectAI v2','score':v.score,'prediction':v.prediction,'binary_decision_method':'argmax_softmax','token_count':v.token_count,'truncated':v.truncated,'device':str(d.device),'dtype':'float32','batch_size':a.batch_size})
    if len(pending)>=a.checkpoint_every:append_checkpoint(ck,pending);done=load_checkpoint(ck);pending=[];write_state(st,{'run_id':a.run_id,'status':'PARTIAL','expected_unique_records':len(df),'completed_unique_records':len(done),'remaining_records':len(df)-len(done),'duplicates':0,'fingerprint':fp,'last_checkpoint':str(ck)})
 except KeyboardInterrupt:
  if pending:append_checkpoint(ck,pending)
  write_state(st,{'run_id':a.run_id,'status':'PARTIAL','expected_unique_records':len(df),'completed_unique_records':len(load_checkpoint(ck)),'remaining_records':0,'duplicates':0,'fingerprint':fp,'last_checkpoint':str(ck)});return
 if pending:append_checkpoint(ck,pending)
 rows=list(load_checkpoint(ck).values());atomic_write(run/'final'/'baseline_per_prompt.csv',pd.DataFrame(rows).to_csv(index=False));write_state(st,{'run_id':a.run_id,'status':'COMPLETE','expected_unique_records':len(df),'completed_unique_records':len(rows),'remaining_records':len(df)-len(rows),'duplicates':0,'fingerprint':fp,'last_checkpoint':str(ck)})
if __name__=='__main__':main()
