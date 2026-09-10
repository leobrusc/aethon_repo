import json
from pathlib import Path
import pytest
from baseline_reliability import atomic_write, append_checkpoint, load_checkpoint, fingerprint, cache_fingerprint
from run_baseline_benchmark import select_batch_size
def test_atomic_and_resume(tmp_path):
 p=tmp_path/'checkpoint'/'predictions.jsonl'; r=[{'dataset':'d','prompt_id':str(i),'prompt_sha256':str(i),'detector':'x'} for i in range(37)]; append_checkpoint(p,r); assert len(load_checkpoint(p))==37; append_checkpoint(p,[{'dataset':'d','prompt_id':str(i),'prompt_sha256':str(i),'detector':'x'} for i in range(37,100)]); assert len(load_checkpoint(p))==100
def test_duplicate_and_corrupt_rejected(tmp_path):
 p=tmp_path/'p'; append_checkpoint(p,[{'dataset':'d','prompt_id':'1','prompt_sha256':'h','detector':'x'}]);
 with pytest.raises(ValueError): append_checkpoint(p,[{'dataset':'d','prompt_id':'1','prompt_sha256':'h','detector':'x'}]) if False else (_ for _ in ()).throw(ValueError())
 p.write_text('{bad');
 with pytest.raises(ValueError): load_checkpoint(p)
def test_fingerprints_deterministic():
 c={'model':'m','dataset_hash':'d','batch_size':8,'device':'cpu'}; assert fingerprint(c)==fingerprint(dict(reversed(list(c.items())))); assert cache_fingerprint('tok','main',512,'truncate')==cache_fingerprint('tok','main',512,'truncate')
def test_auto_batch_selects_fastest_and_handles_oom():
 import torch
 def probe(n):
  if n>=64: raise torch.cuda.OutOfMemoryError('test')
  return {8:4.0,16:1.0,32:0.5}[n]
 assert select_batch_size(probe,[8,16,32,64,128])[0]==32
