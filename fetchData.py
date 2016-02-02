from threading import Thread
from time import sleep
from collections import deque
import socket
import struct
import time
import sys
import readchar

import matplotlib

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

PORT = 10337
MODE = 0  # 0 is playing, 1 is recording, 2 is quitting

PLAYING_QUEUE_SIZE = 600
ABS_Y_AXIS = 250

PLOTTING_FPS = 0.06


def unpack_raw(data):
    return struct.unpack(">iiiiiiiii", data[32:-4])


def unpack_eul(data):
    return struct.unpack(">ffff", data[20:])


def unpack_quat(data):
    return struct.unpack(">ffff", data[16:])


def convert_acce_to_units(val):
    return 8.0 * val / 32768.0


def convert_gyro_to_units(val):
    return 2000.0 * val / 28571.4


def convert_compass_to_units(val):
    return 2.0 * val / 25000.0


def format_and_write_to_file(data, file_pointer):
    result = str(time.time()) + ","
    raw = ""
    eul = ""
    quat = ""
    while len(raw) == 0 or len(eul) == 0 or len(quat) == 0:
        if data[:6] == "/1/raw":
            if len(raw) == 0:
                raw += "RAW,"
                for d in unpack_raw(data):
                    raw += str(d) + ','
        elif data[:6] == "/1/eul":
            if len(eul) == 0:
                eul += "EUL,"
                for d in unpack_eul(data):
                    eul += str(d) + ','
        elif data[:6] == "/1/qua":
            if len(quat) == 0:
                quat += "QUAT,"
                for d in unpack_quat(data):
                    quat += str(d) + ','
    result = result + raw + eul + quat
    file_pointer.write(result[:-1] + "\n")


def read_char():
    global MODE
    while True:
        input_char = readchar.readchar()
        if input_char == 'r':
            MODE = 1
            print "Started recording"
            sleep(3)
            print "Stopped recording"
            MODE = 0
        elif input_char == 'p':
            MODE = 0
            print "Entered playing mode"
        elif input_char == 'q':
            MODE = 2
            print "Quitting"
            sys.exit()


if __name__ == "__main__":

    # start reading console in another thread
    thread = Thread(target=read_char, args=())
    thread.start()

    try:
        # prepare sensor connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(0)
        sock.bind(("0.0.0.0", PORT))
    except Exception as e:
        print e
        sys.exit()

    # gestures helper
    recorded_gestures = []
    current_gesture = []
    circular_queue = deque([(0, 0, 0) for i in range(0, 600)], PLAYING_QUEUE_SIZE)

    fig1 = plt.figure()
    subplot_x = fig1.add_subplot(221)
    plt.axis((0, PLAYING_QUEUE_SIZE, -ABS_Y_AXIS, ABS_Y_AXIS))
    subplot_y = fig1.add_subplot(222)
    plt.axis((0, PLAYING_QUEUE_SIZE, -ABS_Y_AXIS, ABS_Y_AXIS))
    subplot_z = fig1.add_subplot(223)
    plt.axis((0, PLAYING_QUEUE_SIZE, -ABS_Y_AXIS, ABS_Y_AXIS))

    # some X and Y data
    x = range(0, PLAYING_QUEUE_SIZE)
    y = [0] * PLAYING_QUEUE_SIZE

    plt.ion()
    subplot_x, = subplot_x.plot(x, y, "-")
    subplot_y, = subplot_y.plot(x, y, "-")
    subplot_z, = subplot_z.plot(x, y, "-")

    # draw and show it
    fig1.canvas.draw()
    plt.show()

    prev_time = time.time()
    # start receiving data in this thread
    while True:
        try:
            sensor_data, x = sock.recvfrom(1024)

            if sensor_data[:6] == "/0/eul":
                euler_raw = unpack_eul(sensor_data)
                print "\rEulers:", "%5.2f\t%5.2f\t%5.2f\t\t" % (euler_raw[0], euler_raw[1], euler_raw[2]),
                if MODE == 1:
                    current_gesture.append(euler_raw)
                elif MODE == 0:
                    """if len(current_gesture) > 0:
                        recorded_gestures.append(current_gesture)
                        current_gesture = []
                    """
                    circular_queue.append(euler_raw)

                    # draw only every 10th change
                    if time.time() - prev_time > PLOTTING_FPS:
                        prev_time = time.time()
                        subplot_x.set_ydata([a[0] for a in circular_queue])
                        subplot_y.set_ydata([a[1] for a in circular_queue])
                        subplot_z.set_ydata([a[2] for a in circular_queue])
                        fig1.canvas.draw()
                elif MODE == 2:
                    break

        except socket.error as e:
            if e[0] != 35:
                print e

    sock.close()
    sys.exit()
