import sys
import os
import multiprocessing
import argparse
from os import listdir
from os.path import isfile, join

from scapy.all import *
from scapy.layers.dns import DNSRR, DNS


def printVerbOne(cloaking):
    if cloaking:
        print("CNAME cloaking detected")
    else:
        print("CNAME cloaking not detected")


def printVerbTwo(cloaking, site):
    if cloaking:
        print(site + ": CNAME cloaking detected")
    else:
        print(site + ": CNAME cloaking not detected")


def printVerbThree(cloaking, siteName, cloaks):
    if cloaking:
        print(siteName + ": CNAME cloaking detected:")
        output = ""
        for i in range(len(cloaks)):
            output += "(" + siteName + " -> " + cloaks.pop() + "),\n"
        print(output[:-2])
    else:
        print(siteName + ": CNAME cloaking not detected")


class Processor:

    def __init__(self, files, folder, procs, verbosity):
        self.folder = folder
        self.procs = procs
        self.verbosity = verbosity

        manager = multiprocessing.Manager()
        self.cloakingDetected = manager.list()

        with multiprocessing.Pool(self.procs) as p:
            p.map(self.processFile, files)

        if verbosity == 1:
            printVerbOne(len(self.cloakingDetected) > 0)

    def processFile(self, fName):
        print("Processing", fName)
        splitFName = fName.split("/")
        siteName = splitFName[len(splitFName) - 1].replace(".pcap", "")
        thirdParty = set()
        packets = 0
        try:
            packets = rdpcap(self.folder + fName)
        except Scapy_Exception:
            print(fName + " Invalid PCAP trace")
            return
        for p in packets:
            if DNSRR in p:
                if p.an.type == 5 and not (siteName in p.an.rdata.decode("utf-8")):
                    self.cloakingDetected.append(True)
                    thirdParty.add(p.an.rdata.decode("utf-8"))
                    # Change var that redirection was found

        if self.verbosity == 2:
            printVerbTwo(not len(thirdParty) == 0, siteName)
        elif self.verbosity == 3:
            printVerbThree(not len(thirdParty) == 0, siteName, thirdParty)


def main():
    verbosity = 2
    processes = 2
    folder = "./"
    arguments = len(sys.argv)

    for i in range(1, arguments, 2):
        arg = sys.argv[i]
        if "--verbosity" in arg:
            print("Found Verbosity")
            verbosity = int(sys.argv[i + 1])
        elif "--processes" in arg:
            print("Found Processes")
            processes = int(sys.argv[i + 1])
        elif "--folder" in arg:
            print("Found Folder")
            folder = sys.argv[i + 1]

    onlyfiles = [f for f in listdir("pcaps/") if isfile(join("pcaps/", f))]
    onlypcaps = []
    for f in onlyfiles:
        if ".pcap" in f:
            onlypcaps.append(f)
        elif verbosity == 2 or verbosity == 3:
            print(f + " Invalid PCAP trace")
            pass

    p = Processor(onlypcaps, folder, processes, verbosity)


if __name__ == '__main__':
    main()
