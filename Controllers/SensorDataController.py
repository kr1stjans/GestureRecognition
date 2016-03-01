import socket
import sys
import struct
import itertools
import time
from threading import Thread


class SensorDataController(Thread):
    def __init__(self, queue, port=10337, minimum_time_between_packets=0.05):
        """
        Init nonblocking socket from specified port.
        :param queue:
        :param port:
        :return:
        """
        super(SensorDataController, self).__init__()
        self.__port = port
        self.__queue = queue
        self.__recorded_data_stream = []
        self.__data_tuple = {}
        self.__receive = True
        self.__minimum_time_between_packets = minimum_time_between_packets

        try:
            # initialize UDP socket
            self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # make socket non-blocking
            self.__sock.setblocking(0)
            # bind to localhost
            self.__sock.bind(("0.0.0.0", self.__port))
        except Exception as e:
            # print any exception and exit
            print e
            sys.exit()

    def run(self):
        """
        Start receiving data.
        :return:
        """

        last_packet_timestamp = None

        # warm up. first few hundred packets are processed with delay
        for i in range(0, 5000):
            try:
                self.__sock.recvfrom(1024)
                last_packet_timestamp = time.time()
            except socket.error as e:
                # code 35 = no data ready exception when in non-blocking read
                if e[0] != 35:
                    print e

        print "Data receiving started.\r"

        while self.__receive:
            try:
                # read data if available
                sensor_data, _ = self.__sock.recvfrom(1024)
                if sensor_data[:6] == "/0/raw":
                    self.unpack_raw_to_map(sensor_data)
                elif sensor_data[:6] == "/0/eul":
                    self.unpack_eul_to_map(sensor_data)
                elif sensor_data[:6] == "/0/qua":
                    self.unpack_qua_to_map(sensor_data)

                # data tuple of length 15 means all three packets of data received
                if len(self.__data_tuple) == 15:

                    current_time = time.time()
                    time_between_packets = float(current_time) - float(last_packet_timestamp)

                    # if packets are arriving too slow, throw exception
                    if time_between_packets > self.__minimum_time_between_packets:
                        raise Exception(
                                "Packets arriving too slowly! Actual time between packets: " + str(
                                        time_between_packets) + ". Minimum allowed time between packets: " + str(
                                        self.__minimum_time_between_packets) + ". Please reboot the chip.\r")

                    # set last packet timestamp
                    last_packet_timestamp = current_time
                    # send data to main thread
                    self.__queue.put(self.__data_tuple.copy())
                    # clear collected data map
                    self.__data_tuple.clear()

            except socket.error as e:
                # code 35 = no data ready exception when in non-blocking read
                if e[0] != 35:
                    print e
        self.__sock.close()
        sys.exit()

    def stop(self):
        self.__receive = False

    def unpack_raw_to_map(self, data):
        unpacked = struct.unpack(">iiiiiiiii", data[32:-4])
        for i, data_type in enumerate(list(itertools.product(['acc', 'rot', 'mag'], ['x', 'y', 'z']))):
            self.__data_tuple['raw_' + data_type[0] + "_" + data_type[1]] = unpacked[i]

    def unpack_eul_to_map(self, data):
        unpacked = struct.unpack(">ffff", data[20:])
        for i, data_type in enumerate(list(['x', 'y', 'z'])):
            self.__data_tuple['eul_' + data_type] = unpacked[i]

    def unpack_qua_to_map(self, data):
        unpacked = struct.unpack(">ffff", data[16:])
        for i, data_type in enumerate(list(['x', 'y', 'z'])):
            self.__data_tuple['que_' + data_type] = unpacked[i]

    @staticmethod
    def convert_acce_to_units(val):
        return 8.0 * val / 32768.0

    @staticmethod
    def convert_gyro_to_units(val):
        return 2000.0 * val / 28571.4

    @staticmethod
    def convert_mag_to_units(val):
        return 2.0 * val / 25000.0

    @staticmethod
    def extract_data(data_map, data_types):
        """
        :param data_map: map of all data (raw, euler, quaternion)
        :param data_types: list of data types to include
        :return:
        """
        result = list()
        for k, v in data_map.iteritems():
            for d in data_types:
                if d in k:
                    result.append(v)
        return result
