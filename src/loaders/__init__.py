"""Dataset-specific normalization adapters."""

from loaders.cyberseceval import normalize_cyberseceval
from loaders.jailbreakbench import normalize_jailbreakbench
from loaders.notinject import normalize_notinject


SOURCE_NORMALIZERS = {
    "notinject": normalize_notinject,
    "jailbreakbench_behaviors": normalize_jailbreakbench,
    "cyberseceval_prompt_injection": normalize_cyberseceval,
}
