import socket
import struct
import time

COMPUTER_IP = "192.168.1.110"
PORT = 0


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


if __name__ == "__main__":
    # open socket to and receive sensor data
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((COMPUTER_IP, PORT))

    gyro_euler = [0., 0., 0.]
    prev_gyro_euler = [0., 0., 0.]
    gyro_avg = [0., 0., 0.]
    measure_cnt = 0
    last_timestamp = time.time()

    while True:
        print "here"
        sensor_data, _ = sock.recvfrom(1024)
        if sensor_data[:6] == "/1/raw":
            timestamp = time.time()
            raw_data = unpack_raw(sensor_data)
            # get acceleration in m/s^2
            acce = map(convert_acce_to_units, raw_data[:3])
            # get angular velocity in degrees per second
            gyro_euler_read = map(convert_gyro_to_units, raw_data[3:6])

            # account for measured error when sensor isn't moving
            # Measurement 1: 1.057227	-3.283120	-3.786003)
            # Measurement 2: 1.113599	-3.320273	-3.748888)
            """gyro_euler_read[0] += 0.278754
            gyro_euler_read[1] += 3.983473
            gyro_euler_read[2] += 3.755614"""

            for i in range(3):
                # integrate values by time
                gyro_euler[i] += (gyro_euler_read[i] + prev_gyro_euler[i]) / 2.0 * (timestamp - last_timestamp)
                # average
                gyro_avg[i] += gyro_euler_read[i]

            last_timestamp = timestamp
            prev_gyro_euler = gyro_euler_read
            measure_cnt += 1

            #print "\rAcce:", "%5.2f\t%5.2f\t%5.2f\t\t" % tuple(acce), "Gyro:", "%5.2f\t%5.2f\t%5.2f" % tuple(gyro_euler_read), "Error:", "%5f\t%5f\t%5f" % tuple(map(lambda a: a / measure_cnt, gyro_avg)),
            print "\rAcce:", "%5d\t%5d\t%5d\t\t" % acce, "Gyro:", "%5d\t%5d\t%5d" % gyro, max_acce, max_gyro,
            # print "\rGyro:", "%5.2f\t%5.2f\t%5.2f" % tuple(gyro_euler),