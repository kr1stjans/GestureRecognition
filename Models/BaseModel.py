import xmm
from Controllers.SensorDataController import SensorDataController


class BaseModel:
    def __init__(self, model, likelikehood_window=5, nb_mix_comp=10, rel_var_offset=1., abs_var_offset=0.01,
                 data_types=('raw_acc', 'raw_rot')):
        """
        :param likelikehood_window:
        :param nb_mix_comp:
        :param rel_var_offset:
        :param abs_var_offset:
        :return:
        """
        self.__model = model
        self.__model.set_nbMixtureComponents(nb_mix_comp)
        self.__model.set_varianceOffset(rel_var_offset, abs_var_offset)
        self.__model.set_likelihoodwindow(likelikehood_window)
        self.__data_types = data_types

    def train(self, recorded_gestures_map):
        """
        :param recorded_gestures_map: map where key is gestures group name
        and value is 2D array where rows are measurements and columns are attributes
        :return:
        """

        training_set = xmm.TrainingSet()
        # get array of gestures for first gesture name
        first_gestures_list = recorded_gestures_map.itervalues().next()
        # get first gesture
        first_gesture = first_gestures_list[0]
        # get first measurement
        first_measurement = first_gesture[0]
        # get relevant attributes
        extracted_attributes = SensorDataController.extract_data(first_measurement, self.__data_types)
        # length of the extracted attributes is the dimension of the model
        training_set.set_dimension(len(extracted_attributes))

        gesture_cnt = 1
        for name, gestures_group in recorded_gestures_map.iteritems():
            name = str(gesture_cnt).zfill(4) + name
            for gesture in gestures_group:
                # frame is vector of attributes at each time frame. size must match training set dimension
                for frame in gesture:
                    extracted_attributes = SensorDataController.extract_data(frame, self.__data_types)
                    training_set.recordPhrase(gesture_cnt, extracted_attributes)
                training_set.setPhraseLabel(gesture_cnt, xmm.Label(name))
            gesture_cnt += 1

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
            print "Number of models: ", self.__model.size(), "\r"

            for label in self.__model.models.keys():
                print "Model", label.getSym(), ": trained in ", self.__model.models[
                    label].trainingNbIterations, "iterations, loglikelihood = ", self.__model.models[
                    label].trainingLogLikelihood, "\r"
        else:
            print "Model not yet trained.\r"
