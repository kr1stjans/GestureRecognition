import xmm


class BaseModel:
    def __init__(self, model, likelikehood_window=1, nb_mix_comp=10, rel_var_offset=8., abs_var_offset=0.01):
        """
        :param likelikehood_window:
        :param nb_mix_comp:
        :param rel_var_offset: Simple tests indicate when this attribute is closer to nb_mix_comp
        it affects faster fallback to init position.
        :param abs_var_offset:
        :return:
        """
        self.__model = model
        self.__model.set_nbMixtureComponents(nb_mix_comp)
        self.__model.set_varianceOffset(rel_var_offset, abs_var_offset)
        self.__model.set_likelihoodwindow(likelikehood_window)

    def train(self, gestures):
        """
        :param gestures: list of tuples, where first element is gesture name and second element is 2D numpy array
        where rows are measurements and columns are attributes
        :return:
        """

        training_set = xmm.TrainingSet()
        # get first gesture tuple
        first_gesture_tuple = gestures[0]
        # get 2D numpy array of gesture data
        gesture_measurements = first_gesture_tuple[1]
        # attributes are columns, that is the second element of the shape
        attributes_cnt = gesture_measurements.shape[1]
        # training set dimension is number of gesture attributess
        training_set.set_dimension(attributes_cnt)

        for i in range(len(gestures)):
            gesture_measurements = gestures[i][1]
            gesture_name = gestures[i][0]

            # frame is vector of attributes at each time frame. size must match training set dimension
            for frame in gesture_measurements:
                training_set.recordPhrase(i, frame)
            training_set.setPhraseLabel(i, xmm.Label(gesture_name))

        self.__model.set_trainingSet(training_set)

        self.__model.train()

        self.__model.performance_init()

    def update(self, gesture):
        self.__model.performance_update(xmm.vectorf(gesture))

    def log_likelihoods(self):
        return list(self.__model.results_log_likelihoods)

    def normalized_likelihoods(self):
        return list(self.__model.results_normalized_likelihoods)

    def print_trained_model_statistics(self):
        if self.__model.is_trained():
            print "Number of models: ", self.__model.size()

            for label in self.__model.models.keys():
                print "Model", label.getSym(), ": trained in ", self.__model.models[
                    label].trainingNbIterations, "iterations, loglikelihood = ", self.__model.models[
                    label].trainingLogLikelihood
        else:
            print "Model not yet trained."
