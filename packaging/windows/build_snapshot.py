#
# Build a windows installer snapshot.
#

#
# Basic plan:
#
# This script assumes there is a build directory somewhere with
# basically everything in place to build a distribution.
# invoke the innosetup compiler on the modified iss file
# Also need to modify setup.py to change the version there to match
# this snapshot version.
#
import sys
import os
import time
import getopt
import shutil
import win32api
import _winreg
from win32com.shell import shell, shellcon

#
# The version being packaged
#  We set this to X.Y since it should be specified for every execution
#
AGTkVersion = "X.Y"

# Source Directory
#  We assume the following software is in this directory:
#    ag-rat, ag-vic, and AccessGrid
SourceDir = os.environ['AG_BUILD']

# Build Name
#  This is the default name we use for the installer
BuildTime = time.strftime("%Y%m%d-%H%M%S")

# Create the dest dir stamped with the same time stamp
DestDir = os.path.join(SourceDir, "dist-%s" % BuildTime)

# Names for the software
metainformation = "Snapshot %s" % BuildTime

def usage():
    print """
%s: 
    -h|--help : print usage
    
    -s|--sourcedir <directory>
       The directory the AG source code is in. If the code is in
       The default is: %s
       
    -m|--meta <name>
       Meta information string about this release.
       The default is: %s
    
    -c|--checkoutcvs
       A flag that indicates the snapshot should be built from an
       exported cvs checkout. This is cleaner.
    
    -i|--innopath <directory>
       The path to the isxtool.
       If this is not specified on the command line, the value is retrieved
       from the system registry.
    
    -v|--verbose
       The option to be very very spammy when run.
       """ % (sys.argv[0], SourceDir, metainformation)

# Innosoft config file names
iss_orig = "agtk.iss"

# Innosoft path
innopath = ""

# CVS Flag
checkoutnew = 0

# Verbosity flag
verbose = 0

try:
    opts, args = getopt.getopt(sys.argv[1:], "s:i:m:chv",
                               ["version=", "sourcedir=", "innopath=", 
                                "shortname=", "metainfo=", "checkoutcvs",
                                "help", "verbose"])
except:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == "--version":
        AGTkVersion = a
    elif o in ("-s", "--sourcedir"):
        SourceDir = a
    elif o in ("-i", "--innopath"):
        innopath = a
    elif o in ("-m", "--metainfo"):
        metainformation = a
    elif o in ("-c", "--checkoutcvs"):
        checkoutnew = 1
    elif o in ("-h", "--help"):
        usage()
        sys.exit(0)
    elif o in ("-v", "--verbose"):
        verbose = 1
    else:
        usage()
        sys.exit(0)


BuildDir = os.path.join(SourceDir, "AccessGrid-%s" % BuildTime)
if verbose:
    print "Build Dir: ", BuildDir

#
# Location of the Inno compiler
#

if innopath != "":
    # It was set on the command line
    inno_compiler = os.path.join(innopath, "iscc.exe")
    if not os.path.exists(inno_compiler):
        print "command-line innopath not found: ", inno_compiler
        sys.exit()
else:
    # It wasn't specified, so go find it
    try:
        ipreg = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                                "Software\\Bjornar Henden\\ISTool4\\Prefs")
        innopath, type = _winreg.QueryValueEx(ipreg, "InnoFolder")
        ip = os.path.join(innopath, "iscc.exe")
        inno_compiler = win32api.GetShortPathName(ip)
    except WindowsError:
        print "Couldn't find iscc from registry key." 

    if innopath == "":
        # If still not found, try default path:
        innopath = r"\Program Files\ISTool 4"
        inno_compiler = os.path.join(innopath, "iscc.exe")
        
    if verbose:
        if os.path.exists(inno_compiler):
            print "Found ISXTool in default path:", inno_compiler
        else:
            print "Couldn't find ISXTool!"
            print "  Make sure My Inno Setup Extentions are installed."
            print "  If necessary, specify the location of iscc.exe "
            print "  with command-line option -i."
            sys.exit()
            
#
# Grab stuff from cvs
#

if checkoutnew:
    # Either we check out a copy
    cvsroot = ":pserver:anonymous@cvs.mcs.anl.gov:/cvs/fl"

    # WE ASSUME YOU HAVE ALREADY LOGGED IN WITH:
    # cvs -d :pserver:anonymous@cvs.mcs.anl.gov:/cvs/fl login

    cvs_cmd = "cvs -z6 -d %s export -d %s -D now AccessGrid" % (cvsroot,
                                                                BuildDir)
    print "Checking out code with command: ", cvs_cmd
    os.system(cvs_cmd)

#
# Go to that checkout to build stuff
#


#
# Run precompile scripts
#

for cmd in [
    "BuildAccessGridDist.cmd",
    "BuildVic.cmd",
    "BuildRat.cmd",
    "BuildGlobus.cmd",
    "BuildPythonModules.cmd"
    ]:
    cmd = "%s %s %s %s" % (cmd, SourceDir, BuildDir, DestDir)
    if verbose:
        print "Running: %s" % cmd

    os.system(cmd)

#
# Now we can compile
#

# Add quotes around command.
iscc_cmd = "%s %s /dAppVersion=\"%s\" /dVersionInformation=\"%s\" /dSourceDir=%s" % (inno_compiler, iss_orig, AGTkVersion, metainformation, SourceDir)

if verbose:
    print "Executing:", iscc_cmd

#os.system(iscc_command)

