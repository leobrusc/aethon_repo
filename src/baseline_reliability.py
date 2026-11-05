"""Crash-safe state and cache primitives for long-running baseline jobs."""
from __future__ import annotations
import hashlib,json,os,tempfile
from pathlib import Path

SCHEMA_VERSION=1
def fingerprint(config):
    scientific={k:config[k] for k in sorted(config) if k not in {'batch_size','device','run_id'}}
    return hashlib.sha256(json.dumps(scientific,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def atomic_write(path:Path,text:str):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8',newline='') as f:f.write(text);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    except Exception:
        try: os.unlink(tmp)
        except OSError: pass
        raise
def write_state(path, state): atomic_write(Path(path),json.dumps(state,sort_keys=True,indent=2))
def read_state(path):
    try:return json.loads(Path(path).read_text(encoding='utf-8'))
    except Exception as e: raise ValueError(f'corrupt checkpoint state: {path}') from e
def append_checkpoint(path, records):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True); tmp=p.with_suffix('.tmp')
    existing=p.read_text(encoding='utf-8') if p.exists() else ''
    with tmp.open('w',encoding='utf-8',newline='') as f:
        f.write(existing)
        for r in records:f.write(json.dumps(r,sort_keys=True)+'\n')
        f.flush();os.fsync(f.fileno())
    os.replace(tmp,p)
def load_checkpoint(path):
    p=Path(path)
    if not p.exists():return {}
    out={}
    try:
        for line in p.read_text(encoding='utf-8').splitlines():
            r=json.loads(line); key=(r['dataset'],r['prompt_id'],r['prompt_sha256'],r['detector'])
            if key in out: raise ValueError('duplicate checkpoint key')
            out[key]=r
    except Exception as e: raise ValueError(f'corrupt checkpoint: {p}') from e
    return out
def cache_fingerprint(tokenizer_id,revision,max_length,truncation):
    return hashlib.sha256(json.dumps({'tokenizer':tokenizer_id,'revision':revision,'max_length':max_length,'truncation':truncation},sort_keys=True).encode()).hexdigest()[:24]
