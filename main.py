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
maxConnections = 10
connectedClients = 0


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
        print("Got message")
        with self.logLock:
            if(len(self.logginQueue) == 0):
                self.loggingQueue.append(message)
                return
            for i in range(len(self.loggingQueue)):
                if message.time < self.loggingQueue[i]:
                    print("Message Added")
                    self.loggingQueue.insert(i, message)
                    break

    def logWorker(self):
        while self.logging:
            if not len(self.loggingQueue) == 0:
                msg = self.loggingQueue.pop()
                # Need to change message to include timestamp
                timeStr = time.strftime('[%Y-%m-%d %H:%M:%S]', time.localtime(msg.time))
                print(timeStr, msg.message, file=sys.stderr)

    def stop(self):
        self.logging = False
        self.thread.join()


# TODO Change messages to use logger
def handleConenction(client, address, lock):
    lock.acquire()
    global connectedClients
    connectedClients += 1
    lock.release()
    if(connectedClients > maxConnections):
        client.close()
        return
    receivedData = client.recv(1024)
    if not receivedData:
        return  # Handle Error Better
    splitRec = receivedData.split(b'\r\n')
    for d in splitRec:
        if b'X-additional-wait:' in d:
            waitTime = int(d.split(b' ')[1])
            time.sleep(waitTime)
    filename = receivedData.split()[1].decode("utf-8")
    if ".." in filename or filename.count("/") > 1:
        client.send(errmsg.encode())
        client.close()
        lock.acquire()
        connectedClients -= 1
        lock.release()
        return
    f = open(filename[1:])
    outputdata = f.read()
    f.close()
    client.send(response10.encode())
    client.send(outputdata.encode())
    # Send disconnect message
    client.close()
    lock.acquire()
    connectedClients -= 1
    lock.release()
    print("Disconnected from", address)


def startServer():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((ip, port))
    sock.listen(maxQueue)
    lock = threading.Lock()

    try:
        while 1:
            newSocket, address = sock.accept()
            print("Connection from", address)
            thread = threading.Thread(target=handleConenction, args=[newSocket, address, lock])
            thread.start()
    finally:
        sock.close()


if __name__ == '__main__':
    print("-------- Starting Server --------")
    logger = Logger()
    startServer()
    logger.logMessage(Message(time.localtime(), "Started Server"))
