#-----------------------------------------------------------------------------
# Name:        Venue.py
# Purpose:     The Virtual Venue is the object that provides the collaboration
#               scopes in the Access Grid.
#
# Author:      Ivan R. Judson, Thomas D. Uram
#
# Created:     2002/12/12
# RCS-ID:      $Id: Venue.py,v 1.80 2003-04-28 00:44:58 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys
import time
import string
import types
import socket
import os.path
import logging
import urlparse
import ConfigParser

from AccessGrid.hosting.pyGlobus import ServiceBase
from AccessGrid.GUID import GUID

from AccessGrid.hosting import AccessControl

from AccessGrid import AppService
from AccessGrid.Types import Capability
from AccessGrid.Descriptions import StreamDescription, CreateStreamDescription
from AccessGrid.Descriptions import ConnectionDescription, VenueDescription
from AccessGrid.Descriptions import ApplicationDescription, ServiceDescription
from AccessGrid.Descriptions import CreateDataDescription, DataDescription
from AccessGrid.NetworkLocation import MulticastNetworkLocation
from AccessGrid.GUID import GUID
from AccessGrid import DataStore
from AccessGrid.scheduler import Scheduler
from AccessGrid.Events import Event, HeartbeatEvent, DisconnectEvent
from AccessGrid.Utilities import formatExceptionInfo, AllocateEncryptionKey
from AccessGrid.Utilities import GetHostname

# these imports are for dealing with SOAP structs, which we won't have to 
# do when we have WSDL; at that time, these imports and the corresponding calls
# should be removed
from AccessGrid.ClientProfile import CreateClientProfile
from AccessGrid.Descriptions import CreateServiceDescription
from AccessGrid.Descriptions import CreateDataDescription

log = logging.getLogger("AG.VenueServer")

class VenueException(Exception):
    """
    A generic exception type to be raised by the Venue code.
    """
    pass

class NotAuthorized(Exception):
    pass

