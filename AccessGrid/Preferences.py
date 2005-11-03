import cPickle
import os
import copy

from AccessGrid.Platform.Config import UserConfig, AGTkConfig
from AccessGrid import Log
from AccessGrid.Platform import IsWindows, IsOSX
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid.Utilities import LoadConfig, SaveConfig

log = Log.GetLogger(Log.VenueClient)

class Preferences:
    '''
    Class including accessors to user preferences.
    '''
    RECONNECT = "reconnect"
    MAX_RECONNECT = "maxReconnect"
    RECONNECT_TIMEOUT = "reconnectTimeout"
    SECURE_VENUE_CONNECTION = "secureVenueConnection"
    SECURE_CLIENT_CONNECTION = "secureClientConnection"
    CLIENT_PORT = "clientPort"
    STARTUP_MEDIA = "startupMedia"
    NODE_URL = "defaultNodeServiceUrl"
    NODE_CONFIG = "defaultNodeConfig"
    NODE_CONFIG_TYPE = "user"
    MULTICAST = "multicast"
    BEACON = "beacon"
    LOG_TO_CMD = "logToCmd"
    ENABLE_DISPLAY = "enableDisplay"
    ENABLE_VIDEO = "enableVideo"
    ENABLE_AUDIO = "enableAudio"
    DISPLAY_MODE = "displayMode"
    EXITS = "exits"
    MY_VENUES = "my venues"
    ALL_VENUES = "all venues"
                
    def __init__(self):
        '''
        Initiate preferences class. Simple client configuration
        parameters are saved in preferences dictionary. More
        complicated data structures are added as separate class
        objects and are saved to separate config file, for example
        client profile.
        '''

        self.preferences = {}
        
        # Default preferences
        self.default = { self.RECONNECT : 1,
                         self.MAX_RECONNECT : 3,
                         self.RECONNECT_TIMEOUT : 10,
                         self.SECURE_VENUE_CONNECTION: 0,
                         self.SECURE_CLIENT_CONNECTION: 0,
                         self.CLIENT_PORT: 0,
                         self.STARTUP_MEDIA: 1,
                         self.NODE_URL: "http://localhost:11000/NodeService",
                         self.NODE_CONFIG_TYPE : "",
                         self.NODE_CONFIG: "",
                         self.MULTICAST: 1,
                         self.BEACON: 1,
                         self.LOG_TO_CMD: 0,
                         self.ENABLE_DISPLAY: 1,
                         self.ENABLE_VIDEO: 1,
                         self.ENABLE_AUDIO: 1,
                         self.DISPLAY_MODE: self.EXITS
                         }

        # Set default log levels to Log.DEBUG.
        # Keys used for log preferences
        # are the same as listed in Log.py.
        # Save log levels as
        # Log.VenueClient=Log.DEBUG.
        categories = Log.GetCategories()
        for category in categories:
            self.default[category] = Log.DEBUG

        # Use the already implemented parts of
        # client profile. Save client profile
        # to separate profile file.
        self.profile = ClientProfile()

        # Use already implemented parts of
        # node service. Default node service
        # config will get saved using the node
        # service.
        self.nodeConfigs = []
        self.config = UserConfig.instance(initIfNeeded=0)

        self.LoadPreferences()
     
    def GetPreference(self, preference):
        '''
        Accessor for client preferences. If the preference
        is not set, the method returns default value.
        
        ** Arguments **

        *preference* Preference you want to know value of

        ** Returns **

        *value* Value for preference
        '''
        r = None
        if self.preferences.has_key(preference):
            r = self.preferences[preference]
            
        elif self.default.has_key(preference):
            r = self.default[preference]
        else:
            return Exception, "Preferences.GetPreference: %s does not exist in preferences" %preference
        return r
                
    def SetPreference(self, preference, value):
        '''
        Set value for preference.
        
        ** Arguments **

        *preference* Preference to set

        *value* Value for preference
        '''
        self.preferences[preference] = value
        
    def StorePreferences(self):
        '''
        Save preferences to config file using INI file format.
        Client profile is saved separately.
        '''
        tempDict = {}

        # Add category to preference
        for key in self.preferences.keys():
            tempDict["Preferences."+key] = self.preferences[key]

        # Save preference
        try:
            log.debug("Preferences.StorePreferences: open file")
            SaveConfig(self.config.GetPreferences(), tempDict)
        
        except:
            log.exception("Preferences.StorePreferences: store file error")

        # Save client profile in separate file.
        try:
            profileFile = os.path.join(self.config.GetConfigDir(),
                                       "profile" )
            self.profile.Save(profileFile)
        except:
            log.exception("Preferences.StorePreferences: store profile file error")
            
    def LoadPreferences(self):
        '''
        Read preferences from configuration file.
        '''
        try:
            log.debug("Preferences.LoadPreferences: open file")
            preferences = LoadConfig(self.config.GetPreferences())

            # Remove category from preference
            for p in preferences.keys():
                pref = p.split(".")[1]
                self.preferences[pref] = preferences[p]
        except:
            log.exception("Preferences.LoadPreferences: open file error")
            self.preferences = {}
                
        # Load client profile separately
        try:
            profileFile = os.path.join(self.config.GetConfigDir(),
                                       "profile" )
            self.profile = ClientProfile(profileFile)
                   
        except IOError:
            log.exception("Preferences.LoadPreferences: open file io error")

    def ResetPreferences(self):
        '''
        Reset all preferences to default values. The preferences will
        also get stored in configuration file.
        '''
        for key in self.default.GetKeys():
            self.preferences[key] = self.default[key]

        self.StorePreferences()

    def GetDefaultNodeConfig(self):
        configs = self.GetNodeConfigs()
        defaultName = self.GetPreference(self.NODE_CONFIG)
        defaultType = self.GetPreference(self.NODE_CONFIG_TYPE)
        
        for c in configs:
            if c.name == defaultName and c.type == defaultType:
                return c
            
        return None
        
                        
    def GetNodeConfigs(self):
        '''
        Get all available node configuration from a node service.

        ** Returns **
        *configs* list of node configurations [string]
        '''
        from AccessGrid.interfaces.AGNodeService_client import AGNodeServiceIW

        # Retreive from node service; not stored in preferences.
        configs = []
        try:
            nservice = AGNodeServiceIW(self.GetPreference(self.NODE_URL))
            configs = nservice.GetConfigurations() 
        except:
            log.exception("Preferences:SetDefaultNodeConfig: Failed to set default node service configuration.")
                               
        return configs

    def SetProfile(self, profile):
        '''
        Set client profile describing your personal information.

        ** Arguments **
        
        * profile * ClientProfile with your information.
        '''
        # To avoid storing redundant information, save
        # client preferences in profile file.
        if type(profile) != ClientProfile:
            return Exception, "Invalid Type: SetProfile takes a ClientProfile as argument"
        self.profile = profile
        
    def GetProfile(self):
        '''
        Get client profile describing your personal information.

        **Returns**

        * clientProfile * ClientProfile with your information. 
        '''
        return self.profile
    

