#-----------------------------------------------------------------------------
# Name:        VenueServer.py
# Purpose:     This serves Venues.
#
# Author:      Ivan R. Judson, Thomas D. Uram
#
# Created:     2002/12/12
# RCS-ID:      $Id: VenueServer.py,v 1.14 2003-01-21 15:20:49 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

# Standard stuff
import sys
import ConfigParser
import socket
import string
from threading import Thread
import shelve
import signal

# AG Stuff
from AccessGrid.hosting.pyGlobus import ServiceBase
from AccessGrid import Venue
import CoherenceService
import GUID
import NetworkLocation
from MulticastAddressAllocator import MulticastAddressAllocator
import DataStore
import scheduler
from AccessGrid.Descriptions import VenueDescription

class VenueServer(ServiceBase.ServiceBase):
    """
    The Virtual Venue Server object is responsible for creating,
    destroying, and configuring Virtual Venue objects.

    The Virtual Venue Server object is:

    configFile : string
    config : dictionary of Key/Value pairs that holds configuration parameters.
    adminstrators : list of strings (each is a DN of a adminsitrative user)
    dataStorage : string
    defaultVenue : VenueURL
    hostingEnvironment : AccessGrid.hosting.pyGlobus.Server
    multicastAddressAllocator : AccessGrid.MulticastAddressAllocator
    venues : a list of Venues Objects that are being made available
    services : a list of service descriptions, these are either network or
               application services that are available so any venue hosted
               by this venue server can add these to the services available
               from within that venue
    houseKeeper : Scheduler
    """

    configDefaults = {
            "VenueServer.houseKeeperFrequency" : 30,
            "VenueServer.persistenceData" : 'VenueData',
            "CoherenceService.coherencePortBase" : 9000,
            "DataStorage.store" : 'Data/',
            "DataStorage.port" : 8892
            }

    def __init__(self, hostEnvironment = None, configFile=None):
        """
        The constructor creates a new Venue Server object, initializes
        that object, then registers signal handlers so the venue can cleanly
        shutdown in the event of catastrophic signals.
        """
        # Figure out which configuration file to use for the
        # server configuration. If no configuration file was specified
        # look for a configuration file named VenueServer.cfg
        # VenueServer is the value of self.__class__
        classpath = string.split(str(self.__class__), '.')
        if configFile == None:
            self.configFile = classpath[-1]+'.cfg'
        else:
            self.configFile = configFile

        # Instantiate a new config parser
        self.config = self.LoadConfig(self.configFile,
                                      self.configDefaults)

        # Initialize our state
        # We need to get the first administrator from somewhere
        self.administrators = [] 
        self.dataStorage = None
        self.defaultVenue = ''
        self.hostingEnvironment = hostEnvironment
        self.multicastAddressAllocator = MulticastAddressAllocator()
        self.venues = {}
        self.services = []
        self.coherencePort = self.config['CoherenceService.coherencePortBase']
        
        # Try to open the persistent store for Venues. If we fail, we
        # open a temporary store, but it'll be empty.
        try:
            store = shelve.open(
                self.config['VenueServer.persistenceData'])

            # If we've successfully opened the store, we load Venues
            # from it.
            for vURL in store.keys():
                print "Loading Venue: %s" % vURL
                self.venues[vURL] = store[vURL]
            store.close()
        except:
            print "Corrupt persistence database detected.", sys.exc_type, sys.exc_value

        # The houseKeeper is a task that is doing garbage collection and
        # other general housekeeping tasks for the Venue Server.
        # The first task we register with the houseKeeper is a periodic
        # checkpoint, this tries to ensure that the persistent store is
        # kept up to date.
        self.houseKeeper = scheduler.Scheduler()
        self.houseKeeper.AddTask(self.Checkpoint,
                            self.config['VenueServer.houseKeeperFrequency'], 0)

        # We register signal handlers for the VenueServer. In the event of
        # a signal we just try to shut down cleanly.
        signal.signal(signal.SIGINT, self.SignalHandler)
        # for some reason this signal doesn't work now
        # signal.signal(signal.SIGBREAK, self.SignalHandler)
        signal.signal(signal.SIGTERM, self.SignalHandler)

    def SignalHandler(self, signum, frame):
        """
        SignalHandler catches signals and shuts down the VenueServer (and
        all of it's Venues. Then it stops the hostingEnvironment.
        """
        print "Got signal: ", signum
        self.Shutdown(None, 0)

    def LoadConfig(self, file, config={}):
        """
        Returns a dictionary with keys of the form <section>.<option>
        and the corresponding values.
        This is from the python cookbook credit: Dirk Holtwick.
        """
        config = config.copy()
        self.cp = ConfigParser.ConfigParser()
        self.cp.read(file)
        for sec in self.cp.sections():
            name = string.lower(sec)
            for opt in self.cp.options(sec):
                config[name + "."
                       + string.lower(opt)] = string.strip(
                        self.cp.get(sec, opt))
        return config

    def AddVenue(self, connectionInfo, venueDescription):
        """
        The AddVenue method takes a venue description and creates a new
        Venue Object, complete with a coherence service, then makes it
        available from this Venue Server.
        """
        try:
            # instantiate a local venueDecription from the input,
            # since it probably came from a SOAP client and we don't
            # want to store it
            venueDescription = VenueDescription( venueDescription.name,
                                                 venueDescription.description,
                                                 venueDescription.icon,
                                                 venueDescription.extendedDescription )

            # Get the next port for the coherenceService for the new venue
