import xmm
from BaseModel import BaseModel


class GaussianMixtureModel(BaseModel):
    def __init__(self):
        BaseModel.__init__(self, xmm.GMMGroup())
