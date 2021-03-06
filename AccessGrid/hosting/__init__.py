#-----------------------------------------------------------------------------
# Name:        __init__.py
# Purpose:     
#
# Author:      Ivan R. Judson, Robert D. Olson
#
# Created:     2003/08/02
# RCS-ID:      $Id: __init__.py,v 1.17 2005-11-02 21:06:32 eolson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
AG Hosting environment tools.
"""
__revision__ = "$Id: __init__.py,v 1.17 2005-11-02 21:06:32 eolson Exp $"
__docformat__ = "restructuredtext en"

# External imports
import os
import urlparse

# mechanisms to support multiple hosting environments and to set defaults
__hostingImpl = "ZSI"

# pointers to methods and objects, helpful magic
SecureServer = lambda x: None
InsecureServer = lambda x: None
GetSOAPContext = lambda x: None
Client = lambda x: None
Decorate = lambda x: None
Reconstitute = lambda x: None
__root = lambda x: None

HostingException = lambda x: None
GetHostingExceptionModuleAndClassName = lambda x: None
GetHostingException = lambda x: None
ReraiseHostingException = lambda x: None
NotAuthorized = lambda x: None
NoSuchService = lambda x: None

def GetHostingImpl():
    """
    Return the currently selected hosting implementation.

    @return: string
    """
    global __hostingImpl
    return __hostingImpl

def SetHostingImpl(choice):
    """
    Set the hosting implementation to the one specifed.

    @param choice: the hosting implementation to use
    @type choice: string

    @return: 1 if successful, None if not
    """
    global __hostingImpl, __root, Server, Client, Decorate, Reconstitute
    global GetSOAPContext, SecureServer, InsecureServer
    global HostingException, GetHostingExceptionModuleAndClassName, GetHostingException, ReraiseHostingException, NotAuthorized, NoSuchService
    
    __hostingImpl = choice
    
    nis = ".".join([__name__, __hostingImpl, "Server"])
    nic = ".".join([__name__, __hostingImpl])
    nit = ".".join([__name__, __hostingImpl, "Tools"])

    try:
        s = __import__(nis, globals(), locals(), ["SecureServer",
                                                  "InsecureServer",
                                                  "GetSOAPContext"])
        SecureServer = s.SecureServer
        InsecureServer = s.InsecureServer
        GetSOAPContext = s.GetSOAPContext
    except ImportError:
        raise
    
    try:
        c = __import__(nic, globals(), locals(), ["Client", "HostingException", "GetHostingExceptionModuleAndClassName", "GetHostingException", "ReraiseHostingException", "NotAuthorized", "NoSuchService"])
        Client = c.Client
        HostingException = c.HostingException
        NotAuthorized = c.NotAuthorized
        NoSuchService = c.NoSuchService
        GetHostingExceptionModuleAndClassName = c.GetHostingExceptionModuleAndClassName
        GetHostingException = c.GetHostingException
        ReraiseHostingException = c.ReraiseHostingException
    except ImportError:
        raise

    try:
        t = __import__(nit, globals(), locals(), ["Decorate",
                                                  "Reconstitute"])
        Decorate = t.Decorate
        Reconstitute = t.Reconstitute
    except ImportError:
        raise
    
    return 1

def ListHostingImpls():
    """
    This method lists the hosting implementations currently isntalled.

    @return: a list of hosting implementation names.
    """
    global __root
    retList = list()
    for e in os.listdir(__root):
        ae = os.path.join(__root, e)
        if os.path.isdir(ae):
            # Just in case we're using dev source
            if e != 'CVS':
                retList.append(e)
    return retList

def PathFromURL(URL):
    """
    """
    if URL[0:5] == 'httpg':
        return urlparse.urlparse(URL[6:])[2]
    else:
        return urlparse.urlparse(URL)[2]

def IdFromURL(URL):
    """
    """
    path = PathFromURL(URL)
    oid = path.split('/')[-1]

    return oid

# Set the default
SetHostingImpl(__hostingImpl)