class Venue(ServiceBase.ServiceBase):
    """
    A Virtual Venue is a virtual space for collaboration on the Access Grid.
    """
    def __init__(self, server, name, description, administrators,
                 dataStoreLocation, id=None):
        """
        Venue constructor.

        dataStorePath is the directory which the Venue's data storage object
        should use for storing its files.

        """
        log.debug("------------ STARTING VENUE")
        self.server = server
        self.name = name
        self.description = description
        self.administrators = administrators
        self.encryptMedia = server.GetEncryptAllMedia()
        self.encryptionKey = None

        if id == None:
            self.uniqueId = str(GUID())
        else:
            self.uniqueId = id
            
        self.uri = self.server.MakeVenueURL(self.uniqueId)
        log.info("URI %s", self.uri)

        self.server.eventService.AddChannel(self.uniqueId)
        self.server.textService.AddChannel(self.uniqueId)
        log.debug("Registering heartbeat for %s", self.uniqueId)
        self.server.eventService.RegisterCallback(self.uniqueId,
                                           HeartbeatEvent.HEARTBEAT,
                                           self.ClientHeartbeat)

        #
        # Create the directory to hold the venue's data.
        #

        log.debug("data store location: %s" % dataStoreLocation)
        
        if dataStoreLocation is None or not os.path.exists(dataStoreLocation):
            log.warn("Creating venue: Data storage path %s not valid",
                     dataStoreLocation)
            self.dataStorePath = None
        else:
            self.dataStorePath = os.path.join(dataStoreLocation, self.uniqueId)
            if not os.path.exists(self.dataStorePath):
                try:
                    os.mkdir(self.dataStorePath)
                except OSError, e:
                    log.exception("Could not create venueStoragePath.")
                    self.dataStorePath = None
                
        if self.encryptMedia == 1:
            self.encryptionKey = AllocateEncryptionKey()

        self.cleanupTime = 30

        self.connections = dict()
        self.applications = dict()
        self.data = dict()
        self.services = dict()
        self.streamList = StreamDescriptionList()
        self.clients = dict()

        self.dataStore = None
        self.producerCapabilities = []
        self.consumerCapabilities = []

        self.houseKeeper = Scheduler()
        self.houseKeeper.AddTask(self.CleanupClients, 10)
        self.houseKeeper.StartAllTasks()

        self.startDataStore()

        self.server.eventService.AddChannel(self.uniqueId)
        self.server.textService.AddChannel(self.uniqueId)
        log.debug("Registering heartbeat for %s", self.uniqueId)
        self.server.eventService.RegisterCallback(self.uniqueId,
                                           HeartbeatEvent.HEARTBEAT,
                                           self.ClientHeartbeat)
        # This might make things better
        self.server.eventService.RegisterCallback(self.uniqueId,
                                                  DisconnectEvent.DISCONNECT,
                                                  self.EventServiceDisconnect)

        #self.StartApplications()

        #self.AllowedEntryRole = AccessControl.Role("Venue.AllowedEntry", self)
        #self.VenueUsersRole = AccessControl.Role("Venue.VenueUsers", self)

    def AsINIBlock(self):
        # The Venue Block
        sclass = str(self.__class__).split('.')
        string = "[%s]\n" % self.uniqueId
        string += "type : %s\n" % sclass[-1]
        string += "name : %s\n" % self.name
        string += "description : %s\n" % self.description
        string += "administrators : %s\n" % ":".join(self.administrators)
        string += "encryptMedia : %d\n" % self.encryptMedia
        if self.encryptMedia:
            string += "encryptionKey : %s\n" % self.encryptionKey
        clist = ":".join(map( lambda conn: conn.GetId(),
                              self.connections.values() ))
        string += "connections : %s\n" % clist

        # For now we have to sort out the data so we only
        # store venue data in the persistence file
        vdata = []
        for d in self.data.values():
            if d.GetType() == None:
                vdata.append(d)
        dlist = ":".join(map( lambda data: data.GetId(), vdata ))
        
        string += "data : %s\n" % dlist
        slist = ":".join(map( lambda stream: stream.GetId(),
                              self.streamList.GetStaticStreams() ))
        string += "streams : %s\n" % slist
        string += "cleanupTime : %d\n\n" % self.cleanupTime

        # The blocks for other data
        string += "\n".join(map(lambda conn: conn.AsINIBlock(),
                                self.connections.values() ))
        string += "\n".join(map(lambda data: data.AsINIBlock(), vdata ))
        string += "\n".join(map(lambda stream: stream.AsINIBlock(),
                       self.streamList.GetStaticStreams()))

        return string

    def AsVenueDescription(self):
        """
        """
        desc = VenueDescription(self.name, self.description,
                                self.administrators, 
                                (self.encryptMedia, self.encryptionKey),
                                self.connections.values(),
                                self.GetStaticStreams())
        desc.SetURI(self.uri)
        
        return desc
    
    def _authorize(self):
        """
        """
        sm = AccessControl.GetSecurityManager()
        if sm == None:
            return 1
        elif sm.GetSubject().GetName() in self.administrators:
            return 1
        # call back up to the server
        elif self.server._authorize():
            return 1
        else:
            return 0

    def __repr__(self):
        return "Venue: name=%s id=%s" % (self.name, id(self))

    def startDataStore(self):
        """
        Start the local datastore server.

        We create a DataStore to manage this Venue's data.
        We have been already given a data transfer service instance
        (in the call to Venue.Start()).
        
        The DataStore is given the Venue's dataStorePath as
        its working directory.  We then loop through the data
        descriptions in the venue, both checking to see that the file
        still exists for each piece of data, and updating the uri
        field in the description with the new download URL.

        Actually, we get to do both steps at once, as
        GetDownloadDescriptor will return None if the file doesn't
        exist in the local data store.
        """
        
        if self.dataStorePath is None or not os.path.isdir(self.dataStorePath):
            log.warn("Not starting datastore for venue: %s does not exist %s",
                      self.uniqueId, self.dataStorePath)
            return

        self.server.dataTransferServer.RegisterPrefix(str(self.uniqueId), self)

        self.dataStore = DataStore.DataStore(self, self.dataStorePath,
                                             str(self.uniqueId))
        self.dataStore.SetTransferEngine(self.server.dataTransferServer)

        log.info("Have upload url: %s", self.dataStore.GetUploadDescriptor())
        
        for file, desc in self.data.items():
            log.debug("Checking file %s for validity", file)
            url = self.dataStore.GetDownloadDescriptor(file)
            if url is None:
                log.warn("File %s has vanished", file)
                del self.data[file]
            else:
                desc.SetURI(url)
                self.UpdateData(desc)

    def SetDataStore(self, dataStore):
        """
        Set the Data Store for the Venue. This is usually set to the data
        store the venue server uses.
        """
        self.dataStore = dataStore

    def GetState(self):
        """
        GetState returns the current state of the Virtual Venue.
        """

        log.debug("Called GetState on %s", self.uniqueId)
        
        venueState = {
            'uniqueId' : self.uniqueId,
            'name' : self.name,
            'description' : self.description,
            'uri' : self.uri,
            'connections' : self.connections.values(),
            'applications': map(lambda x: x.GetState(),
                                self.applications.values()),
            'clients' : self.__GetClients().values(),
            'services' : self.services.values(),
            'eventLocation' : self.server.eventService.GetLocation(),
            'textLocation' : self.server.textService.GetLocation()
            }

        #
        # If we don't have a datastore, don't advertise
        # the existence of any data. We won't be able to get
        # at it anyway.
        #
        if self.dataStore is None:
            venueState['data'] = []
        else:
            venueState['data'] = self.data.values()

        return venueState

    def __GetClients(self):
        '''
        Creates a dictionary of clients by extracting clients from the
        clients-time dictionary
        '''
        clientsDict = {}
        for key in self.clients.keys():
            (client, heartbeatTime) = self.clients[key]
            clientsDict[key] = client
            
        log.debug("Clients contained in the venue are: %s" %str(clientsDict.values()))
        return clientsDict

    def CleanupClients(self):
        now_sec = time.time()
        for privateId in self.clients.keys():
            (client, then_sec) = self.clients[privateId]
            if abs(now_sec - then_sec) > self.cleanupTime:
                log.debug("Removing user %s with expired heartbeat time", client.name)
                self.RemoveUser(privateId)

    def ClientHeartbeat(self, event):
        privateId = event
        now = time.time()
        log.debug("Got Client Heartbeat for %s at %s." % (event, now))
       
        if(self.clients.has_key(privateId)):
            (profile, heartbeatTime) = self.clients[privateId]
            self.clients[privateId] = (profile, now)
        else:
            log.error("Venue::ClientHeartbeat: Trying to set heartbeat time on non existing client")
    
    def EventServiceDisconnect(self, privateId):
        log.debug("VenueServer: Got Client disconnect for %s", privateId)
        self.RemoveUser(privateId)

    def Shutdown(self):
        """
        This method cleanly shuts down all active threads associated with the
        Virtual Venue. Currently there are a few threads in the Event
        Service.
        """
        self.houseKeeper.StopAllTasks()

    def NegotiateCapabilities(self, clientProfile, privateId):
        """
        This method takes a client profile and matching privateId, then it
        finds a set of streams that matches the client profile. Later this
        method could use network services to find The Best Match of all the
        network services, the existing streams, and all the client
        capabilities.
        """
        streamDescriptions = []

        #
        # Compare user's producer capabilities with existing stream
        # description capabilities. New producer capabilities are added
        # to the stream descriptions, and an event is emitted to alert
        # current participants about the new stream
        #

        for clientCapability in clientProfile.capabilities:
            if clientCapability.role == Capability.PRODUCER:
                matchesExistingStream = 0

                # add user as producer of all existing streams that match
                for stream in self.streamList.GetStreams():
                    if stream.capability.matches( clientCapability ):
                        streamDesc = stream
                        self.streamList.AddStreamProducer( privateId,
                                                           streamDesc )
                        streamDescriptions.append( streamDesc )
                        matchesExistingStream = 1
                        log.debug("added user as producer of existent stream")

                # add user as producer of new stream
                if not matchesExistingStream:
                    capability = Capability( clientCapability.role,
                                             clientCapability.type )
                    capability.parms = clientCapability.parms

                    addr = self.AllocateMulticastLocation()
                    streamDesc = StreamDescription( self.name,
                                                    addr,
                                                    capability, 
                                                    self.encryptMedia, 
                                                    self.encryptionKey,
                                                    0)
                    log.debug("added user as producer of non-existent stream")
                    self.streamList.AddStreamProducer( privateId,
                                                       streamDesc )


        #
        # Compare user's consumer capabilities with existing stream
        # description capabilities. The user will receive a list of
        # compatible stream descriptions
        #
        clientConsumerCapTypes = []
        for capability in clientProfile.capabilities:
            if capability.role == Capability.CONSUMER:
                clientConsumerCapTypes.append( capability.type )
        for stream in self.streamList.GetStreams():
            if stream.capability.type in clientConsumerCapTypes:
                streamDescriptions.append( stream )

        return streamDescriptions

    def AllocateMulticastLocation(self):
        """
        This method creates a new Multicast Network Location.
        """
        defaultTtl = 127
        return MulticastNetworkLocation(
            self.server.multicastAddressAllocator.AllocateAddress(),
            self.server.multicastAddressAllocator.AllocatePort(),
            defaultTtl )

    def GetNextPrivateId( self ):
        """This method creates the next Private Id."""
        return str(GUID())

    # Should use self.clients.has_key(privateId), and get rid of this method

    #def IsValidPrivateId( self, privateId ):
    #    """This method verifies the private Id is valid."""
    #    if privateId in self.clients.keys():
    #        return 1
    #    return 0

    def FindUserByProfile(self, profile):
        """
        Find out if a given client is in the venue from their client profile.
        If they are, return their private id, if not, return None.
        """
        for key in self.clients.keys():
            (client, heartbeatTime) = self.clients[key]
            if client.publicId == profile.publicId:
                return key

        return None

    # Interface methods
    def wsAddData(self, dataDescriptionStruct ):
        log.debug("wsAddData")
        if not self._authorize():
            raise NotAuthorized
        else:
            dataDescription = CreateDataDescription(dataDescriptionStruct)
            return self.AddData(dataDescription)

    wsAddData.soap_export_as = "AddData"

    # Interface methods
    def wsRemoveData(self, dataDescriptionStruct ):
        log.debug("wsRemoveData")
        if not self._authorize():
            raise NotAuthorized
        else:
            dataDescription = CreateDataDescription(dataDescriptionStruct)
            return self.RemoveData(dataDescription)

    wsRemoveData.soap_export_as = "RemoveData"

    def wsUpdateData(self, dataDescriptionStruct):
        if not self._authorize():
            raise NotAuthorized
        else:
            dataDescription = CreateDataDescription(dataDescriptionStruct)
            return self.UpdateData(dataDescription)

    wsUpdateData.soap_export_as = "UpdateData"

    def wsGetData(self, name):
        if not self._authorize():
            raise NotAuthorized
        else:        
            return self.GetData(name)

    wsGetData.soap_export_as = "GetData"

    def wsAddService(self, serviceDescriptionStruct ):
        if not self._authorize():
            raise NotAuthorized
        else:
            print "-- creating service description from struct"
            serviceDescription = CreateServiceDescription(serviceDescriptionStruct)
            print "-- done with that"
            return self.AddService(serviceDescription)
        
    wsAddService.soap_export_as = "AddService"

    # Management methods
    def AddAdministrator(self, string):
        """
        """
        if not self._authorize():
            raise NotAuthorized
        if string not in self.administrators:
            self.administrators.append(string)
            return string
        else:
            log.exception("Venue.AddAdministrator: Administrator already present")
            raise VenueException("Administrator already present")

    AddAdministrator.soap_export_as = "AddAdministrator"

    def RemoveAdministrator(self, string):
        """
        """
        if not self._authorize():
            raise NotAuthorized
        if string in self.administrators:
            self.administrators.remove(string)
            return string
        else:
            log.exception("Venue.RemoveAdministrator: Administrator not found")
            raise VenueException("Administrator not found")

    RemoveAdministrator.soap_export_as = "RemoveAdministrator"

    def SetAdministrators(self, administratorList):
        """
        """
        if not self._authorize():
            raise NotAuthorized
        self.administrators = self.administrators + administratorList

    SetAdministrators.soap_export_as = "SetAdministrators"

    def GetAdministrators(self):
        """
        """
        return self.administrators

    GetAdministrators.soap_export_as = "GetAdministrators"

    def SetEncryptMedia(self, value, key=None):
        """
        Turn media encryption on or off.
        """
        if not self._authorize():
            raise NotAuthorized
        self.encryptMedia = value
        if not self.encryptMedia:
            self.encryptionKey = None
        else:
            if key == None:
                key = AllocateEncryptionKey()
            self.encryptionKey = key

        return self.encryptMedia

    SetEncryptMedia.soap_export_as = "SetEncryptMedia"

    def GetEncryptMedia(self):
        """
        Return whether we are encrypting streams or not.
        """
        return self.encryptionKey

    GetEncryptMedia.soap_export_as = "GetEncryptMedia"

