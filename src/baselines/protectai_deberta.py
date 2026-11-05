from .base import DetectorBaseline
class ProtectAIDeberta(DetectorBaseline):
    def __init__(self,**kwargs): super().__init__('protectai/deberta-v3-base-prompt-injection-v2',('injection','adversarial','malicious'),**kwargs)
