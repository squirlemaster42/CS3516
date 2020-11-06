import socket
import threading
import sys
import time

errmsg = 'HTTP/1.1 404 NOT FOUND\r\n\r\n'
response10 = 'HTTP/1.0 200 OK\r\n\r\n'
response11 = 'HTTP/1.1 200 OK\r\n\r\n'
ip = "localhost"
port = 8080
maxQueue = 5


class Message:
    def __init__(self, time, message):
        self.time = time
        self.message = message


class Logger:
    loggingQueue = []
    logLock = threading.Lock()
    logging = False

    def __init__(self):
        print("--------Starting Logger--------")
        self.thread = threading.Thread(target=self.logWorker)
        self.thread.start()
        self.logging = True

    def logMessage(self, message):
        with self.logLock:
            for i in range(len(self.loggingQueue)):
                if message.time < self.loggingQueue[i]:
                    self.loggingQueue.insert(i, message)
                    break

    def logWorker(self):
        while self.logging:
            if not len(self.loggingQueue) == 0:
                msg = self.loggingQueue.pop()
                print(msg.message, file=sys.stderr)

    def stop(self):
        self.logging = False
        self.thread.join()


def startServer():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((ip, port))
    sock.listen(maxQueue)

    try:
        while 1:
            newSocket, address = sock.accept()
            print("Connection from", address)
            while 1:  # Make Thread
                receivedData = newSocket.recv(1024)
                if not receivedData:
                    break
                print(receivedData)
                filename = receivedData.split()[1].decode("utf-8")
                f = open(filename[1:])
                outputdata = f.read()
                f.close()
                newSocket.send(response10.encode())
                newSocket.send(outputdata.encode())
                break
            newSocket.close()
            print("Disconnected from", address)
    finally:
        sock.close()


if __name__ == '__main__':
    print("-------- Starting Server --------")
    logger = Logger()
    startServer()
