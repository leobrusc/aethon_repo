"""Generate pre-publication diagnostics without full benchmark inference."""
from __future__ import annotations
import json,hashlib,time
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.metrics import roc_auc_score,average_precision_score
from sklearn.feature_extraction.text import TfidfVectorizer
from unified_detector_benchmark import DATASET_ROLES,train_and_calibrate,stratified_sample
from dataset_loader import load_dataset
def ece(p,y,bins=10):
 out=[];p=np.asarray(p);y=np.asarray(y)
 for lo in np.linspace(0,1,bins,endpoint=False):
  hi=lo+1/bins;m=(p>=lo)&(p<hi if hi<1 else p<=hi)
  if m.any():out.append({'bin_lower':lo,'bin_upper':hi,'count':int(m.sum()),'mean_probability':float(p[m].mean()),'observed_positive_rate':float(y[m].mean())})
 return out
def main():
 out=Path('results');diag=out/'diagnostics';tab=out/'tables'/'smoke_diagnostic';diag.mkdir(parents=True,exist_ok=True);tab.mkdir(parents=True,exist_ok=True)
 audits=[]; frames={}
 for split,names in DATASET_ROLES.items():
  for ds in names:
   f=load_dataset(ds).copy();f['dataset']=ds;frames[ds]=f;norm=f.prompt_text.fillna('').astype(str).str.strip();audits.append({'dataset':ds,'split':split,'raw_rows':len(f),'parsed_rows':len(f),'normalized_rows':len(f),'missing_prompt':int(f.prompt_text.isna().sum()),'empty_prompt':int((norm=='').sum()),'label_0':int((f.label==0).sum()),'label_1':int((f.label==1).sum()),'duplicate_prompt':int(f.prompt_text.duplicated().sum()),'unique_normalized_prompt':int(norm.str.lower().str.replace(r'\s+',' ',regex=True).nunique())})
 pd.DataFrame(audits).to_csv(diag/'dataset_row_audit.csv',index=False);json.dump(audits,(diag/'dataset_row_audit.json').open('w'),indent=2)
 vec,lr,cal,tau,report=train_and_calibrate();val=frames['prompt_injections_test'];q=lr.predict_proba(vec.transform(val.prompt_text))[:,1];p=cal.predict(q);y=val.label.to_numpy();sweep=[]
 for t in sorted(set(np.linspace(0,1,101).tolist()+p.tolist())):
  d=p>=t;pos=y.sum();neg=len(y)-pos;tp=((d)&(y==1)).sum();fp=((d)&(y==0)).sum();tn=((~d)&(y==0)).sum();fn=((~d)&(y==1)).sum();tpr=tp/pos;fpr=fp/neg;sweep.append({'threshold':t,'TP':tp,'FP':fp,'TN':tn,'FN':fn,'TPR':tpr,'FPR':fpr,'precision':tp/(tp+fp) if tp+fp else 0,'specificity':tn/neg,'balanced_accuracy':(tpr+tn/neg)/2,'Youden_J':tpr-fpr,'selected_by_youden':abs(t-tau)<1e-9})
 pd.DataFrame(sweep).to_csv(tab/'validation_threshold_sweep.csv',index=False);rel=ece(q,y)+ece(p,y);pd.DataFrame(rel).to_csv(tab/'reliability_diagram_data.csv',index=False);report.update({'auroc_raw':roc_auc_score(y,q),'auroc_calibrated':roc_auc_score(y,p),'auprc_raw':average_precision_score(y,q),'auprc_calibrated':average_precision_score(y,p),'ece_raw':float(np.mean([abs(x['mean_probability']-x['observed_positive_rate']) for x in ece(q,y)])),'ece_calibrated':float(np.mean([abs(x['mean_probability']-x['observed_positive_rate']) for x in ece(p,y)]))});json.dump(report,(tab/'calibration_report.json').open('w'),indent=2)
 print(json.dumps({'tau':tau,'validation':report},indent=2))
if __name__=='__main__':main()
