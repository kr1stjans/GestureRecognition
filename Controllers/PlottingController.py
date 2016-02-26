from collections import deque


class PlottingController:
    def __init__(self, size, canvas, params):
        self.__size = size
        self.__canvas = canvas
        self.__plots = []
        self.__queue_handles = [deque([0] * size, size) for _ in params]
        for i in range(len(params)):
            self.__plots.append(self.__canvas.plot(self.__queue_handles[i], params[i][0], label=params[i][1])[0])

    def update_plot(self, data):
        for i in range(len(data)):
            self.__queue_handles[i].append(data[i])
            self.__plots[i].set_ydata(self.__queue_handles[i])
