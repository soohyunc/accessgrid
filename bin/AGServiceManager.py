#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        AGServiceManager.py
# Purpose:     
# Created:     2003/08/02
# RCS-ID:      $Id: AGServiceManager.py,v 1.38 2004-03-18 21:42:38 eolson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

# The standard imports
import sys

if sys.platform=="darwin":
    # On osx pyGlobus/globus need to be loaded before various modules such as socket.
    import pyGlobus.ioc

import signal, time, os

if sys.version.startswith('2.2'):
    try:
        from optik import Option
    except:
        raise Exception, "Missing module optik necessary for the AG Toolkit."

if sys.version.startswith('2.3'):
    try:
        from optparse import Option
    except:
        raise Exception, "Missing module optparse, check your python installation."

# Our imports
from AccessGrid.hosting import Server
from AccessGrid.Toolkit import CmdlineApplication
from AccessGrid.Platform import PersonalNode, isLinux
from AccessGrid.Platform.Config import UserConfig, AGTkConfig, SystemConfig
from AccessGrid.AGServiceManager import AGServiceManager, AGServiceManagerI
from AccessGrid.Platform import PersonalNode
from AccessGrid import Toolkit

# default arguments
log = None
serviceManager = None
server = None

# Signal handler to shut down cleanly
def SignalHandler(signum, frame):
    """
    SignalHandler catches signals and shuts down the VenueServer (and
    all of it's Venues. Then it stops the hostingEnvironment.
    """
    global log, serviceManager, running

    log.info("Caught signal, going down.")
    log.info("Signal: %d Frame: %s", signum, frame)

    serviceManager.Shutdown()
    running = 0
    
def main():
    """
    """
    global serviceManager, log

    # Create the app
    app = CmdlineApplication()
    
    # build options for this application
    portOption = Option("-p", "--port", type="int", dest="port",
                        default=12000, metavar="PORT",
                        help="Set the port the service manager should run on.")
    app.AddCmdLineOption(portOption)
    pnodeOption = Option("--pnode", dest="pnode", metavar="PNODE_TOKEN",
                         help="Personal node rendezvous token.")
    app.AddCmdLineOption(pnodeOption)
    
    # Initialize the application
    try:
        args = app.Initialize("ServiceManager")
    except Exception, e:
        print "Toolkit Initialization failed, exiting."
        print " Initialization Error: ", e
        sys.exit(-1)

    log = app.GetLog()
    pnode = app.GetOption("pnode")
    port = app.GetOption("port")
        
    # Create the hosting environment
    hostname = SystemConfig.instance().GetHostname()
    server = Server((hostname, port))

    # Create the Service Manager
    serviceManager = AGServiceManager(server)

    # Create the Service Manager Service
    smi = AGServiceManagerI(serviceManager)
    server.RegisterObject(smi,path="/ServiceManager")
    url = server.FindURLForObject(serviceManager)

    # If we are starting as a part of a personal node,
    # initialize that state.

    if pnode is not None:
        personalNode = PersonalNode.PN_ServiceManager(url, serviceManager.Shutdown)
        personalNode.Run(pnode)

    # Register the signal handler so we can shut down cleanly
    signal.signal(signal.SIGINT, SignalHandler)
    if isLinux():
        signal.signal(signal.SIGHUP, SignalHandler)

    # Start the service
    server.RunInThread()

    # Tell the world where to find the service manager
    log.info("Starting Service Manager URI: %s", url)

    # Keep the main thread busy so we can catch signals
    global running
    running = 1
    while running:
        time.sleep(1)

    # Exit cleanly
    server.Stop()
    sys.exit(0)
    
if __name__ == "__main__":
    main()
