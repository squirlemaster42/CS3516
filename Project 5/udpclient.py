import argparse
import socket
import time


def timeMillis():
    return int(round(time.time() * 1000))


class Client:

    def __init__(self, port, timeout, server):
        self.port = port
        self.timeout = timeout
        self.server = server
        self.address = (server, port)

    def startClient(self):
        udpClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        udpClientSocket.settimeout(self.timeout / 1000)
        pings = list()
        completedPings = list()

        for i in range(0, 10):
            try:
                startTime = timeMillis()
                udpClientSocket.sendto(str.encode(str(i)), self.address)
                serverMessage = udpClientSocket.recvfrom(1024)
                endTime = timeMillis()
                pings.append(endTime - startTime)
                completedPings.append(endTime - startTime)
                print("Ping %d: %dms" % (i + 1, endTime - startTime))
            except socket.timeout:
                print("Ping %d: Request timed out" % (i + 1))
                pings.append(-1)

        pings.sort()
        completedPings.sort()
        minTime = completedPings[0]
        maxTime = completedPings[-1]
        totalTime = 0
        validPings = 0
        for i in completedPings:
            if i != -1:
                totalTime += i
                validPings += 1
        average = totalTime / validPings
        lossRate = 100 - ((validPings / len(pings)) * 100)
        print("RTT: minimum: %dms; maximum %dms; average: %dms\nPacket loss rate: %d%%" % (minTime, maxTime, average, lossRate))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", default=3000, type=int)
    parser.add_argument("--port", default=12000, type=int)
    parser.add_argument("--server", default="127.0.0.1", type=str)
    args = parser.parse_args()
    client = Client(args.port, args.timeout, args.server)
    client.startClient()