#     def AddNetworkService(self, networkServiceDescription):
#         """
#         AddNetworkService allows an administrator to add functionality to
#         the Venue. Network services are described in the design documents.
#         """
#         if not self._authorize():
#             raise NotAuthorized
#         try:
#             self.networkServices[ networkServiceDescription.uri ] = networkServiceDescription
#         except:
#             log.exception("Exception in Add Network Service!")
#             raise VenueException("Add Network Service Failed!")
        
#     AddNetworkService.soap_export_as = "AddNetworkService"

#     def GetNetworkServices(self):
#         """
#         GetNetworkServices retreives the list of network service descriptions
#         from the venue.
#         """
#         return self.networkServices

#     GetNetworkServices.soap_export_as = "GetNetworkServices"

#     def RemoveNetworkService(self, networkServiceDescription):
#         """
#         RemoveNetworkService removes a network service from a venue, making
#         it unavailable to users of the venue.
#         """
#         if not self._authorize():
#             raise NotAuthorized
#         try:
#             del self.networkServices[ networkServiceDescription.uri ]
#         except:
#             log.exception("Exception in RemoveNetworkService!")
#             raise VenueException("Remove Network Service Failed!")

#     RemoveNetworkService.soap_export_as = "RemoveNetworkService"

    def AddConnection(self, connectionDescription):
        """
        AddConnection allows an administrator to add a connection to a
        virtual venue to this virtual venue.
        """
        if not self._authorize():
            raise NotAuthorized
        try:
            c = ConnectionDescription(connectionDescription.name,
                                      connectionDescription.description,
                                      connectionDescription.uri)
            self.connections[connectionDescription.uri] = c
            self.server.eventService.Distribute( self.uniqueId,
                                          Event( Event.ADD_CONNECTION,
                                                 self.uniqueId, c ) )
        except:
            log.exception("Exception in AddConnection!")
            raise VenueException("Add Connection Failed!")
        
    AddConnection.soap_export_as = "AddConnection"

    def RemoveConnection(self, connectionDescription):
        """
        RemoveConnection removes a connection to another virtual venue
        from this virtual venue. This is an administrative operation.
        """
        if not self._authorize():
            raise NotAuthorized
        try:
            del self.connections[ connectionDescription.uri ]
            self.eventService.Distribute( self.uniqueId,
                                          Event( Event.REMOVE_CONNECTION,
                                                 self.uniqueId,
                                                 connectionDescription ) )
        except:
            log.exception("Exception in RemoveConnection.")
            raise VenueException("Remove Connection Failed!")

    RemoveConnection.soap_export_as = "RemoveConnection"

    def GetConnections(self):
        """
        GetConnections returns a list of all the connections to other venues
        that are found within this venue.
        """
        log.debug("Calling GetConnections.")
        
        return self.connections.values()

    GetConnections.soap_export_as = "GetConnections"

    def wsSetConnections(self, connectionList):
        if not self._authorize():
            raise NotAuthorized
        else:
            cdict = {}
            try:
                # Add them all
                for connection in connectionList:
                    c = ConnectionDescription(connection.name,
                                              connection.description,
                                              connection.uri)
                    cdict[connection.uri] = c
                    self.SetConnections(cdict)
            except:
                log.exception("SetConnections failed.")
                raise VenueException("Set Connections Failed!")

    wsSetConnections.soap_export_as = "SetConnections"
        
    def SetConnections(self, connectionDict):
        """
        SetConnections is a convenient aggregate accessor for the list of
        connections for this venue. Alternatively the user could iterate over
        a list of connections adding them one by one, but this is more
        desirable.
        """
        log.debug("Calling SetConnections.")
        
        self.connections = connectionDict
            
        # Send the event
        self.server.eventService.Distribute( self.uniqueId,
                                             Event( Event.SET_CONNECTIONS,
                                                    self.uniqueId,
                                                    connectionDict.values() ) )

    def SetDescription(self, description):
        """
        SetDescription allows an administrator to set the venues description
        to something new.
        """
        if not self._authorize():
            raise NotAuthorized

        self.description = description

    SetDescription.soap_export_as = "SetDescription"

    def GetDescription(self):
        """
        GetDescription returns the description for the virtual venue.
        """
        return self.description
    
    GetDescription.soap_export_as = "GetDescription"

    def AddStream(self, inStreamDescription ):
        """
        Add a stream to the list of streams "in" the venue
        """
        if not self._authorize():
            raise NotAuthorized
        log.debug("%s - Adding Stream: ", self.uniqueId)
        
        streamDescription = CreateStreamDescription( inStreamDescription )
