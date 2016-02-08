import xmm


class HierarchicalHiddenMarkovModel:
    def __init__(self, likelikehood_window=1, nb_mix_comp=10, rel_var_offset=1., abs_var_offset=0.01):
        self.__hhmm = xmm.HierarchicalHMM()
        self.__LIKELIHOOD_WINDOW = likelikehood_window
        self.__NB_MIXTURE_COMPONENTS = nb_mix_comp
        self.__RELATIVE_VARIANCE_OFFSET = rel_var_offset
        self.__ABSOLUTE_VARIANCE_OFFSET = abs_var_offset

    def fit(self, gestures):
        print "Fitting Gaussian Mixture Model"
        training_set = xmm.TrainingSet()
        training_set.set_dimension(len(gestures))  # dimension of data in this example
        training_set.set_column_names(xmm.vectors(['x', 'y', 'z']))

        for i in range(len(gestures)):
            for frame in gestures[i]:
                # Append data frame to the phrase i
                training_set.recordPhrase(i, frame)
            training_set.setPhraseLabel(i, xmm.Label(i + 1))
        # Set pointer to the training set
        self.__hhmm.set_trainingSet(training_set)

        # Set parameters
        self.__hhmm.set_nbMixtureComponents(self.__NB_MIXTURE_COMPONENTS)
        self.__hhmm.set_varianceOffset(self.__RELATIVE_VARIANCE_OFFSET, self.__ABSOLUTE_VARIANCE_OFFSET)
        # Train all models
        self.__hhmm.train()

        # Set Size of the likelihood Window (samples)
        self.__hhmm.set_likelihoodwindow(self.__LIKELIHOOD_WINDOW)
        # Initialize performance phase
        self.__hhmm.performance_init()

        print "Number of models: ", self.__hhmm.size()

        for label in self.__hhmm.models.keys():
            print "Model", label.getInt(), ": trained in ", self.__hhmm.models[
                label].trainingNbIterations, "iterations, loglikelihood = ", self.__hhmm.models[
                label].trainingLogLikelihood

    def predict(self, gesture):
        self.__hhmm.performance_update(xmm.vectorf(gesture))
        return list(self.__hhmm.results_normalized_likelihoods)
