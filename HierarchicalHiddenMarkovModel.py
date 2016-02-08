import xmm


class HierarchicalHiddenMarkovModel:
    def __init__(self, likelikehood_window=1, nb_mix_comp=10, rel_var_offset=1., abs_var_offset=0.01, debug=True):
        self.__hhmm = xmm.HierarchicalHMM()
        self.__hhmm.set_nbMixtureComponents(nb_mix_comp)
        self.__hhmm.set_varianceOffset(rel_var_offset, abs_var_offset)
        self.__hhmm.set_likelihoodwindow(likelikehood_window)
        self.__debug = debug

    def fit(self, gestures):
        training_set = xmm.TrainingSet()
        training_set.set_dimension(gestures[0].shape[1])

        for i in range(len(gestures)):
            for frame in gestures[i]:
                training_set.recordPhrase(i, frame)
            training_set.setPhraseLabel(i, xmm.Label(i + 1))
        self.__hhmm.set_trainingSet(training_set)

        self.__hhmm.train()

        self.__hhmm.performance_init()

        if self.__debug:
            print "Number of models: ", self.__hhmm.size()

            for label in self.__hhmm.models.keys():
                print "Model", label.getInt(), ": trained in ", self.__hhmm.models[
                    label].trainingNbIterations, "iterations, loglikelihood = ", self.__hhmm.models[
                    label].trainingLogLikelihood

    def predict(self, gesture):
        self.__hhmm.performance_update(xmm.vectorf(gesture))
        return list(self.__hhmm.results_normalized_likelihoods)
