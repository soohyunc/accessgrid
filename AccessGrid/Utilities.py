#-----------------------------------------------------------------------------
# Name:        Utilities.py
# Purpose:
#
# Author:      Everyone
#
# Created:     2003/23/01
# RCS-ID:      $Id: Utilities.py,v 1.65 2004-05-04 20:35:07 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""

__revision__ = "$Id: Utilities.py,v 1.65 2004-05-04 20:35:07 turam Exp $"
__docformat__ = "restructuredtext en"

import os
import string
import sys
import traceback
import ConfigParser
import time
from random import Random
import sha
import urllib
import urlparse
from threading import Lock, Condition
import re

from AccessGrid import Log
log = Log.GetLogger(Log.Utilities)

from AccessGrid.Version import GetVersion
from AccessGrid import Platform
from AccessGrid.Platform import Config

# Global variables for sending log files
VENUE_CLIENT_LOG = 0
VENUE_MANAGEMENT_LOG = 1
NODE_SETUP_WIZARD_LOG = 2
NO_LOG = 3


def LoadConfig(fileName, config=dict(), separator="."):
    """
    Returns a dictionary with keys of the form <section>.<option>
    and the corresponding values.
    This is from the python cookbook credit: Dirk Holtwick.
    """
    rconfig = config.copy()
    cp = ConfigParser.ConfigParser()
    cp.optionxform = str
    cp.read(fileName)
    for sec in cp.sections():
        for opt in cp.options(sec):
            rconfig[sec + separator + opt] = string.strip(cp.get(sec, opt, 1))
    return rconfig

def SaveConfig(fileName, config, separator="."):
    """
    This method saves the current configuration out to the specified file.
    """
    cp = ConfigParser.ConfigParser()
    cp.optionxform = str
    section = ""
    option = ""
    value = ""
    for k in config.keys():
        if k.find(separator) != -1:
            (section, option) = k.split(separator)
        value = config[k]
        if not cp.has_section(section):
            try:
                cp.add_section(section)
            except:
                print "Couldn't add section."
        try:
            if option != "None":
                cp.set(section, option, value)
        except:
            print "Couldn't set option."

    try:
        outFile = file(fileName, 'w+')
    except IOError, e:
        print "Couldn't open file for writing, database mods lost."
        return

    cp.write(outFile)
    outFile.close()

def GetRandInt(r):
    return int(r.random() * sys.maxint)
    
def AllocateEncryptionKey():
    """
    This function returns a key that can be used to encrypt/decrypt media
    streams.    
    
    Return: string
    """
    rg = Random(time.time())
    
    intKey = GetRandInt(rg)
    
    for i in range(1, 8):
        intKey = intKey ^ rg.randrange(1, sys.maxint)

    return "%x" % intKey

def GetLogText(maxSize, logFileName):
    '''
    Reads log records, based on todays date, from log file.  

    **Arguments:**
    
    *logFileName* Name of log file to read from.
    *maxSize* The maximum number of bytes we want to read from the log file.
      
    **Returns:**
    
    *test* a string including log records from todays date.
    If the log file is missing, GetLogText will return the error message
    received when trying to read the file.  If the log file does not include any
    records from today, the last "maxSize" bytes of the file will be included in the string.
    '''
        
    try:
        #
        # Try to get text from the log file.
        #
        logFile = file(logFileName)
        
        #
        # Move to a position "maxSize" bytes from the end of the file. 
        # The read will now just include the end of the file with a maximum
        # of "maxSize" bytes
        #
                   
        try:
            # If the file is smaller than "maxSize" this will fail
            # and the entire file will be read.
            logFile.seek(-maxSize, 2)
           
        except:
            # Start from beginning of file again
            logFile.seek(0)

        text = logFile.read(maxSize) # text for error report             
        logFile.close()
    
    except Exception,e:
        #
        # If reading the log file failed somehow, the text sent in the
        # error report contains the received error message
        #
        (name, args, traceback_string_list) = formatExceptionInfo()
        
        traceback = ""
        for x in traceback_string_list:
            traceback += x + "\n"

  
        text = logFileName + " could not be located "

    # Seek for todays date to just include relevant
    # log messages in the error report
    #
    
    #todaysDate = time.strftime("%m/%d/%Y", time.localtime())
    #dateIndex = text.find(str(todaysDate))
    
    #if dateIndex != -1:
        #
        # If today's date is found, send log info starting from that index.
        # Else, the last "maxSize" bytes of the log file is sent
        #
        
        #text = text[dateIndex:]

    return text

