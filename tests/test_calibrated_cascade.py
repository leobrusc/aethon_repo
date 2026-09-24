import numpy as np
from aethon_calibrated_cascade import ValidationCalibrator,cascade_score,operational_decision,select_threshold
def test_score_and_decision_invariants():
 h=np.array([0,1,0]);p=np.array([.8,.2,.4]);s,d=operational_decision(h,p,.5);assert np.allclose(s,[.8,1,.4]);assert d.tolist()==[1,1,0];assert np.allclose(s,cascade_score(h,p))
def test_calibration_validation_only_api():
 c=ValidationCalibrator('sigmoid').fit([.1,.2,.8,.9],[0,0,1,1]); assert len(c.predict([.3,.7]))==2
def test_isotonic_and_threshold():
 c=ValidationCalibrator('isotonic').fit([.1,.2,.8,.9],[0,0,1,1]); assert np.all(np.diff(c.predict([.1,.2,.8,.9]))>=0); assert 0<select_threshold([.1,.2,.8,.9],[0,0,1,1])<1