#         log.debug("%s - Location: %s %d", self.uniqueId,
#                   streamDescription.location.GetHost(),
#                   streamDescription.location.GetPort())
#         log.debug("%s - Capability: %s %s", self.uniqueId,
#                   streamDescription.capability.role,
#                   streamDescription.capability.type)
#         log.debug("%s - Encyrption Key: %s", self.uniqueId,
#                   streamDescription.encryptionKey)
#         log.debug("%s - Static: %d", self.uniqueId, streamDescription.static)
        
        self.streamList.AddStream( streamDescription )

    AddStream.soap_export_as = "AddStream"

    def RemoveStream(self, streamDescription):
        """
        Remove the given stream from the venue
        """
        if not self._authorize():
            raise NotAuthorized
        
        self.streamList.RemoveStream( streamDescription )

    RemoveStream.soap_export_as = "RemoveStream"

    def GetStreams(self):
        """
        GetStreams returns a list of stream descriptions to the caller.
        """
        return self.streamList.GetStreams()

    GetStreams.soap_export_as = "GetStreams"

    def GetStaticStreams(self):
        """
        GetStaticStreams returns a list of static stream descriptions
        to the caller.
        """
        return self.streamList.GetStaticStreams()

    GetStaticStreams.soap_export_as = "GetStaticStreams"

    # Client Methods
    def Enter(self, clientProfileStruct):
        """
        The Enter method is used by a VenueClient to gain access to the
        services, clients, and content found within a Virtual Venue.
        """
        privateId = None
        streamDescriptions = []
        state = self.GetState()

        #
        # Convert the ClientProfile struct to a ClientProfile obj
        #
        clientProfile = CreateClientProfile( clientProfileStruct )


        #
        # Authorization management.
        #
        # Get the security manager for this invocation. This will tell
        # us how the user was authenticated for this call.
        #
        # To check to see whether this user can even enter, see if
        # he is in the AllowedEntry role
        #

