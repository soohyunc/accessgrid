#-----------------------------------------------------------------------------
# Name:        VenueServer.py
# Purpose:     This serves Venues.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: VenueServer.py,v 1.2 2002-12-17 22:45:46 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

# Standard stuff
import ConfigParser
import socket
import string
from threading import Thread
import shelve

# AG Stuff
from AccessGrid.hosting.pyGlobus import ServiceBase
import GUID
import CoherenceService
import NetworkLocation
import MulticastAddressAllocator
import DataStore
import Venue

class VenueServer(ServiceBase.ServiceBase):
    """
    
    """
    serverHost = ''
    serverURL = ''
    venueBaseURL = ''
    administrators = []
    
    configFile = ''
    config = {
        "VenueServer.serverPort" : 7500,
        "VenueServer.houseKeeperFrequency" : 900,
        "VenueServer.serverNS" : 'VenueServer',
        "VenueServer.venueNS" : 'Venues/',
        "VenueServer.persistenceData" : 'VenueData',
        "CoherenceService.coherencePortBase" : 9000,
        "DataStorage.store" : 'Data/',
        "DataStorage.port" : 8892
        }  
    serverInstance = None
    defaultVenue = None
    multicastAddressAllocator = None
    dataStorage = None
    houseKeeper = None
    venues = {}
    services = []
    
    def __init__(self, configFile=''):
        __doc__ = """ """
        # Get the local hostname of the server
        self.serverHost = string.lower(socket.getfqdn())
        
        # Figure out which configuration file to use for the
        # server configuration. If no configuration file was specified
        # look for a configuration file named VenueServer.cfg
        # VenueServer is the value of self.__class__
        classpath = string.split(str(self.__class__), '.')
        if configFile == '': 
            self.configFile = classpath[0]+'.cfg'
        else:
            self.configFile = configFile
        
        # Instantiate a new config parser
        self.LoadConfig(configFile, self.config)
        self.serverPort = self.config['VenueServer.serverPort']
        
        # Set default attributes of the server
        #   the server URL
        #   the base URL to the venues
        #   create a new MulticastAddressAllocator
        #   create a new DataStore
        baseURL = "http://%s:%s/" % (self.serverHost, self.serverPort)
        self.serverURL = baseURL + self.config['VenueServer.serverNS']
        self.venueBaseURL = baseURL + self.config['VenueServer.venueNS']
        self.multicastAddressAllocator = MulticastAddressAllocator.MulticastAddressAllocator()
        self.dataStorage = None
        self.store = shelve.open(self.config['VenueServer.persistenceData'], 'c')
        for k in self.store.keys():
            venue = self.store[k]
            self.venues[venue.description.uri] = venue
        houseKeeper = VenueHouseKeeper(self)
        houseKeeper.start()
          
    def LoadConfig(self, file, config={}):
        __doc__ = """
        Returns a dictionary with keys of the form <section>.<option> and 
        the corresponding values.
        This is from the python cookbook credit: Dirk Holtwick.
        """
        config = config.copy()
        cp = ConfigParser.ConfigParser()
        cp.read(file)
        for sec in cp.sections():
            name = string.lower(sec)
            for opt in cp.options(sec):
                config[name + "." + string.lower(opt)] = string.strip(
                    cp.get(sec, opt))
        return config
    
    def AddVenue(self, connectionInfo, venueDescription):
        __doc__ = """ """
        
        print "Add Venue Called."
        
        # Get the next port for the coherenceService for the new venue
        self.coherencePortBase = self.coherencePortBase + 1
        
        # Build the new coherenceService
#        coherenceService = CoherenceService.CoherenceService(NetworkLocation.UnicastNetworkLocation(self.serverHost, self.coherencePortBase))
                    
        # Set the new Venue's URL
        venueID = GUID.GUID()
        venueURI = "%s%s" % (self.venueBaseURL, venueID)
        venueDescription.uri = venueURI
        
        # Create a new Venue object, pass it the coherenceService, 
        #   the server's Multicast Address Allocator, and the server's
        #   Data Storage object
        venue = Venue.Venue(self, venueID, venueDescription, coherenceService,
                      self.multicastAddressAllocator, self.dataStorage)
            
        # If this is the first venue, set it as the default venue
        if(len(self.venues) == 0):
            self.SetDefaultVenue(venueURI)
                
        # Add the venue to the list of venues
        self.venues[venueURI] = venue
                            
        # Somehow we have to register this venue as a new service on the 
        #  server.  This gets tricky, since we're not assuming the VenueServer
        #  knows about the SOAP server.
        print "Setting the new venue to handle calls"
