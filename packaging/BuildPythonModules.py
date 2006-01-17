#!/usr/bin/python

import sys
import os

#
#  Build all the python modules and stick them somewhere safe
#

#
# Store command-line args
#
SOURCE=sys.argv[1]
AGDIR=sys.argv[2]
DEST=sys.argv[3]

# Don't pass this in anymore
PYVER=sys.version[:3]

#
# Setup the given module in the given dest directory
#
def SetupModule(modName, source, dest):
    os.chdir(os.path.join(source,modName))
    os.spawnl(os.P_WAIT,sys.executable,sys.executable,"setup.py","clean","--all")
    os.spawnl(os.P_WAIT,sys.executable,sys.executable,"setup.py","build")
    os.spawnl(os.P_WAIT,sys.executable,sys.executable,"setup.py","install",
              "--prefix=%s"%(dest,), "--no-compile")


#
# Modify the python path to pick up packages as they're built,
# so inter-package dependencies are satisfied
#
BuildPath=SOURCE + os.pathsep + os.path.join(DEST,"lib","python"+PYVER,"site-packages")
if os.environ.has_key("PYTHONPATH"):
   os.environ["PYTHONPATH"] = os.environ["PYTHONPATH"] + os.pathsep + BuildPath
else:
   os.environ["PYTHONPATH"] = BuildPath


#
# Build python modules
#

print "Python: ", PYVER

print "*********** Building pyOpenSSL_AG\n"
if sys.platform == 'win32':
   # Find better solution later...
    os.chdir(os.path.join(SOURCE,"pyOpenSSL"))
    os.spawnl(os.P_WAIT,sys.executable,sys.executable,"setup.py","clean","--all")
    sslp = os.path.join(SOURCE, "openssl-0.9.7g")
    os.spawnl(os.P_WAIT,sys.executable,sys.executable,"setup.py","build_ext","-I%s"%(os.path.join(sslp,"inc32")),"-L%s"%(os.path.join(sslp, "out32dll")))
    os.spawnl(os.P_WAIT,sys.executable,sys.executable,"setup.py","build")
    os.spawnl(os.P_WAIT,sys.executable,sys.executable,"setup.py","install",
              "--prefix=%s"%(DEST,), "--no-compile")
else:
    SetupModule("pyOpenSSL", SOURCE, DEST)

print "*********** Building bajjer\n"
SetupModule("bajjer-0.2.3", SOURCE, DEST)

print "*********** Building feedparser\n"
SetupModule("feedparser", SOURCE, DEST)

print "*********** Building pyxml\n"
SetupModule("PyXML-0.8.4", SOURCE, DEST)

print "*********** Building ZopeInterface\n"
SetupModule("ZopeInterface-3.0.1", SOURCE, DEST)

print "*********** Building zsi\n"
SetupModule("zsi", SOURCE, DEST)

print "*********** Building m2crypto\n"
SetupModule("m2crypto-0.15", SOURCE, DEST)

print "*********** Building twisted\n"
SetupModule("Twisted-2.1.0", SOURCE, DEST)

print "*********** Building bonjour-py\n"
SetupModule("bonjour-py-0.1", SOURCE, DEST)

print "*********** Building common\n"
SetupModule(os.path.join("common","examples", "_common"), SOURCE, DEST)

