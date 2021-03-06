#-----------------------------------------------------------------------------
# Name:        VideoServiceH264.py
# Purpose:
# Created:     2003/06/02
# RCS-ID:      $Id$
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import re
import sys, os
import wx
try:
    import win32api
    import _winreg
except: pass

import subprocess
import xml.dom.minidom

from AccessGrid.Descriptions import Capability, ResourceDescription
from AccessGrid.GUID import GUID
from AccessGrid.AGService import AGService
from AccessGrid.AGParameter import ValueParameter, OptionSetParameter, RangeParameter, TextParameter
from AccessGrid.Platform import IsWindows, IsLinux, IsOSX, IsFreeBSD
from AccessGrid.Platform.Config import AGTkConfig, UserConfig, SystemConfig
from AccessGrid.NetworkLocation import MulticastNetworkLocation
from AccessGrid import Toolkit
from AccessGrid.UIUtilities import GetScreenWidth

vicstartup="""option add Vic.disable_autoplace %s startupFile
option add Vic.muteNewSources %s startupFile
option add Vic.maxbw 10240 startupFile
option add Vic.bandwidth %d startupFile
option add Vic.framerate %d startupFile
option add Vic.quality %d startupFile
option add Vic.defaultFormat %s startupFile
option add Vic.inputType %s startupFile
option add Vic.device \"%s\" startupFile
option add Vic.defaultTTL 127 startupFile
option add Vic.rtpName \"%s\" startupFile
option add Vic.rtpEmail \"%s\" startupFile
option add Vic.useDeinterlacerComp %s startupFile
option add Vic.largeSizeResolution \"%s\" startupFile
proc user_hook {} {
    global videoDevice inputPort transmitButton transmitButtonState inputSize

    update_note 0 \"%s\"

    after 200 {
        set transmitOnStartup %s

        if { ![winfo exists .menu] } {
            build.menu
        }

        set inputPort \"%s\"
        grabber port \"%s\"

        set inputSize %d

        if { $transmitOnStartup } {
            if { [$transmitButton cget -state] != \"disabled\" } {
                set transmitButtonState 1
                transmit
            }
        }
    }
}
"""


def OnOff(onOffVal):
    if onOffVal == "On":
        return "true"
    elif onOffVal == "Off":
        return "false"
    raise Exception,"OnOff value neither On nor Off: %s" % onOffVal