#          sm = AccessControl.GetSecurityManager()
#          if  sm.ValidateRole(self.AllowedEntryRole):
#              subject = sm.GetSubject()
#              log.info("User %s validated for entry to %s", subject, self)

#              if self.VenueUsersRole.HasSubject(subject):
#                  self.VenueUsersRole.AddSubject(subject)
#          else:
#              log.info("User %s rejected for entry to %s", sm.GetSubject(), self)
#              raise VenueException("Entry denied")


        #try:
        log.debug("Called Venue Enter for: ")
        log.debug(dir(clientProfile))
        
        privateId = self.FindUserByProfile(clientProfile)
        
        if privateId != None:
            log.debug("Client already in venue")
        else:
            privateId = self.GetNextPrivateId()
            log.debug("Assigning private id: %s", privateId)
            clientProfile.distinguishedName = AccessControl.GetSecurityManager().GetSubject().GetName()
            self.clients[privateId] = (clientProfile, time.time())
            state['clients'] = self.__GetClients().values()
                       
        # negotiate to get stream descriptions to return
        streamDescriptions = self.NegotiateCapabilities(clientProfile,
                                                            privateId)
        log.debug("Distribute enter event ")
        self.server.eventService.Distribute( self.uniqueId,
                                             Event( Event.ENTER,
                                                    self.uniqueId,
                                                    clientProfile ) )
        #except:
        #    log.exception("Exception in Enter!")
        #    raise VenueException("Enter: ")

        return ( state, privateId, streamDescriptions )

    Enter.soap_export_as = "Enter"

    def Exit(self, privateId ):
        """
        The Exit method is used by a VenueClient to cleanly leave a Virtual
        Venue. Cleanly leaving a Virtual Venue allows the Venue to cleanup
        any state associated (or caused by) the VenueClients presence.
        """
        try:
            log.debug("Called Venue Exit on %s", privateId)
            
            if self.clients.has_key( privateId ):
                self.RemoveUser(privateId)
                
            else:
                log.warn("* * Invalid private id %s!!", privateId)
        except:
            log.exception("Exception in Exit!")
            raise VenueException("ExitVenue: ")

    Exit.soap_export_as = "Exit"

    def RemoveUser(self, privateId):
        # Remove user as stream producer
        log.debug("Called RemoveUser on %s", privateId)
        self.streamList.RemoveProducer(privateId)

        # Distribute event
        clientProfile, heartbeatTime = self.clients[privateId]
        log.debug("Distribute EXIT event")
        self.server.eventService.Distribute( self.uniqueId,
                                             Event( Event.EXIT,
                                                    self.uniqueId,
                                                    clientProfile ) )
        # Remove clients private data
        for description in self.data.values():
            client, heartbeatTime = self.clients[privateId]

            if description.type == client.publicId:
                log.debug("Remove private data %s" %description.name)
                del self.data[description.name]
                   
        # Remove clients from venue
        if self.clients.has_key(privateId):
            del self.clients[privateId]
        else:
            log.warn("Tried to remove a client that doesn't exist in the venue")
       
    def UpdateClientProfile(self, clientProfileStruct ):
        """
        UpdateClientProfile allows a VenueClient to update/modify the client
        profile that is stored by the Virtual Venue that they gave to the Venue
        when they called the Enter method.
        """

        #
        # Convert the ClientProfile struct to a ClientProfile obj
        #
        clientProfile = CreateClientProfile( clientProfileStruct )

        log.debug("Called UpdateClientProfile on %s " %clientProfile.name)
        for key in self.clients.keys():
            client, heartbeatTime = self.clients[key]
            if client.publicId == clientProfile.publicId:
                self.clients[key] = (clientProfile, time.time())

        log.debug("Distribute MODIFY_USER event")
        self.server.eventService.Distribute( self.uniqueId,
                                             Event( Event.MODIFY_USER,
                                                    self.uniqueId,
                                                    clientProfile ) )
        
    UpdateClientProfile.soap_export_as = "UpdateClientProfile"

    def AddData(self, dataDescription ):
        """
        The AddData method enables VenuesClients to put data in the Virtual
        Venue. Data put in the Virtual Venue through AddData is persistently
        stored.
        """
        name = dataDescription.name
              
        log.debug("AddData with name %s " %name)
             
        if self.data.has_key(name):
            #
            # We already have this data; raise an exception.
            #
            log.exception("AddData: data already present: %s", name)
            raise VenueException("AddData: data %s already present" % (name))

        self.data[name] = dataDescription
        
        log.debug("Distribute ADD_DATA event %s", dataDescription)
        self.server.eventService.Distribute( self.uniqueId,
                                      Event( Event.ADD_DATA,
                                             self.uniqueId,
                                             dataDescription ) )

    def AddService(self, serviceDescription):
        """
        The AddService method enables VenuesClients to put services in
        the Virtual Venue. Service put in the Virtual Venue through
        AddService is persistently stored.
        """

        name = serviceDescription.name
     

        if self.services.has_key(name):
            #
            # We already have this service; raise an exception.
            #
            log.exception("AddService: service already present: %s", name)
            raise VenueException("AddService: service %s already present" % (name))

        self.services[serviceDescription.name] = serviceDescription
        log.debug("Distribute ADD_SERVICE event %s", serviceDescription)
        self.server.eventService.Distribute( self.uniqueId,
                                             Event( Event.ADD_SERVICE,
                                                    self.uniqueId,
                                                    serviceDescription ) )

    def RemoveService(self, serviceDescription):
        """
        RemoveService removes persistent service from the Virtual Venue.
        """
        try:
            if serviceDescription.name in self.services:
                del self.services[serviceDescription.name ]
                self.server.eventService.Distribute( self.uniqueId,
                                                     Event( Event.REMOVE_SERVICE,
                                                            self.uniqueId,
                                                            serviceDescription ) )
            else:
                log.exception("Service not found!")
                raise VenueException("Service not found.")
        except:
            log.exception("Exception in RemoveService!")
            raise VenueException("Cannot remove service!")

    RemoveService.soap_export_as = "RemoveService"


    def UpdateData(self, dataDescription):
        """
        Replace the current description for dataDescription.name with
        this one.

        Send out an update event.
        """

        name = dataDescription.name

        if not self.data.has_key(name):
            #
            # We don't already have this data; raise an exception.
            #

            log.exception("UpdateData: data not already present: %s", name)
            raise VenueException("UpdateData: data %s not already present" %
                                 name)

        self.data[dataDescription.name] = dataDescription
        log.debug("Distribute UPDATE_DATA event %s", dataDescription)
        self.server.eventService.Distribute( self.uniqueId,
                                      Event( Event.UPDATE_DATA,
                                             self.uniqueId,
                                             dataDescription ) )

    def GetData(self, name):
        """
        GetData is the method called by a VenueClient to retrieve information
        about the data. This might also be the operation that the VenueClient
        uses to actually retrieve the real data.
        """

        #
        # If we do not have a running datastore, never return a descriptor
        # (So that data doesn't even show up in the venue).
        #
        if self.dataStore is None:
            return ''

        if self.data.has_key(name):
            return self.data[name]
        else:
            return ''

    GetData.soap_export_as = "GetData"

    def RemoveData(self, dataDescription):
        """
        RemoveData removes persistent data from the Virtual Venue.
        """
        name = dataDescription.name
        
        if name in self.data:
            del self.data[ dataDescription.name ]
            
            # This is venue resident so delete the file
            if(dataDescription.type == None):
                self.dataStore.DeleteFile(dataDescription.name)
                
            # Send the event
            self.server.eventService.Distribute( self.uniqueId,
                                                 Event( Event.REMOVE_DATA,
                                                        self.uniqueId,
                                                        dataDescription ) )
        else:
            log.exception("Data not found!")
            raise VenueException("Data not found.")

    def GetUploadDescriptor(self):
        """
        Retrieve the upload descriptor from the Venue's datastore.

        If the venue has no data store configured, return None.
        """

        #
        # Sigh. Return '' because None marshals as "None".
        #
        if self.dataStore is None:
            return ''
        else:
            return self.dataStore.GetUploadDescriptor()

    GetUploadDescriptor.soap_export_as = "GetUploadDescriptor"

    #
    # Application support
    #

    def GetApplication(self, id):
        """
        Return the application state for the given application object.
        """

        if self.applications.has_key(id):
            app = self.applications[id]
            return app.GetState()
        else:
            return None

    GetApplication.soap_export_as = "GetApplication"

    def CreateApplication(self, name, description, mimeType ):
        """
        Create a new application object.  Initialize the
        implementation, and create a web service interface for it.
        """
        
        log.debug("Create application name=%s description=%s", name, description)

        appImpl = AppService.CreateApplication(name, description, mimeType, 
                                           self.server.eventService)
        app = AppService.AppObject(appImpl)
        hostObj = self.server.hostingEnvironment.create_service_object()
        app._bind_to_service(hostObj)
        appHandle = hostObj.GetHandle()
        self.applications[appImpl.GetId()] = appImpl
        appImpl.SetHandle(appHandle)

        ad = ApplicationDescription(appImpl.GetId(), name, description,
                                    appHandle, mimeType)
        
        self.server.eventService.Distribute( self.uniqueId,
                                             Event( Event.ADD_APPLICATION,
                                                    self.uniqueId,
                                                    ad ) )
        
        log.debug("Created app id=%s handle=%s", appImpl.GetId(), appHandle)

        return appHandle

    CreateApplication.soap_export_as = "CreateApplication"

    def StartApplications(self):
        """
        Restart the application services after a server restart.

        For each app impl, awaken the app, and create a new
        web service binding for it.
        """

        for appImpl in self.applications.values():
            appImpl.Awaken(self.eventService)
            app = AppService.AppObject(appImpl)
            hostObj = self.hostingEnvironment.create_service_object()
            app._bind_to_service(hostObj)
            appHandle = hostObj.GetHandle()
            appImpl.SetHandle(appHandle)
            log.debug("Restarted app id=%s handle=%s", appImpl.GetId(), appHandle)

    def DestroyApplication(self, appId):
        """
        Destroy an application object.

        """

        #
        # This needs to be more robust; in particular we need
        # to pay attention to reference counts to ensure that
        # the app instances all go away so that the objects
        # get deleted. This involves the hosting environment
        # deregistering the handlers properly.
        #
        # For now we'll just remove the reference to the app.
        #
        
        if self.applications.has_key(appId):
            self.applications[appId].Shutdown()

            appImpl = self.applications[appId]
            ad = ApplicationDescription(appImpl.GetId(), appImpl.name, appImpl.description,
                                        appImpl.handle, appImpl.mimeType)
            self.server.eventService.Distribute( self.uniqueId,
                                                 Event( Event.REMOVE_APPLICATION,
                                                        self.uniqueId,
                                                        ad ) )
            del self.applications[appId]


    DestroyApplication.soap_export_as = "DestroyApplication"

