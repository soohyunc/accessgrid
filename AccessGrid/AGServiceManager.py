#-----------------------------------------------------------------------------
# Name:        AGServiceManager.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/08/02
# RCS-ID:      $Id: AGServiceManager.py,v 1.12 2003-02-24 20:56:23 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
import sys
import urllib
import os
import socket
import time

try:     import win32process
except:  pass


from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.hosting.pyGlobus.ServiceBase import ServiceBase
from AccessGrid.hosting.pyGlobus.AGGSISOAP import faultType

from AccessGrid.Descriptions import AGServiceDescription
from AccessGrid.Types import AGServicePackage
from AccessGrid.AuthorizationManager import AuthorizationManager
from AccessGrid.DataStore import GSIHTTPDownloadFile
from AccessGrid import Utilities


class AGServiceManager( ServiceBase ):
    """
    AGServiceManager : exposes local resources and configures services to deliver them
    """

    def __init__( self ):
        self.name = None
        self.description = None
        self.resources = []
        # note: services dict is keyed on pid
        self.services = dict()
        self.authManager = AuthorizationManager()
        self.executable = None

        self.nextToken = 9500

        # note: unregisteredServices dict is keyed on token
        self.unregisteredServices = dict()

        self.servicesDir = "local_services"

    ####################
    ## AUTHORIZATION methods
    ####################

    def SetAuthorizedUsers( self, authorizedUsers ):
        """
        Set the authorizedUsers list; this is usually pushed from a NodeService,
        thus this wholesale Set of the authorized user list.  Also, push this
        list to known services
        """

        try:
            self.authManager.SetAuthorizedUsers( authorizedUsers )
            print "got authorized user list", authorizedUsers

            self.__PushAuthorizedUserList()
        except:
            print "AGServiceManager.SetAuthorizedUsers : ", sys.exc_type, sys.exc_value
            raise faultType("AGServiceManager.SetAuthorizedUsers failed: " + str( sys.exc_value ))
    SetAuthorizedUsers.soap_export_as = "SetAuthorizedUsers"


    ####################
    ## RESOURCE methods
    ####################

    def GetResources( self ):
        """
        Return a list of resident resources
        """
        self.__DiscoverResources()

        return self.resources
    GetResources.soap_export_as = "GetResources"


    def DiscoverResources( self ):
        """Discover local resources (audio cards, etc.)
        """
        try:
            self.__DiscoverResources()
        except:
            raise faultType("AGServiceManager.DiscoverResources failed: " + str( sys.exc_value ))
    DiscoverResources.soap_export_as = "DiscoverResources"


    ####################
    ## SERVICE methods
    ####################

    def AddService( self, serviceDescription, resourceToAssign ):
        """
        Add a service to the service manager.  The service is an executable
        or python script, which will be started by the ServiceManager
        """
        try:
            #
            # Determine resource to assign to service
            #
            print "** resourceToAssign = ", resourceToAssign, type(resourceToAssign)
            if resourceToAssign != None and resourceToAssign != "None":
                foundResource = 0
                for resource in self.resources:
                    if resource.resource == resourceToAssign.resource:
                        if resource.inUse == 1:
                            print "** Resource is already in use ! ", resource.resource
                            # should error out here later; for now, services aren't using the resources anyway
                        foundResource = 1
                        break

                if foundResource == 0:
                    print "** Resource does not exist! ", resourceToAssign.resource
