#-----------------------------------------------------------------------------
# Name:        SOAPInterface.py
# Purpose:     Base class for all SOAP interface objects, this has the
#              constructor and authorization callback defined.
#
# Author:      Ivan R. Judson
#
# Created:     2003/23/01
# RCS-ID:      $Id: SOAPInterface.py,v 1.4 2004-03-02 19:12:17 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
This is the base class for all SOAP interface objects. It has two
primary methods, the constructor and a default authorization for all
interfaces.
"""

__revision__ = "$Id: SOAPInterface.py,v 1.4 2004-03-02 19:12:17 judson Exp $"
__docformat__ = "restructuredtext en"

# External imports
import re

# AGTk imports
from AccessGrid.hosting import Client
from AccessGrid.Security.Action import MethodAction

methodPat = re.compile("^<(slot wrapper|bound method|built-in method) .+>$")

class InvalidURL(Exception):
    """
    This is raised when a url doesn't point to a service.
    """
    pass

class ConnectionFailed(Exception):
    """
    This is raised when a SOAP client can't connect to a service.
    """
    pass

class SOAPInterface:
    """
    This is the SOAP Interface object. It is meant to be derived from for all
    real SOAP Interfaces. This object provides the glue for how the interfaces
    and implementations get stuck together. It also provides a default
    authorization method that returns 0 (not authorized).
    """
    def __init__(self, impl):
        """
        This constructor for all SOAP Interfaces.

        @param impl: an implementation object messages are routed to.
        @type impl: a python object.
        """
        self.impl = impl

    def _authorize(self, *args, **kw):
        """
        This is meant to be a base class for all SOAP interfaces, so it's going
        to default to disallow calls. Derived interfaces can tailor this to
        suit their needs.

        @return: 1, things are authorized by default right now.
        """
        return 1

    def _GetMethodActions(self):
        """
        This method extracts all the methods and creates MethodActions
        for them, which means Authorization can be automatically
        loaded with actions for all the methods on an interface
        object.

        @return: a list of AccessGrid.Security.Action.MethodAction objects.
        """
        global methodPat
        obj = self
        actions = list()

        # Here we preload the methods as actions
        for attrName in dir(obj):
            if attrName.startswith("_"):
                # don't register private methods
                pass
            else:
                try:
                    attr = eval("obj.%s" % attrName)
                    attrRepr = repr(attr)
                    m = methodPat.match(attrRepr)
                    if m:
                        actions.append(MethodAction(attrName))
                except:
                    print "Blew up trying to register methods."
                    raise

        return actions

    def IsValid(self):
        """
        This method is here to support calls that just want to see if there
        is a valid server endpoint for communication from the client.

        @returns: 1
        """
        return 1

class SOAPIWrapper:
    """
    A SOAP interface wrapper object. This object helps provide a rich
    encapsulation of the SOAP implementation underneath.
    """
    def __init__(self, url=None):
        """
        The constructor.

        @param url: the url to the SOAP interface.
        @type url: string

        @raises InvalidURL: if the url doesn't point ot a service
        @raises ConnectionFailed: if client can't connection to the service.
        """
        self.proxy = None
        self.url = url
        if url != None:
            try:
                self.proxy = Client.Handle(self.url).GetProxy()
            except:
                self.proxy = None
                raise ConnectionFailed
        else:
            raise InvalidURL

    def IsValid(self):
        """
        Method to provide interface verification.

        @returns: the result of calling across the network to the service.
        """
        return self.proxy.IsValid()
    
    def _IsValid(self):
        """
        This method is here to support calls that just want to see if there
        is a valid server endpoint for communication from the client.
        """
        return 1