class VideoServiceH264( AGService ):

    onOffOptions = [ "On", "Off" ]
    tileOptions = [ '1', '2', '3', '4', '5', '6', '7', '8', '9', '10' ]

    def __init__( self ):
        AGService.__init__( self )
        self.thepath = os.getcwd()

        if IsWindows():
            vic = "vic.exe"
        else:
            vic = "vic"

        self.executable = os.path.join(os.getcwd(),vic)
        if not os.path.isfile(self.executable):
            self.executable = vic

        proc = subprocess.Popen([self.executable, '-Q'],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        self.deviceDOM = xml.dom.minidom.parse(proc.stdout)

        self.encodingOptions = []
        self.capabilities = []
        codecs = self.deviceDOM.getElementsByTagName("codec")
        for codec in codecs:
            if codec.childNodes[0].nodeType == xml.dom.minidom.Node.TEXT_NODE:
                if codec.childNodes[0].data in ['h263', 'h263+', 'raw', 'pvh']:
                    continue
                self.encodingOptions.append(codec.childNodes[0].data)
                self.capabilities.append(Capability( Capability.CONSUMER,
                                          Capability.VIDEO,
                                          codec.childNodes[0].data.upper(),
                                          90000, self.id))

                self.capabilities.append(Capability( Capability.PRODUCER,
                                          Capability.VIDEO,
                                          codec.childNodes[0].data.upper(),
                                          90000, self.id))

        self.sysConf = SystemConfig.instance()

        self.profile = None
        self.windowGeometry = None

        self.startPriority = '7'
        self.startPriorityOption.value = self.startPriority
        self.id = str(GUID())

        self.resolution = None

        # Set configuration parameters
        # note: the datatype of the port, standard and inputsize parameters change when a resource is set!
        self.streamname = TextParameter( "Stream Name", "" )
        self.port = TextParameter( "port", "" )
        self.encoding = OptionSetParameter( "Encoding", "mpeg4", self.encodingOptions )
        self.standard = TextParameter( "standard", "" )
        self.tiles = OptionSetParameter( "Thumbnail Columns", "4", VideoServiceH264.tileOptions )
        self.bandwidth = RangeParameter( "Bandwidth", 2500, 0, 10240 )
        self.framerate = RangeParameter( "Frame Rate", 24, 1, 30 )
        self.quality = RangeParameter( "Quality", 75, 1, 100 )
        self.transmitOnStart = OptionSetParameter( "Transmit on Startup", "On", VideoServiceH264.onOffOptions )
        self.muteSources = OptionSetParameter( "Mute Sources", "Off", VideoServiceH264.onOffOptions )
        self.inputsize = TextParameter( "inputsize", "" )
        self.positionWindow = OptionSetParameter( 'Position Window', 'Justify Left', ['Off', 'Justify Left', 'Justify Right'])
        self.encodingDeinterlacer = OptionSetParameter( "Encoding Deinterlacer", "Off", VideoServiceH264.onOffOptions )

        self.configuration.append( self.streamname )
        self.configuration.append( self.port )
        self.configuration.append( self.encoding )
        self.configuration.append( self.standard )
        self.configuration.append( self.tiles )
        self.configuration.append( self.bandwidth )
        self.configuration.append( self.framerate )
        self.configuration.append( self.quality )
        self.configuration.append( self.transmitOnStart )
        self.configuration.append( self.muteSources )
        self.configuration.append( self.inputsize )

        self.configuration.append( self.positionWindow )
        self.configuration.append( self.encodingDeinterlacer )
        if IsWindows():
            try:
                import win32api

                # get number of processors
                systemInfo = win32api.GetSystemInfo()
                numprocs = systemInfo[5]
                self.allProcsMask = 2**numprocs-1

                self.procOptions = ['All']
                for i in range(numprocs):
                    self.procOptions.append(str(i+1))

                self.processorUsage = OptionSetParameter( "Processor usage", self.procOptions[0], self.procOptions )
                self.configuration.append( self.processorUsage )
            except:
                self.log.exception('Error initializing processor usage options')

        self.__GetResources()
        self.deviceDOM.unlink()

    def __SetRTPDefaults(self, profile):
        """
        Set values used by rat for identification
        """
        if profile == None:
            self.log.exception("Invalid profile (None)")
            raise Exception, "Can't set RTP Defaults without a valid profile."

        if IsLinux() or IsOSX() or IsFreeBSD():
            try:
                rtpDefaultsFile=os.path.join(os.environ["HOME"], ".RTPdefaults")
                rtpDefaultsText="*rtpName: %s\n*rtpEmail: %s\n*rtpLoc: %s\n*rtpPhone: \
                                 %s\n*rtpNote: %s\n"
                rtpDefaultsFH=open( rtpDefaultsFile,"w")
                rtpDefaultsFH.write( rtpDefaultsText % ( profile.name,
                                       profile.email,
                                       profile.location,
                                       profile.phoneNumber,
                                       profile.publicId ) )
                rtpDefaultsFH.close()
            except:
                self.log.exception("Error writing RTP defaults file: %s", rtpDefaultsFile)

        elif IsWindows():
            try:
                #
                # Set RTP defaults according to the profile
                #
                k = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER,
                                    r"Software\Mbone Applications\common")

                # Vic reads these values (with '*')
                _winreg.SetValueEx(k, "*rtpName", 0,
                                   _winreg.REG_SZ, profile.name)
                _winreg.SetValueEx(k, "*rtpEmail", 0,
                                   _winreg.REG_SZ, profile.email)
                _winreg.SetValueEx(k, "*rtpPhone", 0,
                                   _winreg.REG_SZ, profile.phoneNumber)
                _winreg.SetValueEx(k, "*rtpLoc", 0,
                                   _winreg.REG_SZ, profile.location)
                _winreg.SetValueEx(k, "*rtpNote", 0,
                                   _winreg.REG_SZ, str(profile.publicId) )
                _winreg.CloseKey(k)
            except:
                self.log.exception("Error writing RTP defaults to registry")
        else:
            self.log.error("No support for platform: %s", sys.platform)


    def MapWinDevice(self,deviceStr):
        """
        Abuse registry to get correct mapping from vfw names
        to video sources
        """

        videowidth = 352
        videoheight = 288

        self.log.info("Mapping windows device: %s", deviceStr)
        if deviceStr.find('Videum') >= 0:
            self.log.info("- videum")
            devnum = -1
            videum_re = re.compile(".*(\d)_Videum.*")
            m = videum_re.search(deviceStr)
            if m:
                self.log.info("Found match : %d", int(m.group(1)))
                devnum = int(m.group(1))
            else:
                self.log.info("No match")
                if deviceStr.startswith('Videum Video Capture'):
                    self.log.info("is videum video capture")
                    devnum = 0
                else:
                    self.log.info("is not videum video capture")

            self.log.info("Videum device: %d", devnum)
            if devnum >= 0:
                # Set the registry
                keyStr = r"Software\Winnov\Videum\vic.exe%d" % (devnum,)
                key = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER,
                                        keyStr)
                _winreg.SetValueEx(key,'Source',0,_winreg.REG_DWORD,int(devnum))
                _winreg.SetValueEx(key,'Height',0,_winreg.REG_DWORD,int(videoheight))
                _winreg.SetValueEx(key,'Width',0,_winreg.REG_DWORD,int(videowidth))
                _winreg.CloseKey(key)

    def Start( self ):
        """
        Start service
        """
        try:
            # Set processor affinity (windows only)
            if IsWindows():
                try:
                    if self.processorUsage.value == 'All':
                        self.log.info('Setting processor affinity to all processors')
                        SystemConfig.instance().SetProcessorAffinity(self.allProcsMask)
                    else:
                        val = 2**(int(self.processorUsage.value)-1)
                        self.log.info('Ssetting processor affinity : use processor %s', self.processorUsage.value)
                        SystemConfig.instance().SetProcessorAffinity(int(self.processorUsage.value))
                except:
                    self.log.exception("Exception setting processor affinity")

            # Enable firewall
            self.sysConf.AppFirewallConfig(self.executable, 1)

            # Resolve assigned resource to a device understood by vic
            if self.resource == "None":
                vicDevice = "None"
            else:
                vicDevice = self.resource[0]
                vicDevice = vicDevice.replace("[","\[")
                vicDevice = vicDevice.replace("]","\]")

            if IsWindows():
                try:
                    self.MapWinDevice(self.resource[0])
                except:
                    self.log.exception("Exception mapping device")

            #
            # Write vic startup file
            #
            startupfile = os.path.join(UserConfig.instance().GetTempDir(),
               'VideoServiceH264_%s.vic' % self.id )

            f = open(startupfile,"w")
            if self.port.value == '':
                portstr = "None"
            else:
                portstr = self.port.value

            if self.standard.value == '':
                standardstr = "None"
            else:
                standardstr = self.standard.value

            if self.muteSources.value == "On":
                # streams are muted, so disable autoplace
                disableAutoplace = "true"
            else:
                # streams are not muted, so don't disable autoplace
                # (flags should not be negative!)
                disableAutoplace = "false"

            if self.inputsize.value == "Small":
                inputsize = 4
            elif self.inputsize.value == "Large" and self.encoding.value != "h261":
                inputsize = 1
            else:
                inputsize = 2

            if self.resolution != None:
                resolution = self.resolution.value
            else:
                resolution = "none"

            name=email="Participant"
            if self.profile:
                name = self.profile.name
                email = self.profile.email
            else:
                # Error case
                name = email = Toolkit.GetDefaultSubject().GetCN()
                self.log.error("Starting service without profile set")

            f.write( vicstartup % ( disableAutoplace,
                                    OnOff(self.muteSources.value),
                                    self.bandwidth.value,
                                    self.framerate.value,
                                    self.quality.value,
                                    self.encoding.value,
                                    standardstr,
                                    vicDevice,
                                    "%s(%s)" % (name,self.streamname.value),
                                    email,
                                    OnOff(self.encodingDeinterlacer.value),
                                    resolution,
                                    email,
                                    OnOff(self.transmitOnStart.value),
                                    portstr,
                                    portstr,
                                    inputsize) )
            f.close()

            # Open permissions on vic startupfile
            os.chmod(startupfile,0777)

            # Replace double backslashes in the startupfile name with single
            #  forward slashes (vic will crash otherwise)
            if IsWindows():
                startupfile = startupfile.replace("\\","/")

            #
            # Start the service; in this case, store command line args in a list and let
            # the superclass _Start the service
            options = []
            options.append( "-u" )
            options.append( startupfile )
            options.append( "-C" )
            options.append( str(self.streamDescription.name) )
            if IsOSX():
                if self.transmitOnStart.value:
                    options.append( "-X")
                    options.append( "transmitOnStartup=1")
            if self.streamDescription.encryptionFlag != 0:
                options.append( "-K" )
                options.append( self.streamDescription.encryptionKey )

            # Set drop time to something reasonable
            options.append('-XsiteDropTime=5')

            if not self.positionWindow.value == 'Off':
                # - set vic window geometry
                try:

                    if not self.windowGeometry:
                        h = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)
                        w_sys = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
                        try:
                            w = GetScreenWidth(w_sys,h)
                        except ValueError:
                            self.log.debug('Error computing screen width; using system screen width %d', w_sys)
                            w = w_sys
                        window_width = w-300
                        window_height = 300
                        window_x = 300
                        window_y = h-375
                        border_w = wx.SystemSettings_GetMetric(wx.SYS_FRAMESIZE_X)
                        if border_w > 0:
                            window_width -= 4*border_w
                            window_x += 2*border_w
                        self.windowGeometry = (window_width,window_height,window_x,window_y)
                    if self.positionWindow.value == 'Justify Left':
                        options.append('-Xgeometry=%dx%d+%d+%d' % self.windowGeometry)
                    else:
                        options.append('-Xgeometry=%dx%d-%d+%d' % self.windowGeometry)
                except:
                    self.log.exception('Error calculating window placement')


            if self.profile:
                options.append("-X")
                options.append("site=%s" % self.profile.publicId)

            # Set number of columns to use for thumbnail display
            options.append("-Xtile=%s" % self.tiles.value)

            # Check whether the network location has a "type" attribute
            # Note: this condition is only to maintain compatibility between
            # older venue servers creating network locations without this attribute
            # and newer services relying on the attribute; it should be removed
            # when the incompatibility is gone
            if self.streamDescription.location.__dict__.has_key("type"):
                # use TTL from multicast locations only
                if self.streamDescription.location.type == MulticastNetworkLocation.TYPE:
                    options.append( "-t" )
                    options.append( '%d' % (self.streamDescription.location.ttl) )
            options.append( '%s/%d' % ( self.streamDescription.location.host,
                                           self.streamDescription.location.port) )

            self.log.info("Starting VideoServiceH264")
            self.log.info(" executable = %s" % self.executable)
            self.log.info(" options = %s" % options)
            os.chdir(self.thepath)
            self._Start( options )
            #os.remove(startupfile)
        except:
            self.log.exception("Exception in VideoServiceH264.Start")
            raise Exception("Failed to start service")

    def Stop( self ):
        """
        Stop the service
        """

        # vic doesn't die easily (on linux at least), so force it to stop
        AGService.ForceStop(self)

        # Disable firewall
        self.sysConf.AppFirewallConfig(self.executable, 0)

    def SetStream( self, streamDescription ):
        """
        Configure the Service according to the StreamDescription
        """
        self.log.info("SetStream called")

        ret = AGService.ConfigureStream( self, streamDescription )
        if ret and self.started:
            # service is already running with this config; ignore
            return

        # if started, stop
        if self.started:
            self.Stop()

        # if enabled, start
        if self.enabled:
            self.Start()

    def GetResource(self):
        if self.resource:
            return ResourceDescription(self.resource[0])
        else:
            return ResourceDescription('')

    def SetResource( self, resource ):
        """
        Set the resource used by this service
        """

        self.log.info("VideoServiceH264.SetResource : %s" % resource.name )
        for r in self.resources:
            if r[0].strip() == resource.name:
                self.resource = r

        # Find the config element that refers to "port"
        try:
            index = self.configuration.index(self.port)
            found = 1
        except ValueError:
            found = 0

        # Create the port parameter as an option set parameter, now
        # that we have multiple possible values for "port"
        # If self.port is valid, keep it instead of setting the default value.
        if (( isinstance(self.port, TextParameter) or isinstance(self.port, ValueParameter) )
              and self.port.value != "" and self.port.value in self.resource[1]):
            self.port = OptionSetParameter( "Port", self.port.value,
                                                         self.resource[1] )
        else:
            self.port = OptionSetParameter( "Port", self.resource[1][0],
                                                         self.resource[1] )

        self.log.info('port = %s', self.port.value)

        # Replace or append the "port" element
        if found:
            self.configuration[index] = self.port
        else:
            self.configuration.append(self.port)


        # Find the config element that refers to "standard"
        try:
            index = self.configuration.index(self.standard)
            found = 1
        except ValueError:
            found = 0

        # Create the standard parameter as an option set parameter, now
        # that we have multiple possible values for "standard"
        # If self.standard is valid, keep it instead of setting the default value.
        if (( isinstance(self.standard, TextParameter) or isinstance(self.standard, ValueParameter) )
              and self.standard.value != "" and self.standard.value in self.resource[2]):
            self.standard = OptionSetParameter( "Standard", self.standard.value,
                                                         self.resource[2] )
        else:
            if (IsWindows() and "PAL" in self.resource[2]):
                self.standard = OptionSetParameter( "Standard", "PAL", self.resource[2] )
            else :
                self.standard = OptionSetParameter( "Standard", self.resource[2][0],
                                                    self.resource[2] )

        self.log.info('standard = %s', self.standard.value)

        # Replace or append the "standard" element
        if found:
            self.configuration[index] = self.standard
        else:
            self.configuration.append(self.standard)


        # Find the config element that refers to "inputsize"
        try:
            index = self.configuration.index(self.inputsize)
            found = 1
        except ValueError:
            found = 0

        # Create the inputsize parameter as an option set parameter, now
        # that we have multiple possible values for "inputsize"
        # If self.inputsize is valid, keep it instead of setting the default value.
        if (( isinstance(self.inputsize, TextParameter) or isinstance(self.inputsize, ValueParameter) )
              and self.inputsize.value != "" and self.inputsize.value in self.resource[3]):
            self.inputsize = OptionSetParameter( "Capture Size", self.inputsize.value,
                                                 self.resource[3] )
        else:
            if ("Medium" in self.resource[3]):
                self.inputsize = OptionSetParameter( "Capture Size", "Medium",
                                                     self.resource[3] )
            else:
                self.inputsize = OptionSetParameter( "Capture Size", self.resource[3][0],
                                                     self.resource[3] )

        self.log.info('inputsize = %s', self.inputsize.value)

        # Replace or append the "inputsize" element
        if found:
            self.configuration[index] = self.inputsize
        else:
            self.configuration.append(self.inputsize)

        if len(self.resource[4]) > 0:
            # Find the config element that refers to "resolution"
            try:
                index = self.configuration.index(self.resolution)
                found = 1
            except ValueError:
                found = 0
            except AttributeError:
                found = 0

            # Create the resolution parameter as an option set parameter, now
            # that we have multiple possible values for "resolution"
            # If self.resolution is valid, keep it instead of setting the default value.
            if (( isinstance(self.resolution, TextParameter) or isinstance(self.resolution, ValueParameter) )
                and self.resolution.value != "" and self.resolution.value in self.resource[4]):
                self.resolution = OptionSetParameter( "Large Size/Scaler Resolution", self.resolution.value,
                                                  self.resource[4] )
            else:
                self.resolution = OptionSetParameter( "Large Size/Scaler Resolution", self.resource[4][0],
                                                  self.resource[4] )

            self.log.info('resolution = %s', self.resolution.value)

            # Replace or append the "resolution" element
            if found:
                self.configuration[index] = self.resolution
            else:
                self.configuration.append(self.resolution)

        # If the stream name has not been set, set it to the resource name
        if not self.streamname.value:
            self.streamname.value = resource.name

    def SetIdentity(self, profile):
        """
        Set the identity of the user driving the node
        """
        if profile:
            self.log.info("SetIdentity: %s %s", profile.name, profile.email)
        self.profile = profile
        self.__SetRTPDefaults(profile)

    def GetResources(self):
        ret = map(lambda x: ResourceDescription(x[0]) , self.resources)
        self.log.info('resources: %s', ret)
        return ret

    def __GetResources(self):
        self.resources = list()
        devices = self.deviceDOM.getElementsByTagName("device")
        for device in devices:
            nickname = device.getElementsByTagName("nickname")[0]
            if nickname.childNodes[0].nodeType != xml.dom.minidom.Node.TEXT_NODE:
                continue
            deviceName = nickname.childNodes[0].data
            if (deviceName.startswith("V4L2-")):
                deviceName = "V4L2:/dev/video" + deviceName.split("/dev/video", 1)[1]
            elif (deviceName.startswith("V4L-")):
                deviceName = "V4L:/dev/video" + deviceName.split("/dev/video", 1)[1]
            portList = [] # device's input ports
            ports = device.getElementsByTagName("port")
            for port in ports:
                if port.childNodes[0].nodeType == xml.dom.minidom.Node.TEXT_NODE:
                    portList.append(port.childNodes[0].data)
            if len(portList) == 0:
                portList=[ deviceName ]
            typeList = [] # video standards supported by device,  e.g. NTSC, PAL, 720p25, etc
            types = device.getElementsByTagName("type")
            for type in types:
                if type.childNodes[0].nodeType == xml.dom.minidom.Node.TEXT_NODE:
                    if (type.childNodes[0].data in ['pal', 'ntsc', 'secam']):
                        typeList.append(type.childNodes[0].data.upper())
                    else :
                        typeList.append(type.childNodes[0].data)
            if len(typeList) == 0:
                typeList=[ "NTSC", "PAL" ]
            sizeList = [] # video capture sizes supported by device
            sizes = device.getElementsByTagName("size")
            for size in sizes:
                if size.childNodes[0].nodeType == xml.dom.minidom.Node.TEXT_NODE:
                    if (size.childNodes[0].data in ['cif', 'normal']):
                        sizeList.append("Medium")
                    else:
                        sizeList.append(size.childNodes[0].data.capitalize())
            resolutionList = [] # resolutions supported by device
            resolutions = device.getElementsByTagName("large_size_resolution")
            for res in resolutions:
                if res.childNodes[0].nodeType == xml.dom.minidom.Node.TEXT_NODE:
                    resolutionList.append(res.childNodes[0].data.capitalize())

            typeList.sort()
            sizeList.sort()
            self.resources.append([deviceName, portList, typeList, sizeList, resolutionList])

        return self.resources

if __name__ == '__main__':

    from AccessGrid.interfaces.AGService_interface import AGService as AGServiceI
    from AccessGrid.AGService import RunService

    service = VideoServiceH264()
    serviceI = AGServiceI(service)
    RunService(service,serviceI)
