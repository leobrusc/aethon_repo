"""Inference-free analysis of finalized baseline prediction CSVs."""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from sklearn.metrics import *
def main():
 p=argparse.ArgumentParser();p.add_argument('predictions');p.add_argument('--output-root',required=True);a=p.parse_args(); df=pd.read_csv(a.predictions); out=Path(a.output_root);out.mkdir(parents=True,exist_ok=True)
 if 'run_status' in df.columns and (df.run_status=='PARTIAL').any(): raise SystemExit('Refusing publication analysis for PARTIAL run')
 rows=[]
 for (det,ds),g in df.groupby(['detector','dataset']):
  y=g.true_label; z=g.prediction; pos=y.sum();neg=len(y)-pos; tn,fp,fn,tp=confusion_matrix(y,z,labels=[0,1]).ravel(); rows.append({'detector':det,'dataset':ds,'rows':len(g),'auroc':roc_auc_score(y,g.score) if pos and neg else None,'auprc':average_precision_score(y,g.score) if pos and neg else None,'precision':precision_score(y,z,zero_division=0) if pos else None,'recall':recall_score(y,z,zero_division=0) if pos else None,'f1':f1_score(y,z,zero_division=0) if pos else None,'fpr':fp/neg if neg else None,'tp':tp,'tn':tn,'fp':fp,'fn':fn})
 pd.DataFrame(rows).to_csv(out/'baseline_metrics_by_dataset.csv',index=False);return 0
if __name__=='__main__':raise SystemExit(main())
