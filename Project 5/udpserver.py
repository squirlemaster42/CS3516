import argparse
import socket
import random
import time


class Server:

    def __init__(self, port, lossprob, mindelay, maxdelay):
        self.port = port
        self.lossprob = lossprob
        self.mindelay = mindelay
        self.maxdelay = maxdelay

    def startServer(self):
        udpServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        udpServerSocket.bind(("127.0.0.1", self.port))
        while True:
            input = udpServerSocket.recvfrom(1024)
            message = input[0]
            address = input[1]

            # Drop packet
            if random.random() < self.lossprob:
                continue

            time.sleep(random.uniform(self.mindelay, self.maxdelay) / 1000)

            udpServerSocket.sendto(message, address)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--lossprob", default=0, type=float)  # set min/max
    parser.add_argument("--mindelay", default=0, type=int)
    parser.add_argument("--maxdelay", default=0, type=int)
    parser.add_argument("--port", default=12000, type=int)
    args = parser.parse_args()
    server = Server(args.port, args.lossprob, args.mindelay, args.maxdelay)
    server.startServer()
