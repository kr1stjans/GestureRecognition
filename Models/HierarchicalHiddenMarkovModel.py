import xmm
from BaseModel import BaseModel


class HierarchicalHiddenMarkovModel(BaseModel):
    def __init__(self):
        BaseModel.__init__(self, xmm.HierarchicalHMM())
