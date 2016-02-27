import matplotlib.pyplot as plt

from Domain.Plot import Plot


class PlotController:
    def __init__(self, subplot_cnt, plotting_queue_size=400, abs_y_axis=200):
        # set plotting in non blocking interactive mode
        plt.ion()
        # create figure
        self.__figure = plt.figure()

        self.__subplots = []

        # optimal grid size is ceiled subplot_cnt / 2 x subplot_cnt / 2
        grid_size = 1

        # construct subplots
        for i in range(subplot_cnt):
            subplot = self.__figure.add_subplot(grid_size, grid_size, i + 1)
            plt.axis((0, plotting_queue_size, -abs_y_axis, abs_y_axis))
            self.__subplots.append(Plot(plotting_queue_size, subplot,
                                        [("r", "a"), ("b", "b"), ("g", "c")]))
        plt.legend()
        plt.show()

    def update_subplot(self, subplot_index, new_data):
        """
        Updates subplot at index subplot_index with new data.
        :param subplot_index: Starts at 0
        :param new_data: Vector of attributes
        :return:
        """
        self.__subplots[subplot_index].update_plot(new_data)

    def redraw(self):
        self.__figure.canvas.draw()
        # hack to unfreeze canvas
        plt.pause(0.0001)
