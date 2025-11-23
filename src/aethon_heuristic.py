import re
from typing import List

PATTERNS = [
    r"ignore previous instructions",
    r"ignore (the )?previous",
    r"system override",
    r"as an? jailbroken",
    r"reset your instructions",
    r"do not follow previous",
    r"disregard previous",
    r"follow the instructions below"
]

def is_adversarial_heuristic(prompt: str) -> bool:
    if not prompt:
        return False
    text = prompt.lower()
    for p in PATTERNS:
        if re.search(p, text):
            return True
    return False

def batch_detect(prompts: List[str]) -> List[bool]:
    return [is_adversarial_heuristic(p) for p in prompts]
