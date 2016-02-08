import xmm


class GaussianMixtureModel:
    def __init__(self, likelikehood_window=5, nb_mix_comp=10, rel_var_offset=1., abs_var_offset=0.01):
        self.__gmm = xmm.GMMGroup()
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
        self.__gmm.set_trainingSet(training_set)

        # Set parameters
        self.__gmm.set_nbMixtureComponents(self.__NB_MIXTURE_COMPONENTS)
        self.__gmm.set_varianceOffset(self.__RELATIVE_VARIANCE_OFFSET, self.__ABSOLUTE_VARIANCE_OFFSET)
        # Train all models
        self.__gmm.train()

        # Set Size of the likelihood Window (samples)
        self.__gmm.set_likelihoodwindow(self.__LIKELIHOOD_WINDOW)
        # Initialize performance phase
        self.__gmm.performance_init()

        print "Number of models: ", self.__gmm.size()

        for label in self.__gmm.models.keys():
            print "Model", label.getInt(), ": trained in ", self.__gmm.models[
                label].trainingNbIterations, "iterations, loglikelihood = ", self.__gmm.models[
                label].trainingLogLikelihood

    def predict(self, gesture):
        self.__gmm.performance_update(xmm.vectorf(gesture))
        return list(self.__gmm.results_normalized_likelihoods)
