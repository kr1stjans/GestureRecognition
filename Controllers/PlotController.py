import matplotlib.pyplot as plt

from Domain.Plot import Plot


class PlotController:
    def __init__(self, subplot_cnt, plotting_queue_size=400, abs_y_axis=200):
        # set plotting in non blocking interactive mode
        plt.ion()
        # create figure
        self.__figure = plt.figure()

        self.__subplots = []

        # get optimal grid size
        grid_size = self.calculate_grid(subplot_cnt)

        # construct subplots
        for i in range(subplot_cnt):
            subplot = self.__figure.add_subplot(grid_size[0], grid_size[1], i + 1)
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

    @staticmethod
    def calculate_grid(subplot_cnt):
        """
        Supports grid of max 4 x 4 = 16.
        :param subplot_cnt:
        :return:
        """
        for i in range(1, 4):
            for j in range(1, 4):
                if i * j <= subplot_cnt:
                    return i, j