#            coherencePort = self.config['CoherenceService.coherencePortBase'] + len(self.venues.keys())
            self.coherencePort = self.coherencePort + 1

            print "Next coherence port is: %d" % self.coherencePort
            # Build the new coherenceService
#            coherenceService = CoherenceService.CoherenceService(NetworkLocation.UnicastNetworkLocation(socket.getfqdn(), self.coherencePort))
            coherenceService = CoherenceService.CoherenceService( NetworkLocation.UnicastNetworkLocation(socket.getfqdn(), coherencePort))

            venueID = GUID.GUID()
            venuePath = "Venues/%s" % venueID
            venueURL = self.hostingEnvironment.get_url_base() + "/" + venuePath
            venueDescription.uri = venueURL

            # Create a new Venue object, pass it the coherenceService,
            #       the server's Multicast Address Allocator, and the server's
            #       Data Storage object
            venue = Venue.Venue(self, venueID, venueDescription,
                                connectionInfo.get_remote_name(),
                                coherenceService,
                                self.multicastAddressAllocator,
                                self.dataStorage)

            # Somehow we have to register this venue as a new service
            # on the server.  This gets tricky, since we're not assuming
            # the VenueServer knows about the SOAP server.
            if(self.hostingEnvironment != None):
                venueService = self.hostingEnvironment.create_service_object(pathId = venuePath)
                venue._bind_to_service(venueService)

            # If this is the first venue, set it as the default venue
            if(len(self.venues) == 0):
                self.SetDefaultVenue(connectionInfo, venueURL)

            # Add the venue to the list of venues
            self.venues[venueURL] = venue
        except:
            print "Exception in AddVenue ", sys.exc_type, sys.exc_value

        # return the URL to the new venue
        return venueURL

    AddVenue.pass_connection_info = 1
    AddVenue.soap_export_as = "AddVenue"

    def ModifyVenue(self, connectionInfo, URL, venueDescription):
        """
        ModifyVenue updates a Venue Description.
        """
        # This should check
        # 1. That you are allowed to do this
        # 2. That you are setting the right venue description
        if(venueDescription.uri == URL):
            self.venues[URL].description = venueDescription
                
    ModifyVenue.pass_connection_info = 1
    ModifyVenue.soap_export_as = "ModifyVenue"

    def RemoveVenue(self, connectionInfo, URL):
        """
        RemoveVenue removes a venue from the VenueServer.
        """
        venue = self.venues[URL]
        venue.Shutdown()
        del self.venues[URL]

    RemoveVenue.pass_connection_info = 1
    RemoveVenue.soap_export_as = "RemoveVenue"

    def AddAdministrator(self, connectionInfo, string):
        """
        AddAdminstrator adds an administrator to the list of administrators
        for this VenueServer.
        """
        self.administrators.append(string)

    AddAdministrator.pass_connection_info = 1
    AddAdministrator.soap_export_as = "AddAdministrator"

    def RemoveAdministrator(self, connectionInfo, string):
        """
        RemoveAdministrator removes an administrator from the list of
        administrators for this VenueServer.
        """
        self.administrators.remove(string)

    RemoveAdministrator.pass_connection_info = 1
    RemoveAdministrator.soap_export_as = "RemoveAdministrator"

    def GetAdministrators(self, connectionInfo):
        """
        GetAdministrators returns a list of adminsitrators for this 
        VenueServer.
        """
        return self.administrators

    GetAdministrators.pass_connection_info = 1
    GetAdministrators.soap_export_as = "GetAdministrators"

    def AddService(self, connectionInfo, serviceDescription):
        """
        AddService adds a service description to the list of service
        descriptions that are available to the Virtual Venues hosted by
        this VenueServer. 
        """
        self.services[serviceDescription.uri] = serviceDescription

    AddService.pass_connection_info = 1
    AddService.soap_export_as = "AddService"

    def RemoveService(self, connectionInfo, URL, serviceDescription):
        """
        RemoveService removes a service description from the list of 
        service descriptions that this VenueServer knows about.
        """
        self.services.remove(serviceDescription)

    RemoveService.pass_connection_info = 1
    RemoveService.soap_export_as = "RemoveService"

    def ModifyService(self, connectionInfo, URL, serviceDescription):
        """
        ModifyService updates a service description that is in the 
        list of services for this VenueServer.
        """
        if URL == serviceDescription.uri:
            self.services[URL] = serviceDescription

    ModifyService.pass_connection_info = 1
    ModifyService.soap_export_as = "ModifyService"

    def RegisterServer(self, connectionInfo, URL):
        """
        This method should register the server with the venues
        registry at the URL passed in. This is by default a
        registration page at Argonne for now.
        """
        # registryService = SOAP.SOAPProxy(URL)
        # registryService.Register(#data)

    RegisterServer.pass_connection_info = 1
    RegisterServer.soap_export_as = "RegisterServer"

    def GetVenues(self, connectionInfo):
        """
        GetVenues returns a list of Venues Descriptions for the venues hosted by
        this VenueServer.
        """
        try:
            venueDescriptionList = map( lambda venue: venue.GetDescription( connectionInfo ), self.venues.values() )

            for venue in venueDescriptionList:
                print "  ---- venue ", venue.name, venue.description, venue.uri
        except:
            print "Exception in GetVenues ", sys.exc_type, sys.exc_value
        return venueDescriptionList

    GetVenues.pass_connection_info = 1
    GetVenues.soap_export_as = "GetVenues"

    def GetDefaultVenue(self, connectionInfo):
        """
        GetDefaultVenue returns the URL to the default Venue on the
        VenueServer.
        """
        return self.defaultVenue

    GetDefaultVenue.pass_connection_info = 1
    GetDefaultVenue.soap_export_as = "GetDefaultVenue"

    def SetDefaultVenue(self, connectionInfo, venueURL):
        """
        SetDefaultVenue sets which Venue is the default venue for the
        VenueServer.
        """
        self.defaultVenue = venueURL
        self.config["VenueServer.defaultVenue"] = venueURL
        self.cp.set("VenueServer", "defaultVenue", str(venueURL))

    SetDefaultVenue.pass_connection_info = 1
    SetDefaultVenue.soap_export_as = "SetDefaultVenue"

    def SetCoherencePortBase(self, connectionInfo, portBase):
        """
        SetCoherencePortBase sets the base port for the coherence service.
        """
        self.portBase = coherencePortBase

    SetCoherencePortBase.pass_connection_info = 1
    SetCoherencePortBase.soap_export_as = "SetCoherencePortBase"

    def GetCoherencePortBase(self, connectionInfo):
        """
        GetCoherencePortBase returns the base port for the coherence service.
        """
        return self.coherencePortBase

    GetCoherencePortBase.pass_connection_info = 1
    GetCoherencePortBase.soap_export_as = "GetCoherencePortBase"


    def SetStorageLocation( self, path ):
        """
        Set the path for data storage
        """
        self.path = path
    SetStorageLocation.pass_connection_info = 1
    SetStorageLocation.soap_export_as = "SetStorageLocation"


    def SetAddressAllocationMethod( self, addressAllocationMethod ):
        """
        Set the method used for multicast address allocation:
            either RANDOM or INTERVAL (defined in MulticastAddressAllocator)
        """
        self.addressAllocationMethod = addressAllocationMethod
    SetAddressAllocationMethod.pass_connection_info = 1
    SetAddressAllocationMethod.soap_export_as = "SetAddressAllocationMethod"


    def SetBaseAddress( self, address ):
        """
        Set base address used when allocating multicast addresses in
        an interval
        """
        self.multicastAddressAllocator.SetBaseAddress( address )
    SetBaseAddress.pass_connection_info = 1
    SetBaseAddress.soap_export_as = "SetBaseAddress"


    def SetAddressMask( self, mask ):
        """
        Set address mask used when allocating multicast addresses in
        an interval
        """
        self.multicastAddressAllocator.SetAddressMask( mask )
    SetAddressMask.pass_connection_info = 1
    SetAddressMask.soap_export_as = "SetAddressMask"


    def Shutdown(self, connectionInfo, secondsFromNow):
        """
        Shutdown shuts down the server.
        """
        for vURL in self.venues.keys():
            self.venues[vURL].Shutdown()

        self.Checkpoint()

        self.hostingEnvironment.stop()

    Shutdown.pass_connection_info = 1
    Shutdown.soap_export_as = "Shutdown"

    def Checkpoint(self):
        """
        Checkpoint stores the current state of the running VenueServer to
        non-volatile storage. In the event of catastrophic failure, the
        non-volatile storage can be used to restart the VenueServer.
        
        The fequency at which Checkpointing is done will bound the amount of
        state that is lost (the longer the time between checkpoints, the more 
        that can be lost).
        """
        try:
            store = shelve.open(self.config['VenueServer.persistenceData'])

            for vURL in self.venues.keys():
                venue = self.venues[vURL]
                store[vURL] = venue

            store.close()
        except:
            print "Corrupt persistence database detected.", sys.exc_type, sys.exc_value

        self.cp.write(file(self.configFile, 'w+'))

    Checkpoint.soap_export_as = "Checkpoint"

if __name__ == "__main__":
    from AccessGrid.hosting.pyGlobus import Server, ServiceBase
    from AccessGrid.VenueServer import VenueServer
    import sys

    # Explicitly binding the service to a path

    hostingEnvironment = Server.Server(8000)
    venueServer = VenueServer(hostingEnvironment)
    serviceObject = hostingEnvironment.create_service_object(pathId = 'VenueServer')
    venueServer._bind_to_service(serviceObject)

    print "Service running at: %s" % venueServer.get_handle()
    hostingEnvironment.run()
    sys.exit(0)
