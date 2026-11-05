## WildJailbreak diagnosis

The loader selects the raw `prompt` field and maps `adversarial_benign` to 0 and `adversarial_harmful` to 1. Counts are {'adversarial_harmful': 2000, 'adversarial_benign': 210}. The B2 benign result is FP=201, TN=9, FPR=0.9571.
All local rows have raw `split` distribution `{'train': 2210}`. The value `train` is a local metadata anomaly for a file whose 210/2000 counts match the official evaluation construction; the loader correctly does not use this field as the class label. There are 0 normalized exact duplicates within the 210 adversarial-benign prompts.
Safety/refusal vocabulary occurs in 46.2% of adversarial-benign prompts. The official [WildJailbreak dataset card](https://huggingface.co/datasets/allenai/wildjailbreak) defines these as benign-intent prompts deliberately transformed to resemble jailbreaks, specifically to measure exaggerated safety behavior. The [paper](https://arxiv.org/abs/2406.18510) describes the same contrastive construction.
Therefore the loader mapping is faithful, but `benign` here does not mean ordinary benign traffic. The result diagnoses inability to distinguish malicious intent from adversarial form. No relabeling is justified.