class StreamDescriptionList:
    """
    Class to represent stream descriptions in a venue.  Entries in the
    list are a tuple of (stream description, producing users).  A stream
    is added to the list with a producer.  Producing users can be added
    to and removed from an existing stream.  When the number of users
    producing a stream becomes zero, the stream is removed from the list.

    Exception:  static streams remain without regard to the number of producers

    """

    def __init__( self ):
        self.streams = []

    def AddStream( self, stream ):
        """
        Add a stream to the list, only if it doesn't already exist
        """
        if not self.FindStreamByDescription(stream):
            self.streams.append( ( stream, [] ) )
        
    def RemoveStream( self, stream ):
        """
        Remove a stream from the list
        """
        streamListItem = self.FindStreamByDescription(stream)
        if streamListItem != None:
            self.streams.remove(streamListItem)

    def AddStreamProducer( self, producingUser, inStream ):
        """
        Add a stream to the list, with the given producer
        """
        streamListItem = self.FindStreamByDescription(inStream)
        if streamListItem != None:
            (streamDesc, producerList) = streamListItem
            producerList.append( producingUser )
        else:
            self.streams.append( (inStream, [ producingUser ] ) )
            log.debug( "* * * Added stream producer %s", producingUser )

    def RemoveStreamProducer( self, producingUser, inStream ):
        """
        Remove a stream producer from the given stream.  If the last
        producer is removed, the stream will be removed from the list
        if it is non-static.
        """
        self.__RemoveProducer( producingUser, inStream )
        streamListItem = self.FindStreamByDescription(inStream)
        if streamListItem != None:
            (streamDesc, producerList) = streamListItem
            if len(producerList) == 0:
                self.streams.remove((streamDesc, producerList))
            

    def RemoveProducer( self, producingUser ):
        """
        Remove producer from all streams
        """
        for stream, producerList in self.streams:
            self.__RemoveProducer( producingUser, stream )

        self.CleanupStreams()

    def __RemoveProducer( self, producingUser, inStream ):
        """
        Internal : Remove producer from stream with given index
        """
        streamListItem = self.FindStreamByDescription(inStream)
        if streamListItem != None:
            (stream, producerList) = streamListItem
            if producingUser in producerList:
                producerList.remove( producingUser )

    def CleanupStreams( self ):
        """
        Remove streams with empty producer list
        """
        streams = []
        for stream, producerList in self.streams:
            if len(producerList) > 0 or stream.static == 1:
                streams.append( ( stream, producerList ) )
        self.streams = streams

    def GetStreams( self ):
        """
        Get the list of streams, without producing user info
        """
        return map( lambda streamTuple: streamTuple[0], self.streams )

    def GetStaticStreams(self):
        """
        GetStaticStreams returns a list of static stream descriptions
        to the caller.
        """
        staticStreams = []
        for stream, producerList in self.streams:
#             log.debug("GetStaticStreams - Location: %s %d", 
#                       stream.location.GetHost(),
#                       stream.location.GetPort())
#             log.debug("GetStaticStreams - Capability: %s %s",
#                       stream.capability.role,
#                       stream.capability.type)
#             log.debug("GetStaticStreams - Encyrption Key: %s",
#                       stream.encryptionKey)
#             log.debug("GetStaticStreams - Static: %d",
#                       stream.static)
            if stream.static:
                staticStreams.append( stream )
        return staticStreams

    def FindStreamByDescription( self, inStream ):
        """
        """
        for stream, producerList in self.streams:
            log.debug("StreamDescriptionList.index Address %s %s",
                      inStream.location.host,
                      stream.location.host)
            log.debug("StreamDescriptionList.index Port %d %d",
                      inStream.location.port,
                      stream.location.port)
            if inStream.location.host == stream.location.host and \
                   inStream.location.port == stream.location.port:
                return (stream, producerList)

        return None

