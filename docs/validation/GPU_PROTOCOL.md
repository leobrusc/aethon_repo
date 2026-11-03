# Deferred GPU validation — NOT_RUN locally

Local hardware reports Intel integrated graphics and no NVIDIA adapter or
`nvidia-smi`. The maintained torch build is CPU-only. No CUDA installation or
GPU execution is represented as complete. Run this protocol only on an approved
Linux NVIDIA host, with the same checkout, fixed locks and trusted local weights.
No automatic weight download or paid/cloud provisioning is authorized here.

Before execution, freeze a new run ID, model/revision, snapshot hashes, BF16
support, driver/runtime, selected device and the three inputs from
`tests/fixtures/readiness_smoke.json`. Verify access/licensing separately. Record
operator approval and validate the cache using `review_snapshot` below.

```bash
set -euo pipefail
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
.venv-dev/bin/python scripts/install_security_environment.py requirements/environments/gpu-linux-py312.lock .venv-gpu
.venv-dev/bin/python scripts/audit_security_environment.py requirements/environments/gpu-linux-py312.lock --installed --target-python .venv-gpu/bin/python --output results/validation/gpu-audits
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export AETHON_MODEL_SNAPSHOT=/approved/local/cache/models--meta-llama--Llama-3.2-1B-Instruct/snapshots/9213176726f574b556790deb65791e0c5aa438b6
.venv-gpu/bin/python - <<'PY'
import hashlib, json, os, platform, sys, time
from pathlib import Path
sys.path.insert(0, 'scripts')
from validate_real_inference import review_snapshot
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
output = Path('results/validation/gpu-controlled-smoke.json')
if output.exists(): raise RuntimeError('Preserve old evidence; freeze a new run/output ID')
output.parent.mkdir(parents=True, exist_ok=True)
report = {'status':'NOT_RUN', 'real_inference':False, 'python':platform.python_version(),
          'torch':torch.__version__, 'cuda_runtime':torch.version.cuda,
          'binary_catalog':'NOT_AUDITED', 'records':[]}
try:
    if not torch.cuda.is_available():
        report['reason'] = 'No accessible CUDA device'
        output.write_text(json.dumps(report, indent=2) + '\n')
        print('NOT_RUN'); raise SystemExit(0)
    if not torch.cuda.is_bf16_supported(): raise RuntimeError('Frozen BF16 mode unavailable')
    report['gpu'] = torch.cuda.get_device_name(0)
    report['total_memory_bytes'] = torch.cuda.get_device_properties(0).total_memory
    torch.manual_seed(2026); torch.cuda.manual_seed_all(2026)
    torch.use_deterministic_algorithms(True)
    a = torch.tensor([[1., 2.], [3., 4.]], device='cuda')
    assert torch.equal(a @ torch.eye(2, device='cuda'), a)
    torch.cuda.synchronize(); report['operators'] = 'PASS'
    snapshot = Path(os.environ['AETHON_MODEL_SNAPSHOT'])
    report.update(review_snapshot(snapshot, 'llama-3.2-1b-instruct'))
    fixture = Path('tests/fixtures/readiness_smoke.json')
    report['fixture_sha256'] = hashlib.sha256(fixture.read_bytes()).hexdigest()
    protocol = json.loads(fixture.read_text())
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(snapshot, local_files_only=True,
                trust_remote_code=False, use_safetensors=True, dtype=torch.bfloat16).to('cuda').eval()
    torch.cuda.reset_peak_memory_stats()
    for row in protocol['inputs']:
        messages = [{'role':'system', 'content':protocol['system']}, {'role':'user', 'content':row['text']}]
        rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        batch = tokenizer(rendered, add_special_tokens=False, return_tensors='pt').to('cuda')
        torch.cuda.synchronize(); start = time.perf_counter()
        with torch.inference_mode():
            tokens = model.generate(**batch, do_sample=False, max_new_tokens=16, pad_token_id=tokenizer.eos_token_id)
        torch.cuda.synchronize()
        text = tokenizer.decode(tokens[0][batch.input_ids.shape[1]:], skip_special_tokens=True)
        assert text.strip()
        report['records'].append({'id':row['id'], 'text':text,
                 'seconds':time.perf_counter()-start, 'dtype':str(next(model.parameters()).dtype)})
    report.update(status='PASS', real_inference=True, peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                  peak_reserved_bytes=torch.cuda.max_memory_reserved())
except Exception as error:
    report.update(status='FAIL', error_type=type(error).__name__, error=str(error))
output.write_text(json.dumps(report, indent=2) + '\n')
print(report['status'])
PY
```

Record driver output, environment/lock and implementation hashes, synchronized
latencies, memory, exceptions and the exact protocol revision. Operator and model
steps must individually pass before claiming GPU compatibility. Official hashes
prove artifact identity, not safety; public-version advisory queries do not audit
the exact CUDA binary. The above commands are a prepared protocol, not execution
evidence. CUDA-specific historical/new output equality is not required without
equivalent hardware, dtype and stochastic controls.
