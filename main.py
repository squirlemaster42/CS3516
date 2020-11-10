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
timeout = 10


class Message:
    def __init__(self, curTime, message):
        self.curTime = curTime
        self.message = message


class Logger:
    loggingQueue = []
    logLock = threading.Lock()
    logging = False

    def __init__(self):
        self.thread = threading.Thread(target=self.logWorker)
        self.logging = True
        self.thread.start()

    def logMessage(self, message):
        with self.logLock:
            if len(self.loggingQueue) == 0:
                self.loggingQueue.append(message)
                return
            for i in range(len(self.loggingQueue)):
                if message.time < self.loggingQueue[i]:
                    self.loggingQueue.insert(i, message)
                    break

    def logWorker(self):
        t = time.time()
        self.logMessage(Message(t, "--------Starting Logger--------"))
        while self.logging:
            if not len(self.loggingQueue) == 0:
                msg = self.loggingQueue.pop()
                # Need to change message to include timestamp
                timeStr = time.strftime('[%Y-%m-%d %H:%M:%S]', time.localtime(msg.curTime))
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
    if connectedClients > maxConnections:
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
    try:
        f = open(filename[1:])
    except FileNotFoundError:
        client.send(errmsg.encode())
        client.close()
        lock.acquire()
        connectedClients -= 1
        lock.release()
        return
    outputdata = f.read()
    f.close()
    client.send(response10.encode())
    client.send(outputdata.encode())
    # Send disconnect message
    client.close()
    lock.acquire()
    connectedClients -= 1
    lock.release()
    logger.logMessage(Message(time.time(), "Disconnected from " + str(address)))


def startServer():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((ip, port))
    sock.listen(maxQueue)
    lock = threading.Lock()

    try:
        while 1:
            newSocket, address = sock.accept()
            logger.logMessage(Message(time.time(), "Connection from " + str(address)))
            thread = threading.Thread(target=handleConenction, args=[newSocket, address, lock])
            thread.start()
    finally:
        sock.close()


if __name__ == '__main__':
    # Check args
    arguments = len(sys.argv)

    for i in range(1, arguments, 2):
        arg = sys.argv[i]
        if "--port" in arg:
            print("Found Port")
            port = int(sys.argv[i + 1])
            print(port)
        elif "--maxrq" in arg:
            print("Found MaxRQ")
            maxConnections = int(sys.argv[i + 1])
            print(maxConnections)
        elif "--timeout" in arg:
            print("Found Timeout")
            timeout = int(sys.argv[i + 1])
            print(timeout)

    logger = Logger()
    t = time.time()
    logger.logMessage(Message(t, "-------- Started Server --------"))
    startServer()
