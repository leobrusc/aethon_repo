import time
import numpy as np
from aethon_heuristic import is_adversarial_heuristic
from aethon_ml_pipeline import load_model, predict

def noisy_count(count, epsilon=1.0):
    scale = 1/epsilon
    return count + np.random.laplace(0, scale)

class AethonFull:
    def __init__(self, ml_model_path=None, epsilon=1.2):
        self.ml = load_model(ml_model_path) if ml_model_path else None
        self.epsilon = epsilon
        self.log = []

    def decide(self, prompt):
        meta = {"heuristic": is_adversarial_heuristic(prompt)}
        pred = 0
        if self.ml:
            try:
                pred = predict(self.ml, [prompt])[0]
            except:
                pred = 0
        meta["ml_pred"] = pred

        if meta["heuristic"] or pred == 1:
            action = "mitigate"
        else:
            action = "allow"

        entry = {
            "prompt_snip": prompt[:100],
            "action": action,
            "timestamp": time.time(),
            "noisy": noisy_count(1, epsilon=self.epsilon),
        }
        self.log.append(entry)

        return {"action": action, "meta": meta}