def SubmitBug(comment, profile, email, userConfig, logFile = VENUE_CLIENT_LOG):
    """
    Submits a bug to bugzilla. 

    **Parameters**
      *comment* = Bug description from reporter
      *profile* = Client Profile describing reporter
      *email* = Entered email address for support information. If the email
                is blank, the reporter does not want to be contacted.
      
    """
     
    url = "http://bugzilla.mcs.anl.gov/accessgrid/post_bug.cgi"
    args = {}

    bugzilla_login = 'client-ui-bugzilla-user@mcs.anl.gov'
    bugzilla_password = '8977f68349f93fead279e5d4cdf9c3a3'

    args['Bugzilla_login'] = bugzilla_login
    args['Bugzilla_password'] = bugzilla_password
    args['version'] = str(GetVersion())
    args['rep_platform'] = "Other"
    
    #
    # This detection can get beefed up a lot; I say
    # NT because I can't tell if it's 2000 or XP and better
    # to not assume there.
    #
    # cf http://www.lemburg.com/files/python/platform.py
    #
    
    if Platform.IsLinux():
        args['op_sys'] = "Linux"
        args['rep_platform'] = "All"  # Need a better check for this.
    elif Platform.IsWindows():
        args['op_sys'] = "Windows NT"
        args['rep_platform'] = "PC"
    elif Platform.IsOSX():
        args['op_sys'] = "MacOS X"
        args['rep_platform'] = "Macintosh"
    else:
        args['op_sys'] = "other"
        
    args['priority'] = "P2"
    args['bug_severity'] = "normal"
    args['bug_status'] = "NEW"
    args['assigned_to'] = ""
    args['cc'] = "lefvert@mcs.anl.gov"   # email to be cc'd
    args['bug_file_loc'] = "http://"
    
    
    args['submit'] = "    Commit    "
    args['form_name'] = "enter_bug"
    
    # Combine comment, profile, and log file information
    userConfigDir = userConfig.GetConfigDir()

    # Get config information
    configData =  "\n%s" % Config.AGTkConfig.instance()
    configData += "\n%s" % Config.UserConfig.instance()
    configData += "\n%s" % Config.GlobusConfig.instance()
    configData += "\n%s\n" % Config.SystemConfig.instance()

    # Defaults.
    args['product'] = "Virtual Venues Client Software"
    args['component'] = "Client UI"
    logToSearch = None
    
    if profile:
        # Always set profile email to empty string so we don't write
        # to wrong email address.
        profile.email = ""
        profileString = str(profile)

    else:
        profileString = "This reporter does not have a client profile"
        
    if email == "":
        # This reporter does not want to be contacted. Do not submit
        # email address.
        email = "This reporter does not want to be contacted.  No email address specified."

        
    commentAndLog = "\n\n--- EMAIL TO CONTACT REPORTER ---\n\n" + str(email) \
                +"\n\n--- REPORTER CLIENT PROFILE --- \n\n" + profileString \
                +"\n\n--- COMMENT FROM REPORTER --- \n\n" + comment 


    if logFile == NO_LOG:
        args['short_desc'] = "Feature or bug report from menu option"

    elif logFile == VENUE_MANAGEMENT_LOG:
        args['short_desc'] = "Crash in Venue Management UI"

        args['product'] = "Virtual Venue Server Software"
        args['component'] = "Management UI"
        
        logText = GetLogText(20000, os.path.join(userConfigDir,
                                                 "VenueManagement.log"))
        commentAndLog = commentAndLog \
            +"\n\n--- VenueManagement.log INFORMATION ---\n\n"+ logText
        
    elif logFile == NODE_SETUP_WIZARD_LOG:
        args['short_desc'] = "Crash in Node Setup Wizard UI"

        args['product'] = "Node Management Software"
        args['component'] = "NodeSetupWizard"

        logText = GetLogText(20000, os.path.join(userConfigDir,
                                                 "NodeSetupWizard.log"))
        commentAndLog = commentAndLog \
            +"\n\n--- NodeSetupWizard.log INFORMATION ---\n\n"+ logText

    else:
        args['short_desc'] = "Automatic Bug Report"
        logToSearch = GetLogText(20000, os.path.join(userConfigDir,
                                                     "VenueClient.log"))
        commentAndLog = commentAndLog \
             +"\n\n--- VenueClient.log INFORMATION ---\n\n"+ logToSearch \
             +"\n\n--- agns.log INFORMATION ---\n\n"+GetLogText(20000,
                                 os.path.join(userConfigDir, "agns.log"))\
             +"\n\n--- agsm.log INFORMATION ---\n\n"+GetLogText(20000,
                                 os.path.join(userConfigDir, "agsm.log"))\
             +"\n\n--- AGService.log INFORMATION ---\n\n"+GetLogText(20000,
                                 os.path.join(userConfigDir, "AGService.log"))

    # If we've got a logToSearch, look at it to find a GSI exception
    # at the end.  If it has one, mark the component as Certificate
    # Management.

    if logToSearch:
        loc = logToSearch.rfind("Traceback")
        if loc >= 0:
            m = re.search("GSI.*Exception.*", logToSearch[loc:])
            if m:
                args['component'] = "Certificate Management"

        logToSearch = None

    # Look at the end of the log and guess whether we need to mark this 
    args['comment']= configData + "\n\n" + commentAndLog
      
    # Now submit to the form.
    params = urllib.urlencode(args)
    f = urllib.urlopen(url, params)
    
    # And read the output.
    out = f.read()
    f.close()
        
    o = open("out.html", "w")
    o.write(out)
    o.close()

