#!/usr/bin/python

import os, sys, time
import urllib
import socket
import traceback
import random
from optparse import Option
from DocXMLRPCServer import DocXMLRPCServer 
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler, SimpleXMLRPCDispatcher

from AccessGrid.AGXMLRPCServer import AsyncAGXMLRPCServerThreaded
from AccessGrid.Toolkit import CmdlineApplication

defaultPort = 8030
defaultPeerListUrl = "http://www.accessgrid.org/registry/peers.txt"
log = None

class RegistryInterface:

    # Bridge Interface, accepts a BridgeDescription
    # Returns the amount of time before the registration expires.
    def RegisterBridge(self, bridgeDescription):
        return 0     # Returns the number of seconds before it needs to update

    # Client Interface
    def LookupBridge(self, maxToReturn=None):
        pass

    def Ping(self, data): # Returns whatever data was sent, likely the time sent.
        return data

    # Peer Interface
    def PeerUpdate(self, data):
        pass

class RegistryBase(RegistryInterface):
    defaultSecondsBetweenBridgeCleanups = 30
    defaultRegistrationLengthSecs = 120
    def __init__(self, port, peerListUrl=""):
        self.port = port
        self.host = ""
        self.peerUpdateInterval = 3 # 60  # seconds
        self.peerListUrl = peerListUrl
        self.registryPeers = []
        self.localPeerAddr = None
        if peerListUrl.startswith("file://"):
            self._readPeerListLocalTest(self.peerListUrl[7:])
        else:
            self._readPeerList(url=self.peerListUrl)
        self.secondsBetweenBridgeCleanups = self.defaultSecondsBetweenBridgeCleanups
        self.nextBridgeCleanupTime = time.time() + self.secondsBetweenBridgeCleanups
        self.registrationLengthSecs = self.defaultRegistrationLengthSecs
        self.registeredBridges = {}

    def _readPeerList(self,url):
        opener = urllib.FancyURLopener({})
        f = opener.open(url)
        contents = f.read()
        f.close()
        registryPeers = contents.split()
        fqdn = socket.getfqdn(socket.gethostname())
        localPeerName = fqdn + ":%s" % self.port
        if localPeerName not in registryPeers:
            raise Exception ("Error: this peer " + localPeerName + " is not listed in the master list.  The current registry requires all peers to know about each other.")
        registryPeers.remove(localPeerName)
        self.host = localPeerName
        self.registryPeers = registryPeers

    def _readPeerListLocalTest(self,filename):
        opener = urllib.FancyURLopener({})
        #f = opener.open(url)
        f = open(filename, "r")
        contents = f.read()
        f.close()
        registryPeers = contents.split() # split by line
        # make list of (host,port)
        def makeHostPortListFromString(peerList):
            peers = []
            for peer in peerList:
                splitPeer = peer.split(":")
                peers.append( (splitPeer[0], int(splitPeer[1])) )
            return peers
        registryPeers = makeHostPortListFromString(registryPeers)

        # for local test, just find the peer with the same port
        localPeerAddr = ""
        for peer in registryPeers:
            if peer[1] == self.port:
                localPeerAddr = peer

        if localPeerAddr not in registryPeers:
            raise Exception ("Error: this peer " + localPeerAddr + " is not listed in the master list.  The current registry requires all peers to know about each other.")
        registryPeers.remove(localPeerAddr)
        ##print "localPeer:", localPeerAddr
        ##print "otherPeers:", registryPeers

        self.registryPeers = []

    def _CleanupBridges(self):
        bridgesToRemove = []
        now = time.time()
        for key in self.registeredBridges.keys():
            expirationTime = self.registeredBridges[key][1]
            if now > expirationTime:
                #print "removing bridge:", key
                #log.info("removing bridge: %s" % key)
                bridgesToRemove.append(key)
        for bridge in bridgesToRemove:
            self.registeredBridges.pop(bridge)

    def _UpdateCallback(self):
        if time.time() > self.nextBridgeCleanupTime:
            self._CleanupBridges()
            self.nextBridgeCleanupTime = time.time() + self.secondsBetweenBridgeCleanups

        # self._RefreshPeerList()

    def _StoreBridgeDescription(self, bridgeDescriptionDict, expirationTime):
        # The function to actually store bridge data that is registered.
        # For now stored based on host and port.
        self.registeredBridges[(bridgeDescriptionDict["host"], bridgeDescriptionDict["port"])] = (bridgeDescriptionDict, expirationTime)

    def RefreshPeerList(self, url=None):
        # Allows a running peer to refresh its peer list in case a peer has been manually added or removed.
        # Call to this function probably would be initiated manually.
        if url == None:
            url = self.peerListUrl
        self._readPeerList(url)

    def ConnectToRegistries(self):
        for peer in self.registryPeers:
            try:
                #print "Would connect to:", peer
                pass
            except Exception:
                traceback.print_exc()

    def RandomBridgeLookup(self, maxToReturn=None):
        keys = self.registeredBridges.keys()
        if maxToReturn == None or maxToReturn==0:
            numToReturn = len(keys)
        else:
            numToReturn = min(maxToReturn, len(keys))
        serversToReturn = []
        for i in range(numToReturn):
            key = keys[random.randrange(len(keys))]
            #print "Key:", key
            keys.remove(key)
            serversToReturn.append(self.registeredBridges[key][0])
        return serversToReturn 

    LookupBridge = RandomBridgeLookup

class RegistryPeerXMLRPC(RegistryBase):
    def __init__(self, port, peerListUrl):
        RegistryBase.__init__(self, port, peerListUrl)
        self.requestServer = AsyncAGXMLRPCServerThreaded( ("", self.port), intervalSecs=1, callback=self._UpdateCallback )
        self._RegisterFunctions()

    def _RegisterFunctions(self):
        self.requestServer.register_function(self.LookupBridge, "LookupBridge")
        self.requestServer.register_function(self.RegisterBridge, "RegisterBridge")
        self.requestServer.register_function(self.Ping, "Ping")

    def RegisterBridge(self, bridgeDescription):
        #print "Registering bridge:", bridgeDescription["host"], bridgeDescription["port"]
        expirationTime = time.time() + self.registrationLengthSecs
        self._StoreBridgeDescription(bridgeDescription, expirationTime)
        #print "bridges:", self.registeredBridges.keys()
        return self.registrationLengthSecs

    def Run(self):
        self.ConnectToRegistries()
        self.requestServer.run()

    def Stop(self):
        self.requestServer.stop()

RegistryPeer=RegistryPeerXMLRPC

def main():
    app = CmdlineApplication()

    portOption = Option("-p", "--port",
        type="int", dest="port",
        default=defaultPort, metavar="PORT",
        help="Set the port the RegistryPeer will use")
    app.AddCmdLineOption(portOption)

    urlOption = Option("-u", "--peerListUrl",
        type="string", dest="peerListUrl",
        default=defaultPeerListUrl, metavar="URL",
        help="The url to bootstrap the system. For the current design, this is a complete list of peers.")
    app.AddCmdLineOption(urlOption)

    try:
        args = app.Initialize("RegistryPeer")
    except Exception, e:
        print "Toolkit Initialization failed, exiting."
        print " Initialization Error: ", e
        sys.exit(-1)

    global log
    log = app.GetLog()
    peerListUrl = app.GetOption("peerListUrl")
    port = app.GetOption("port")

    log.info("Starting RegistryPeer with registry %s" % peerListUrl)
    log.info("Starting RegistryPeer at port %s" % port)
    r = RegistryPeer(peerListUrl=peerListUrl, port=port)
    r.Run()


if __name__ == "__main__":
    main()

