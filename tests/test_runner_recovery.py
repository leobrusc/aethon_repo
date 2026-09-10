from pathlib import Path
import pandas as pd
from run_baseline_benchmark import run_records
from baseline_reliability import load_checkpoint, read_state, write_state, fingerprint

class FakeDetector:
    device=type('D',(),{'__str__':lambda s:'cpu'})()
    def __init__(self, stop_after=None, fail_call=None): self.calls=[]; self.stop_after=stop_after; self.fail_call=fail_call; self.n=0
    def predict_batch(self, prompts):
        self.n+=1
        if self.fail_call==self.n: raise RuntimeError('synthetic batch failure')
        self.calls.extend(prompts)
        return [(0.9,1,0,4) for _ in prompts]

def frame():
    return pd.DataFrame({'dataset':['synthetic']*100,'prompt_id':[str(i) for i in range(100)],'prompt_text':[f'p{i}' for i in range(100)],'label':[1]*100,'source':['synthetic']*100})
def setup(tmp_path):
    run=tmp_path/'runs'/'r'; (run/'checkpoint').mkdir(parents=True); (run/'final').mkdir();
    fp=fingerprint({'detector':'fake','datasets':['synthetic']}); return run,fp
def test_real_orchestration_37_63_and_no_reinference(tmp_path):
    df=frame();run,fp=setup(tmp_path); d=FakeDetector();
    # deterministic interruption after first 37-record batch is represented by a detector raising
    class Interrupt(FakeDetector):
        def predict_batch(self,p):
            if self.n==0: self.n+=1; self.calls.extend(p); return [(0.9,1,0,4) for _ in p]
            raise KeyboardInterrupt()
    first=Interrupt();
    try: run_records(df,first,run,'r',fp,37,37)
    except KeyboardInterrupt: pass
    # emulate production interruption flush for the completed first batch
    ck=run/'checkpoint'/'predictions.jsonl'; write_state(run/'state.json',{'run_id':'r','status':'PARTIAL','expected_unique_records':100,'completed_unique_records':37,'remaining_records':63,'duplicates':0,'fingerprint':fp})
    second=FakeDetector(); assert run_records(df,second,run,'r',fp,37,37); assert len(second.calls)==63; assert len(load_checkpoint(ck))==100
def test_failed_batch_preserves_prior_checkpoint(tmp_path):
    df=frame();run,fp=setup(tmp_path); d=FakeDetector(fail_call=2)
    try: run_records(df, d, run,'r',fp,10,10)
    except RuntimeError: pass
    assert len(load_checkpoint(run/'checkpoint'/'predictions.jsonl'))==10