class ServerLock:
    """
    Class to be used for locking entry and exit to the venue server.
    Mostly just a wrapper around a normal lock, but adds logging support.
    """

    verbose = 0

    def __init__(self, name = ""):
        if self.verbose:
            log.debug("Create server lock %s", name)
        self.lock = Condition(Lock())
        self.name = name

    def acquire(self):
        if self.verbose:
            c = (traceback.extract_stack())[-2]
            file = c[0]
            line = c[1]
            log.debug("Try to acquire server lock %s...      %s:%s", self.name, file, line)

        self.lock.acquire()

        if self.verbose:
            log.debug("Try to acquire server lock %s...done  %s:%s", self.name, file, line)

    def release(self):
        if self.verbose:
            c = (traceback.extract_stack())[-2]
            file = c[0]
            line = c[1]
            log.debug("Releasing server lock %s  %s:%s", self.name, file, line)
        self.lock.release()

#
# File tree removal stuff, from ASPN recipe.
#

def _rmgeneric(path, func):
    try:
        log.debug("Remove %s with %s", path, func)
        func(path)
    except OSError, (errno, strerror):
        log.error("rmgeneric: error removing %s", path)
           
def removeall(path):

    if not os.path.isdir(path):
        return
   
    files=os.listdir(path)

    for x in files:
        fullpath=os.path.join(path, x)
        if os.path.isfile(fullpath):
            f=os.remove
            _rmgeneric(fullpath, f)
        elif os.path.isdir(fullpath):
            removeall(fullpath)
            f=os.rmdir
            _rmgeneric(fullpath, f)

#
# split_quoted borrowed from distutils.
#
# We're using it without the backslash escaping enabled
# so that we can use it for windows pathnames.
#


# Needed by 'split_quoted()'
_wordchars_re = re.compile(r'[^\'\"%s ]*' % string.whitespace)
_squote_re = re.compile(r"'(?:[^'\\]|\\.)*'")
_dquote_re = re.compile(r'"(?:[^"\\]|\\.)*"')

def split_quoted (s):
    """Split a string up according to Unix shell-like rules for quotes and
    backslashes.  In short: words are delimited by spaces, as long as those
    spaces are not escaped by a backslash, or inside a quoted string.
    Single and double quotes are equivalent, and the quote characters can
    be backslash-escaped.  The backslash is stripped from any two-character
    escape sequence, leaving only the escaped character.  The quote
    characters are stripped from any quoted string.  Returns a list of
    words.
    """
    
    # This is a nice algorithm for splitting up a single string, since it
    # doesn't require character-by-character examination.  It was a little
    # bit of a brain-bender to get it working right, though...

    s = string.strip(s)
    words = []
    pos = 0

    while s:
        m = _wordchars_re.match(s, pos)
        end = m.end()
        if end == len(s):
            words.append(s[:end])
            break

        if s[end] in string.whitespace: # unescaped, unquoted whitespace: now
            words.append(s[:end])       # we definitely have a word delimiter
            s = string.lstrip(s[end:])
            pos = 0

        else:
            if s[end] == "'":           # slurp singly-quoted string
                m = _squote_re.match(s, end)
            elif s[end] == '"':         # slurp doubly-quoted string
                m = _dquote_re.match(s, end)
            else:
                raise RuntimeError, \
                      "this can't happen (bad char '%c')" % s[end]

            if m is None:
                raise ValueError, \
                      "bad string (mismatched %s quotes?)" % s[end]

            (beg, end) = m.span()
            s = s[:beg] + s[beg+1:end-1] + s[end:]
            pos = m.end() - 2

        if pos >= len(s):
            words.append(s)
            break

    return words

# split_quoted ()

if __name__ == "__main__":
    SubmitBug("This is just a test for the Bug Reporting Tool", profile=None,
              email="", userConfig=Config.UserConfig.instance(),
              logFile=NO_LOG)

