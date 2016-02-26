import xmm


class GaussianMixtureModel:
    def __init__(self, likelikehood_window=5, nb_mix_comp=10, rel_var_offset=1., abs_var_offset=0.01, debug=True):
        self.__gmm = xmm.GMMGroup()
        self.__gmm.set_nbMixtureComponents(nb_mix_comp)
        self.__gmm.set_varianceOffset(rel_var_offset, abs_var_offset)
        self.__gmm.set_likelihoodwindow(likelikehood_window)
        self.__debug = debug

    def fit(self, gestures):
        """
        :param gestures: list of tuples, where first element is gesture name and second element is 2D numpy array
        where rows are measurements and columns are attributes
        :return:
        """

        training_set = xmm.TrainingSet()
        training_set.set_dimension(gestures[0][1].shape[1])

        for i in range(len(gestures)):
            for frame in gestures[i][1]:
                training_set.recordPhrase(i, frame)
            training_set.setPhraseLabel(i, xmm.Label(gestures[i][0]))

        self.__gmm.set_trainingSet(training_set)

        self.__gmm.train()

        self.__gmm.performance_init()

        if self.__debug:
            print "Number of models: ", self.__gmm.size()

            for label in self.__gmm.models.keys():
                print "Model", label.getSym(), ": trained in ", self.__gmm.models[
                    label].trainingNbIterations, "iterations, loglikelihood = ", self.__gmm.models[
                    label].trainingLogLikelihood

    def predict(self, gesture):
        self.__gmm.performance_update(xmm.vectorf(gesture))
        return list(self.__gmm.results_normalized_likelihoods)
