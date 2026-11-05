"""Leakage-free AETHON score, calibration, and ablation evaluation."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

@dataclass
class CalibrationResult:
    method: str
    calibrator: object
    threshold: float
    validation_metrics: dict

class ValidationCalibrator:
    def __init__(self, method='sigmoid'):
        if method not in {'sigmoid','isotonic'}: raise ValueError('calibration must be sigmoid or isotonic')
        self.method=method; self.model=None
    def fit(self, raw_probability, labels):
        x=np.asarray(raw_probability,float); y=np.asarray(labels,int)
        if self.method=='sigmoid':
            self.model=LogisticRegression(solver='lbfgs',random_state=42).fit(x.reshape(-1,1),y)
        else: self.model=IsotonicRegression(out_of_bounds='clip').fit(x,y)
        return self
    def predict(self, raw_probability):
        x=np.asarray(raw_probability,float)
        if self.method=='sigmoid': return self.model.predict_proba(x.reshape(-1,1))[:,1]
        return np.asarray(self.model.predict(x),float)

def select_threshold(scores, labels, criterion='youden'):
    y=np.asarray(labels,int); s=np.asarray(scores,float); best=(0.5,-np.inf)
    for tau in np.linspace(0.01,0.99,99):
        d=s>=tau; pos=(y==1).sum(); neg=(y==0).sum(); tpr=((d)&(y==1)).sum()/pos if pos else 0; fpr=((d)&(y==0)).sum()/neg if neg else 0
        value=tpr-fpr if criterion=='youden' else -fpr
        if value>best[1]: best=(float(tau),float(value))
    return best[0]

def cascade_score(heuristic, calibrated_probability):
    return np.maximum(np.asarray(heuristic,int),np.asarray(calibrated_probability,float))

def operational_decision(heuristic, calibrated_probability, tau):
    h=np.asarray(heuristic,int); p=np.asarray(calibrated_probability,float); s=cascade_score(h,p)
    d=(s>=tau).astype(int); assert np.array_equal(d, np.logical_or(h.astype(bool),p>=tau).astype(int))
    return s,d

def calibration_diagnostics(scores, labels):
    return {'brier_score':float(brier_score_loss(labels,scores)), 'n':int(len(labels))}
