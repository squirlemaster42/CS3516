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
                if message.curTime < self.loggingQueue[i].curTime:
                    self.loggingQueue.insert(i, message)
                    break

    def logWorker(self):
        t = time.time()
        self.logMessage(Message(t, "--------Starting Logger--------"))
        while self.logging:
            if not len(self.loggingQueue) == 0:
                msg = self.loggingQueue.pop()
                timeStr = time.localtime(msg.curTime)
                print(msg.message, file=sys.stderr)

    def stop(self):
        self.logging = False
        self.thread.join()


def handleConenction(client, address, lock):
    lock.acquire()
    global connectedClients
    connectedClients += 1
    lock.release()
    try:
        if connectedClients > maxConnections:
            client.close()
            logger.logMessage(Message(time.time(), "Error: too many requests"))
            lock.acquire()
            connectedClients -= 1
            lock.release()
            return

        receivedData = client.recv(1024)

        if not receivedData.find(b'\r\n\r\n') >= 1:
            print(receivedData.find(b'\r\n\r\n'))
            print(receivedData)
            print(receivedData.decode("utf-8"))
            logger.logMessage(Message(time.time(), "Error: unexpected end of input"))
            client.close()
            lock.acquire()
            connectedClients -= 1
            lock.release()
            return

        splitRec = receivedData.split(b'\r\n')
        for d in splitRec:
            if b'X-additional-wait:' in d:
                try:
                    waitTime = int(d.split(b' ')[1])
                except:
                    logger.logMessage(Message(time.time(), "Error: invalid headers"))
                    client.close()
                    lock.acquire()
                    connectedClients -= 1
                    lock.release()
                    return

                time.sleep(waitTime)
        try:
            reqType = receivedData.split()[0].decode("utf-8")
        except ValueError:
            logger.logMessage(Message(time.time(), "Error: invalid input character"))
            client.close()
            lock.acquire()
            connectedClients -= 1
            lock.release()
            return

        if 'GET' not in reqType:
            client.close()
            logger.logMessage(Message(time.time(), "Error: invalid request line"))
            lock.acquire()
            connectedClients -= 1
            lock.release()
            return
        try:
            filename = receivedData.split()[1].decode("utf-8")
        except ValueError:
            logger.logMessage(Message(time.time(), "Error: invalid input character"))
            client.close()
            lock.acquire()
            connectedClients -= 1
            lock.release()
            return

        if ".." in filename or filename.count("/") > 1:
            client.send(errmsg.encode())
            client.close()
            logger.logMessage(Message(time.time(), "Error: invalid path"))
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
        client.close()
        lock.acquire()
        connectedClients -= 1
        lock.release()
        logger.logMessage(Message(time.time(), "Success: served file " + filename))

    except socket.timeout:
        logger.logMessage(Message(time.time(), "Error: socket recv timed out"))
        client.close()
        lock.acquire()
        connectedClients -= 1
        lock.release()


def startServer():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((ip, port))
    sock.listen(maxQueue)
    lock = threading.Lock()

    try:
        while 1:
            newSocket, address = sock.accept()
            global timeout
            newSocket.settimeout(timeout)
            logger.logMessage(Message(time.time(), "Information: received new connection from, " + str(address[0]) + ", port " + str(port)))
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
