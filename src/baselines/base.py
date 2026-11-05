from __future__ import annotations
import torch
class DetectorBaseline:
    def __init__(self,model_id,positive_terms,max_length=512,device='auto',batch_size=8):
        self.model_id=model_id;self.batch_size=batch_size;self.max_length=max_length;self.device=torch.device('cuda' if device=='auto' and torch.cuda.is_available() else ('cuda' if device=='cuda' else 'cpu'));self.positive_terms=positive_terms
    def load(self):
        from transformers import AutoModelForSequenceClassification,AutoTokenizer
        self.tokenizer=AutoTokenizer.from_pretrained(self.model_id);self.model=AutoModelForSequenceClassification.from_pretrained(self.model_id).to(self.device).eval(); labels=self.model.config.id2label
        matches=[(int(i),str(v)) for i,v in labels.items() if any(t in str(v).lower() for t in self.positive_terms)]
        if len(matches)!=1: raise ValueError(f'ambiguous adversarial label mapping: {labels}')
        self.positive_index,self.positive_label=matches[0];return self
    def score(self,prompts):
        import torch
        raw=self.tokenizer(list(prompts),return_tensors='pt',padding=True,truncation=True,max_length=self.max_length);raw={k:v.to(self.device) for k,v in raw.items()}
        with torch.inference_mode(): return torch.softmax(self.model(**raw).logits,dim=-1)[:,self.positive_index].cpu().numpy()
    def predict(self,prompts,threshold=.5): return (self.score(prompts)>=threshold).astype(int)
    def metadata(self): return {'model_id':self.model_id,'resolved_label':self.positive_label,'resolved_index':self.positive_index,'device':str(self.device),'batch_size':self.batch_size,'max_length':self.max_length}
