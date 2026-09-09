"""Leakage-free lightweight detector selection and frozen evaluation."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import hashlib, json, platform, subprocess, time
import joblib, numpy as np, pandas as pd, sklearn
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.svm import LinearSVC
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score, roc_auc_score
from aethon_heuristic import is_adversarial_heuristic
from benchmark.detection import EVALUATION_DATASETS, LABEL_PROVENANCE
from dataset_loader import get_dataset_metadata, load_dataset

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRAINING_DATASET = "prompt_injections_train"
FINAL_DATASETS = tuple(EVALUATION_DATASETS)
REPRESENTATIONS = {
    "word_unigram": {"kind":"word","analyzer":"word","ngram_range":(1,1),"max_features":5000},
    "word_bigram": {"kind":"word","analyzer":"word","ngram_range":(1,2),"max_features":5000},
    "char_3_5": {"kind":"char","analyzer":"char_wb","ngram_range":(3,5),"max_features":5000},
    "char_3_6": {"kind":"char","analyzer":"char_wb","ngram_range":(3,6),"max_features":5000},
    "word_char_union": {"kind":"union","word_ngram_range":(1,2),"char_ngram_range":(3,5),"max_features":5000},
}
CLASSIFIERS = ("logistic_regression","linear_svm","calibrated_linear_svm")
THRESHOLDS = np.round(np.arange(.05,.951,.01),2)
FPR_CAPS = (.05,.10,.15)

def git_commit():
    try: return subprocess.run(["git","rev-parse","HEAD"],cwd=PROJECT_ROOT,check=True,capture_output=True,text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError): return "unavailable"

def load_training_only():
    frame = load_dataset(TRAINING_DATASET)
    if len(frame) != 546 or frame.label.value_counts().to_dict() != {0:343,1:203}: raise ValueError("Unexpected training data")
    return frame

def vec_params(analyzer, ngram, max_features=5000):
    return {"analyzer":analyzer,"ngram_range":ngram,"max_features":max_features,"lowercase":True,"min_df":1,"max_df":1.0,"sublinear_tf":False,"norm":"l2","use_idf":True,"smooth_idf":True}

def build_pipeline(rep, classifier):
    p = REPRESENTATIONS[rep]
    if p["kind"] == "union":
        features = FeatureUnion([("word",TfidfVectorizer(**vec_params("word",p["word_ngram_range"],p["max_features"]))),("char",TfidfVectorizer(**vec_params("char_wb",p["char_ngram_range"],p["max_features"])))])
    else: features = TfidfVectorizer(**vec_params(p["analyzer"],p["ngram_range"],p["max_features"]))
    if classifier == "logistic_regression": est = LogisticRegression(C=1.0,penalty="l2",solver="lbfgs",max_iter=1000,random_state=42,fit_intercept=True,class_weight=None,tol=1e-4)
    elif classifier == "linear_svm": est = LinearSVC(C=1.0,penalty="l2",loss="squared_hinge",dual="auto",max_iter=1000,random_state=42,fit_intercept=True,class_weight=None,tol=1e-4)
    elif classifier == "calibrated_linear_svm": est = CalibratedClassifierCV(LinearSVC(C=1.0,penalty="l2",loss="squared_hinge",dual="auto",max_iter=1000,random_state=42,fit_intercept=True,class_weight=None,tol=1e-4),method="sigmoid",cv=3,n_jobs=1)
    else: raise ValueError(classifier)
    return Pipeline([("features",features),("classifier",est)])

def classifier_parameters(classifier):
    base={"C":1.0,"penalty":"l2","loss":"squared_hinge","dual":"auto","max_iter":1000,"random_state":42,"fit_intercept":True,"class_weight":None,"tol":1e-4}
    if classifier=="logistic_regression": return {"C":1.0,"penalty":"l2","solver":"lbfgs","max_iter":1000,"random_state":42,"fit_intercept":True,"class_weight":None,"tol":1e-4}
    if classifier=="linear_svm": return base
    if classifier=="calibrated_linear_svm": return {"base_estimator":base,"method":"sigmoid","cv":3,"n_jobs":1}
    raise ValueError(classifier)

def score_model(model, texts):
    return model.predict_proba(texts)[:,1] if hasattr(model.named_steps["classifier"],"predict_proba") else model.decision_function(texts)

def metric(labels, predictions, scores):
    labels=np.asarray(labels,dtype=int); predictions=np.asarray(predictions,dtype=int); scores=np.asarray(scores,float)
    pos=int((labels==1).sum()); neg=int((labels==0).sum()); tp=int(((labels==1)&(predictions==1)).sum()); tn=int(((labels==0)&(predictions==0)).sum()); fp=int(((labels==0)&(predictions==1)).sum()); fn=int(((labels==1)&(predictions==0)).sum()); mixed=pos>0 and neg>0
    return {"rows":len(labels),"benign":neg,"adversarial":pos,"auroc":float(roc_auc_score(labels,scores)) if mixed else np.nan,"auprc":float(average_precision_score(labels,scores)) if mixed else np.nan,"precision":float(precision_score(labels,predictions,zero_division=0)) if pos else np.nan,"recall":float(recall_score(labels,predictions,zero_division=0)) if pos else np.nan,"f1":float(f1_score(labels,predictions,zero_division=0)) if pos else np.nan,"fpr":float(fp/neg) if neg else np.nan,"tp":tp,"tn":tn,"fp":fp,"fn":fn}

def choose_threshold(labels,scores,cap):
    candidates=[]
    for threshold in THRESHOLDS:
        values=metric(labels,scores>=threshold,scores)
        if np.isfinite(values["fpr"]) and values["fpr"]<=cap: candidates.append((values["f1"],values["auroc"],values["auprc"],float(threshold),values))
    if not candidates: return np.nan, {"status":"no_candidate_satisfies_fpr_cap","fpr_cap":cap}
    best=max(candidates,key=lambda x:x[:3]); result=dict(best[4]); result.update({"status":"selected","fpr_cap":cap,"threshold":best[3]}); return best[3],result

def cross_validate(training, seed=42, folds=5):
    texts=training.prompt_text.to_numpy(); labels=training.label.to_numpy(int); splitter=StratifiedKFold(folds,shuffle=True,random_state=seed); candidates=[]; fold_rows=[]; oof=[]
    for rep in REPRESENTATIONS:
        for classifier in CLASSIFIERS:
            name=f"{rep}__{classifier}"; scores=np.full(len(training),np.nan); latencies=[]; fold_indices=[]
            for fold,(tr,va) in enumerate(splitter.split(texts,labels),1):
                model=build_pipeline(rep,classifier); model.fit(texts[tr],labels[tr]); started=time.perf_counter(); s=score_model(model,texts[va]); elapsed=(time.perf_counter()-started)*1000; scores[va]=s; latencies.append(elapsed/len(va)); fold_indices.append((fold,va))
            threshold,selected=choose_threshold(labels,scores,.10); cap_results={str(cap):choose_threshold(labels,scores,cap)[1] for cap in FPR_CAPS}; preds=(scores>=threshold).astype(int) if np.isfinite(threshold) else np.zeros(len(labels),int); values=metric(labels,preds,scores)
            row={"candidate":name,"representation":rep,"analyzer":REPRESENTATIONS[rep].get("analyzer","FeatureUnion"),"ngram_range":str(REPRESENTATIONS[rep].get("ngram_range",(REPRESENTATIONS[rep].get("word_ngram_range"),REPRESENTATIONS[rep].get("char_ngram_range")))),"max_features":5000,"classifier":classifier,"classifier_parameters":json.dumps(classifier_parameters(classifier),default=str,sort_keys=True),"threshold":threshold,"selection_criterion":"maximize OOF F1 subject to OOF FPR <= 0.10","fpr_cap_analyses":json.dumps(cap_results,default=str),"mean_latency_ms":float(np.mean(latencies)),"median_latency_ms":float(np.median(latencies)),"p95_latency_ms":float(np.quantile(latencies,.95)),**values}
            fold_metrics=[]
            for fold,va in fold_indices:
                fv=metric(labels[va],(scores[va]>=threshold).astype(int) if np.isfinite(threshold) else np.zeros(len(va),int),scores[va]); fv.update({"candidate":name,"representation":rep,"classifier":classifier,"fold":fold}); fold_metrics.append(fv); fold_rows.append(fv)
            for key in ("auroc","auprc","precision","recall","f1","fpr"): row[key+"_std"]=float(pd.DataFrame(fold_metrics)[key].std(ddof=1))
            candidates.append(row); oof.extend({"candidate":name,"representation":rep,"classifier":classifier,"row_index":int(i),"true_label":int(labels[i]),"oof_score":float(scores[i])} for i in range(len(labels)))
    return pd.DataFrame(candidates),pd.DataFrame(fold_rows),pd.DataFrame(oof)

def pareto(candidates,cap=.10):
    valid=candidates[np.isfinite(candidates.threshold)&(candidates.fpr<=cap)].copy(); keep=[]
    for i,row in valid.iterrows():
        dominated=((valid.f1>=row.f1)&(valid.auroc>=row.auroc)&(valid.auprc>=row.auprc)&((valid.f1>row.f1)|(valid.auroc>row.auroc)|(valid.auprc>row.auprc))).any()
        if not dominated: keep.append(i)
    return valid.loc[keep].sort_values(["f1","auroc"],ascending=False)

def final_evaluation(model,threshold):
    rows=[]
    for dataset in FINAL_DATASETS:
        frame=load_dataset(dataset); scores=[]; latencies=[]
        for prompt in frame.prompt_text.tolist():
            started=time.perf_counter(); scores.append(float(score_model(model,[prompt])[0])); latencies.append((time.perf_counter()-started)*1000)
        scores=np.asarray(scores); heuristic=frame.prompt_text.map(is_adversarial_heuristic).to_numpy(int); ml=(scores>=threshold).astype(int)
        for condition,predictions in (("V1",ml),("V2",np.maximum(heuristic,ml))):
            for source,score,latency,hp,mp,pred in zip(frame.itertuples(index=False),scores,latencies,heuristic,ml,predictions):
                prompt=str(source.prompt_text); rows.append({"dataset":dataset,"prompt_id":str(source.prompt_id),"prompt_sha256":hashlib.sha256(prompt.encode()).hexdigest(),"true_label":int(source.label),"label_provenance":LABEL_PROVENANCE[dataset],"condition":condition,"heuristic_prediction":int(hp),"ml_prediction":int(mp),"ml_score":float(score),"final_prediction":int(pred),"detection_latency_ms":float(latency)})
    result=pd.DataFrame(rows); per=[]
    for (dataset,condition),group in result.groupby(["dataset","condition"],sort=False):
        row=metric(group.true_label,group.final_prediction,group.ml_score); row.update({"dataset":dataset,"condition":condition,"median_latency_ms":float(group.detection_latency_ms.median()),"p95_latency_ms":float(group.detection_latency_ms.quantile(.95))}); per.append(row)
    micro=[]
    for condition,group in result.groupby("condition",sort=False):
        row=metric(group.true_label,group.final_prediction,group.ml_score); row.update({"condition":condition,"aggregation":"micro_pooled_fixed_final_rows","median_latency_ms":float(group.detection_latency_ms.median()),"p95_latency_ms":float(group.detection_latency_ms.quantile(.95))}); micro.append(row)
    per=pd.DataFrame(per); macro=per.groupby("condition",as_index=False)[["auroc","auprc","precision","recall","f1","fpr","median_latency_ms","p95_latency_ms"]].mean(numeric_only=True); return result,per,pd.DataFrame(micro),macro

def mcnemar(new_result):
    old=pd.read_csv(PROJECT_ROOT/"results/revision/detection/per_prompt_results.csv"); old=old[old.condition=="B3"][["dataset","prompt_sha256","final_prediction"]].rename(columns={"final_prediction":"old_prediction"}); new=new_result[new_result.condition=="V2"][["dataset","prompt_sha256","true_label","final_prediction"]].rename(columns={"final_prediction":"new_prediction"}); merged=new.merge(old,on=["dataset","prompt_sha256"],how="inner"); rows=[]
    from math import comb
    for dataset,g in merged.groupby("dataset",sort=False):
        oe=g.old_prediction.to_numpy()!=g.true_label.to_numpy(); ne=g.new_prediction.to_numpy()!=g.true_label.to_numpy(); b=int((oe&~ne).sum()); c=int((~oe&ne).sum()); n=b+c; p=min(1.,2*sum(comb(n,k) for k in range(min(b,c)+1))/(2**n)) if n else 1.; rows.append({"dataset":dataset,"n_paired":len(g),"old_only_errors_b":b,"new_only_errors_c":c,"discordant":n,"mcnemar_p_two_sided":p})
    return pd.DataFrame(rows)

def run_phase2(output_root="results/revision/model_selection",seed=42):
    output=PROJECT_ROOT/output_root; output.mkdir(parents=True,exist_ok=True); training=load_training_only(); candidates,folds,oof=cross_validate(training,seed); candidates.to_csv(output/"cv_candidate_results.csv",index=False); folds.to_csv(output/"cv_fold_results.csv",index=False); oof.to_csv(output/"oof_training_predictions.csv",index=False)
    threshold_rows=[]
    for _,row in candidates.iterrows():
        for cap,values in json.loads(row.fpr_cap_analyses).items(): threshold_rows.append({"candidate":row.candidate,"fpr_cap":float(cap),**values})
    pd.DataFrame(threshold_rows).to_csv(output/"threshold_selection.csv",index=False); pareto(candidates).to_csv(output/"pareto_frontier.csv",index=False)
    candidates[["candidate","representation","classifier","threshold","auroc","auprc","precision","recall","f1","fpr","median_latency_ms","p95_latency_ms"]].to_latex(output/"feature_configuration_comparison.tex",index=False,na_rep="NA",float_format="%.6f")
    valid=candidates[np.isfinite(candidates.threshold)&(candidates.fpr<=.10)]; selected=valid.sort_values(["f1","auroc","auprc"],ascending=False).iloc[0] if len(valid) else candidates.sort_values(["f1","auroc"],ascending=False).iloc[0]; selected_dict=selected.to_dict(); selected_dict["selection_policy"]={"primary_fpr_cap":.10,"secondary_fpr_caps":[.05,.15],"objective":"maximize OOF F1 subject to FPR cap"}; selected_dict["git_commit"]=git_commit(); selected_dict["training_dataset"]=TRAINING_DATASET
    (output/"selected_configuration.json").write_text(json.dumps(selected_dict,indent=2,default=str),encoding="utf-8"); (output/"selected_configuration.md").write_text("# Selected configuration\n\n"+json.dumps(selected_dict,indent=2,default=str),encoding="utf-8")
    model=build_pipeline(selected.representation,selected.classifier); model.fit(training.prompt_text,training.label); model_path=PROJECT_ROOT/"src/models/aethon_detector_revision_v2.pkl"; joblib.dump(model,model_path); metadata={"model_path":str(model_path),"training_dataset":TRAINING_DATASET,"training_dataset_sha256":get_dataset_metadata(TRAINING_DATASET)["sha256"],"training_rows":len(training),"class_distribution":{"benign":343,"adversarial":203},"representation":selected.representation,"classifier":selected.classifier,"classifier_parameters":json.loads(selected.classifier_parameters),"feature_configuration":REPRESENTATIONS[selected.representation],"selected_threshold":selected.threshold,"selection_policy":selected_dict["selection_policy"],"cross_validation_candidate":selected_dict,"python_version":platform.python_version(),"sklearn_version":sklearn.__version__,"git_commit":git_commit(),"timestamp_utc":datetime.now(timezone.utc).isoformat()}; (PROJECT_ROOT/"src/models/aethon_detector_revision_v2.metadata.json").write_text(json.dumps(metadata,indent=2,default=str),encoding="utf-8")
    heuristic=training.prompt_text.map(is_adversarial_heuristic).to_numpy(int); ml_scores=[]; ml_latencies=[]
    for prompt in training.prompt_text:
        started=time.perf_counter(); ml_scores.append(float(score_model(model,[prompt])[0])); ml_latencies.append((time.perf_counter()-started)*1000)
    hits=heuristic.astype(bool); hp=training.label.to_numpy(int)[hits]; heuristic_diag={"rows":len(training),"heuristic_hits":int(hits.sum()),"heuristic_hit_rate":float(hits.mean()),"heuristic_true_positives":int((hp==1).sum()),"heuristic_precision":float((hp==1).mean()) if len(hp) else np.nan,"fraction_resolved_before_ml":float(hits.mean()),"selected_model_mean_ml_latency_ms":float(np.mean(ml_latencies)),"estimated_mean_latency_saved_ms":float(np.mean(ml_latencies)*hits.mean())}
    (output/"l1_training_diagnostics.json").write_text(json.dumps(heuristic_diag,indent=2,default=str),encoding="utf-8")
    final,per,micro,macro=final_evaluation(model,float(selected.threshold)); final.to_csv(output/"final_evaluation.csv",index=False); per.to_csv(output/"final_metrics_by_dataset.csv",index=False); micro.to_csv(output/"final_metrics_micro.csv",index=False); macro.to_csv(output/"final_metrics_macro.csv",index=False)
    subgroup=[]
    for condition,g in final.groupby("condition",sort=False):
        for name,s in (("adversarial_benign_wildjailbreak",g[(g.dataset=="wildjailbreak_eval")&(g.true_label==0)]),("ordinary_benign_other_evaluation",g[(g.true_label==0)&(g.dataset!="wildjailbreak_eval")])):
            subgroup.append({"condition":condition,"subgroup":name,"rows":len(s),"false_positives":int(s.final_prediction.sum()),"fpr":float(s.final_prediction.mean()) if len(s) else np.nan})
    pd.DataFrame(subgroup).to_csv(output/"benign_subgroup_fpr.csv",index=False); mcnemar(final).to_csv(output/"paired_comparison.csv",index=False)
    phase1=pd.read_csv(PROJECT_ROOT/"results/revision/detection/metrics_by_condition.csv"); b3=phase1[phase1.condition=="B3"].iloc[0]; v2=micro[micro.condition=="V2"].iloc[0]; comparison=pd.DataFrame([{"detector":"Phase 1 B3",**{k:b3.get(k,np.nan) for k in ("auroc","auprc","precision","recall","f1","fpr","median_latency_ms","p95_latency_ms")}},{"detector":"Phase 2 V2 selected",**{k:v2.get(k,np.nan) for k in ("auroc","auprc","precision","recall","f1","fpr","median_latency_ms","p95_latency_ms")}}]); tables=PROJECT_ROOT/"results/revision/tables"; tables.mkdir(parents=True,exist_ok=True); comparison.to_csv(tables/"lightweight_detector_comparison.csv",index=False); (tables/"lightweight_detector_comparison.md").write_text(comparison.to_string(index=False),encoding="utf-8"); comparison.to_latex(tables/"lightweight_detector_comparison.tex",index=False,na_rep="NA",float_format="%.6f")
    (output/"experiment_manifest.json").write_text(json.dumps({"training_only_selection":True,"final_evaluation_after_freeze":True,"selected_model_metadata":metadata,"target_llm_initialized":False,"phase1_artifacts_immutable":True,"git_commit":git_commit()},indent=2,default=str),encoding="utf-8")
    return {"candidate_count":len(candidates),"selected":selected_dict,"final_micro":micro.to_dict(orient="records"),"paired":mcnemar(final).to_dict(orient="records"),"output":str(output)}