#        if(self.serverInstance != None):
#            print "Registering the new Venue in NS: " + self.venueBaseURL+str(venueID)
#            self.serverInstance.registerObject(venue, 
#                                               self.venueBaseURL+str(venueID))
        
        # return the URL to the new venue
        # return venue.GetDescription().GetGetURL()
        return venueURI
    
    AddVenue.pass_connection_info = 1
    AddVenue.soap_export_as = "AddVenue"
    
    def ModifyVenue(self, connectionInfo, URL, venueDescription):
        __doc__ = """ """
        # This should check
        # 1. That you are allowed to do this
        # 2. That you are setting the right venue description
        if(venueDescription.uri == URL):
            self.venues[URL] = venueDescription
                
    ModifyVenue.pass_connection_info = 1
    ModifyVenue.soap_export_as = "ModifyVenue"
    
    def RemoveVenue(self, connectionInfo, URL):
        __doc__ = """ """
        venue = self.venues[URL]
        del self.venues[URL]
        
    RemoveVenue.pass_connection_info = 1
    RemoveVenue.soap_export_as = "RemoveVenue"
    
    def AddAdministrator(self, connectionInfo, string):
        __doc__ = """ """
        self.administrators.append(string)
        
    AddAdministrator.pass_connection_info = 1
    AddAdministrator.soap_export_as = "AddAdministrator"
    
    def RemoveAdminstrator(self, connectionInfo, string):
        __doc__ = """ """
        self.administrators.remove(string)
        
    RemoveAdminstrator.pass_connection_info = 1
    RemoveAdminstrator.soap_export_as = "RemoveAdminstrator"
    
    def AddService(self, connectionInfo, serviceDescription):
        __doc__ = """ """
        self.services[serviceDescription.uri] = serviceDescription
        
    AddService.pass_connection_info = 1
    AddService.soap_export_as = "AddService"
    
    def RemoveService(self, connectionInfo, URL, serviceDescription):
        __doc__ = """ """
        self.services.remove(serviceDescription)
        
    RemoveService.pass_connection_info = 1
    RemoveService.soap_export_as = "RemoveService"
    
    def ModifyService(self, connectionInfo, URL, serviceDescription):
        __doc__ = """ """
        if URL == serviceDescription.uri:
            self.services[URL] = serviceDescription
        
    ModifyService.pass_connection_info = 1
    ModifyService.soap_export_as = "ModifyService"
    
    def RegisterServer(self, connectionInfo, URL):
        __doc__ = """ 
        This method should register the server with the venues registry at the
        URL passed in. This is by default a registration page at Argonne for 
        now.
        """
        # registryService = SOAP.SOAPProxy(URL)
        # registryService.register(#data)
        
    RegisterServer.pass_connection_info = 1
    RegisterServer.soap_export_as = "RegisterServer"
    
    def GetVenues(self, connectionInfo):
        __doc__ = """ """
        return self.venues.keys()
    
    GetVenues.pass_connection_info = 1
    GetVenues.soap_export_as = "GetVenues"
    
    def GetDefaultVenue(self, connectionInfo):
        __doc__ = """ """
        return self.defaultVenue
    
    GetDefaultVenue.pass_connection_info = 1
    GetDefaultVenue.soap_export_as = "GetDefaultVenue"
    
    def SetDefaultVenue(self, connectionInfo, venueURI):
        __doc__ = """ """
        self.defaultVenue = venueURI
        self.config.set('VenueServer', 'defaultVenue', venueURI)
        
    SetDefaultVenue.pass_connection_info = 1
    SetDefaultVenue.soap_export_as = "SetDefaultVenue"
    
    def SetCoherencePortBase(self, connectionInfo, portBase):
        __doc__ = """ """
        self.portBase = coherencePortBase
        
    SetCoherencePortBase.pass_connection_info = 1
    SetCoherencePortBase.soap_export_as = "SetCoherencePortBase"
    
    def GetCoherencePortBase(self, connectionInfo):
        __doc__ = """ """
        return self.coherencePortBase
    
    GetCoherencePortBase.pass_connection_info = 1
    GetCoherencePortBase.soap_export_as = "GetCoherencePortBase"
    
    def Shutdown(self, connectionInfo, secondsFromNow):
        __doc__ = """ """
        self.config.write(self.configFile)
        self.store.close()
        
    Shutdown.pass_connection_info = 1
    Shutdown.soap_export_as = "Shutdown"
    
    def Checkpoint(self):
        __doc__ = """ """
        for venueURI in self.venues.keys():
            self.store[venueURI] = self.venues[venueURI]
        return 0
            
    def SetServerInstance(self, instance):
        __doc__ = """ """
        self.serverInstance = instance
        self.serverInstance.registerObject(self)
        
    def GetServerInstance(self):
        __doc__ = """ """
        return self.serverInstance
    
class VenueHouseKeeper(Thread):
    __doc__ = """ """
    # actions is a dictionary that has two keys and a function as a value
    # the first key is the next time to call the function (value)
    # the second key is the frequency between calls, so you can reset the time
    periodic = 10
    actions = {}
    venueServer = None
    
    def __init__(self, venueServer):
        Thread.__init__(self)
        self.venueServer = venueServer
    
    def SetAction(self, frequency, function, startNow=1):
        __doc__ = """ """
        
    def FindNextTime(self):
        __doc__ = """ """
        
    def run(self):
        import time
        if(self.venueServer != None):
            self.venueServer.Checkpoint()
        time.sleep(self.periodic)