import xmm
from Controllers.SensorDataController import SensorDataController


class BaseModel:
    def __init__(self, model, likelikehood_window=1, nb_mix_comp=10, rel_var_offset=8., abs_var_offset=0.01,
                 data_types=('raw_acc', 'raw_rot')):
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
        self.__data_types = data_types

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
        # extract given attributes of the first element of the 2D numpy array
        extracted_attributes = SensorDataController.extract_data(gesture_measurements[0], self.__data_types)
        # length of the extracted attributes is the dimension of the model
        training_set.set_dimension(len(extracted_attributes))

        label_cnt = 1
        for i in range(len(gestures)):
            gesture_measurements = gestures[i][1]
            # append label count as prefix, because labels are internally lexicographically sorted.
            # Label count must be 4 digit number, because 1 must be before 10 (0001 is before 0010).
            gesture_name = str(label_cnt).zfill(4) + gestures[i][0]
            label_cnt += 1

            # frame is vector of attributes at each time frame. size must match training set dimension
            for frame in gesture_measurements:
                extracted_attributes = SensorDataController.extract_data(frame, self.__data_types)
                training_set.recordPhrase(i, extracted_attributes)
            training_set.setPhraseLabel(i, xmm.Label(gesture_name))

        self.__model.set_trainingSet(training_set)

        self.__model.train()

        self.__model.performance_init()

    def update(self, gesture):
        # extract attributes that we want to use
        extracted = SensorDataController.extract_data(gesture, self.__data_types)
        # update model with extracted data
        self.__model.performance_update(xmm.vectorf(extracted))

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
