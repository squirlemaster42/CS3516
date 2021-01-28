#!/usr/bin/python

import _thread
import time


def printTime(threadName, delay):
    print("Here")
    count = 0
    while count < 5:
        time.sleep(delay)
        count += 1
        print("%s: %s" % (threadName, time.ctime(time.time())))


if __name__ == '__main__':
    print("Hello")
    try:
        print("Here")
        _thread.start_new_thread(printTime, ("Thread1", 2,))
        _thread.start_new_thread(printTime, ("Thread2", 4,))
    except:
        print("Unable to start thread")

while 1:
    pass