#FIXME - # should error out here later; for now, services aren't using the resources anyway

        except:
            print "Exception in AddService, checking resource\n-- ", sys.exc_type, sys.exc_value
            raise faultType("AGServiceManager.AddService failed: " + str( sys.exc_value ))


        try:
            #
            # Check for local copy of service implementation
            #
            # -- not yet implemented

            #
            # Retrieve service implementation
            #
            servicePackageFile = self.__RetrieveServicePackage( serviceDescription.uri )
            serviceDescription.resource = resourceToAssign
            print "service description = ", serviceDescription.name, serviceDescription.description, serviceDescription.executable
            self.__AddServiceDescription( serviceDescription )

        except:
            print "Exception in AddService, retrieving service implementation\n-- ", sys.exc_type, sys.exc_value
            raise faultType("AGServiceManager.AddService failed: " + str( sys.exc_value ) )

    AddService.soap_export_as = "AddService"


    def AddServiceDescription( self, serviceDescription ):
        """
        Add a service to the service manager.  The service is an executable
        or python script, which will be started by the ServiceManager
        """
        try:
            serviceDescription = AGServiceDescription( serviceDescription.name,
                                                       serviceDescription.description,
                                                       serviceDescription.uri,
                                                       serviceDescription.capabilities,
                                                       serviceDescription.resource,
                                                       serviceDescription.serviceManagerUri,
                                                       serviceDescription.executable )

            self.__AddServiceDescription( serviceDescription )
        except:
            print "Exception in AGServiceManager.AddServiceDescription ", sys.exc_type, sys.exc_value
            raise faultType("AGServiceManager.AddServiceDescription failed: " + str( sys.exc_value ))
    AddServiceDescription.soap_export_as = "AddServiceDescription"


    def RemoveService( self, serviceToRemove ):
        """Remove a service
        """
        exc = None
        pid = None

        try:

            #
            # Find service to stop using uri
            #
            for key in self.services.keys():
                service = self.services[key]
                if service.uri == serviceToRemove.uri:

                    pid = key
                    Client.Handle( service.uri ).get_proxy().Stop()

                    #
                    # Kill service pid (note: key is pid)
                    #
                    if sys.platform == 'win32':
                        win32process.TerminateProcess( pid, 0 )
                    else:
                        os.kill( pid, 9 )

                    #
                    # Wait on it
                    #
                    try:
                        os.waitpid( pid, 1 )
                    except:
                        pass

                    #
                    # Free the resource
                    #
                    if service.resource.resource != None and service.resource.resource != "None":
                        foundResource = 0
                        for resource in self.resources:
                            if resource.resource == service.resource.resource:
                                resource.inUse = 0
                                foundResource = 1

                        if foundResource == 0:
                            print "** The resource used by the service can not be found !! ", service.resource.resource

                    break

        except:
            print "Exception in AGSM.RemoveService ", sys.exc_type, sys.exc_value
            exc = sys.exc_value

        #
        # Remove service from list
        #
        if pid:
            print "Removing service from list"
            del self.services[pid]

        # raise exception now, if one occurred
        if exc:
            raise faultType("AGServiceManager.RemoveService failed : ", str( exc ) )

    RemoveService.soap_export_as = "RemoveService"


    def RemoveServices( self ):
        """Remove all services
        """

        try:
            for service in self.services.values():
                self.RemoveService( service )
        except:
            print "Exception in AGServiceManager.RemoveServices ", sys.exc_type, sys.exc_value
            raise faultType("AGServiceManager.RemoveServices failed : " + str( sys.exc_value ) )
    RemoveServices.soap_export_as = "RemoveServices"


    def GetServices( self ):
        """Return list of services
        """
        return self.services.values()
    GetServices.soap_export_as = "GetServices"


    def StopServices( self ):
        """
        Stop all services on service manager
        """
        for service in self.services.values():
            print "stopping service at uri ", service.uri
            Client.Handle( service.uri ).get_proxy().Stop()

    StopServices.soap_export_as = "StopServices"


    def RegisterService( self, token, uri ):
        """
        Register a service with the service manager.  Why?  When the service manager
        executes a service implementation, it assigns it a token.  When the service
        actually starts, it registers with the service manager by passing this token
        and its uri
        """

        try:

            # Use the token to identify the unregistered service
            #
            pid, service = self.unregisteredServices[token]
            del self.unregisteredServices[token]

            # Set the uri and add service to list of services
            #
            service.uri = uri
            self.services[pid] = service

            # Push authorized user list
            print "* * * Pushing Authorized user list"
            Client.Handle( service.uri ).get_proxy().SetAuthorizedUsers( self.authManager.GetAuthorizedUsers() )

            # Assign resource to the service
            #
            print "NOW SETTING RESOURCE "
            Client.Handle( service.uri ).get_proxy().SetResource( service.resource )

        except:
            print "--- Exception in RegisterService ", sys.exc_type, sys.exc_value
            raise faultType("AGServiceManager.RegisterService failed: " + str( sys.exc_value ))

    RegisterService.soap_export_as = "RegisterService"


    def Ping( self ):
        return 1
    Ping.soap_export_as = "Ping"


    ####################
    ## INTERNAL methods
    ####################

    def __PushAuthorizedUserList( self ):
        """Push the list of authorized users to service managers"""
        for service in self.services.values():
            Client.Handle( service.uri ).get_proxy().SetAuthorizedUsers( self.authManager.GetAuthorizedUsers() )


    def __RetrieveServicePackage( self, servicePackageUrl ):
        """Internal : Retrieve a service implementation"""
        print "Retrieving ", servicePackageUrl

        #
        # Retrieve the service package
        #
        filename = os.path.basename( servicePackageUrl )
        servicePackageFile = self.servicesDir + os.sep + filename
        GSIHTTPDownloadFile(servicePackageUrl, servicePackageFile, None, None)

        #
        # Extract the executable from the service package
        #
        servicePackage = AGServicePackage( servicePackageFile )
        servicePackage.ExtractExecutable( self.servicesDir )

        return servicePackageFile


    def __AddServiceDescription( self, serviceDescription ):
        """
        Internal : Start the service with given description
        """
        try:
            options = []


            if serviceDescription.executable.endswith(".py"):
                executable = sys.executable
                options.append( sys.executable )
                options.append( self.servicesDir + os.sep + serviceDescription.executable )
            else:
                executable = self.servicesDir + os.sep + serviceDescription.executable
                options.append( executable )

            token = '%d' %(self.nextToken)

            options.append( '%d' % self.nextToken )
            options.append( self.get_handle() )
            self.nextToken = self.nextToken + 1

            print "starting with options ", executable, options
            pid = os.spawnv( os.P_NOWAIT, executable, options )


        except:
            print "Exception in AddService, starting service ", sys.exc_type, sys.exc_value
            raise sys.exc_value

        try:

            #
            # Add the service to the list
            #
            serviceDescription.serviceManagerUri = self.get_handle()
            self.unregisteredServices[token] = ( pid, serviceDescription )
            print "service added ", serviceDescription.name, serviceDescription.uri, serviceDescription.serviceManagerUri, self.get_handle()

        except:
            print "Exception in AddService, other ", sys.exc_type, sys.exc_value
            raise sys.exc_value


    def __DiscoverResources( self ):
        """Discover local resources (video capture cards, etc.)
        """
        self.resources = Utilities.GetResourceList()
