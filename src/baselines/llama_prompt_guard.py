from .base import DetectorBaseline
class LlamaPromptGuard(DetectorBaseline):
    def __init__(self,**kwargs): super().__init__('meta-llama/Llama-Prompt-Guard-2-86M',('malicious','adversarial'),**kwargs)
