#-----------------------------------------------------------------------------
# Name:        PyText.py
# Purpose:
#
# Author:      Ivan R. Judson
#
# Created:     2003/01/02
# RCS-ID:      $Id: TextClientUI.py,v 1.4 2003-02-21 16:10:29 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import os
import sys
import pickle
import string

from wxPython.wx import *
from threading import Thread

from pyGlobus.io import GSITCPSocket
from AccessGrid.Utilities import formatExceptionInfo
from AccessGrid.hosting.pyGlobus.Utilities import CreateTCPAttrAlwaysAuth

class TextEvent:
    def __init__(self, venue, recipient, private, data):
        self.venue = venue
        self.sender = None
        self.recipient = recipient
        self.private = private
        self.data = data
        
class SimpleTextProcessor:
    def __init__(self, socket, venueId, textOut):
        """ """
        self.socket = socket
        self.venueId = venueId
        self.textOut = textOut
        self.wfile = self.socket.makefile('wb', 0)
        self.rfile = self.socket.makefile('rb', -1)

        self.outputThread = Thread(target = self.ProcessNetwork)
        self.outputThread.start()

    def Stop(self):
        self.running = 0
        
    def ProcessForSending(self, event):
        """ """
        data = event.GetString()

        textEvent = TextEvent(self.venueId, None, 0, data)

        try:
            pdata = pickle.dumps(textEvent)
            lenStr = "%s\n" % len(pdata)
            self.wfile.write(lenStr)
            self.wfile.write(pdata)
        except:
            (name, args, tb) = formatExceptionInfo()
            print "Error trying to send data"
            print "Name: %s Args: %s" % (name, args)
            print "TB:\n", tb

    def ProcessForDisplay(self, text):
        """ """
        data = text.data

        if text.sender != None:
            name = text.sender
            stuff = name.split('/')
            for s in stuff[1:]:
                (k,v) = s.split('=')
                if k == 'CN':
                    name = v
            string = "%s says, \"%s\"\n" % (name, data)
        else:
            string = "Someone says, \"%s\"\n" % (data)

        self.textOut.AppendText(string)
            

    def ProcessNetwork(self):
        """ """
        self.running = 1
        while self.running:
            str = self.rfile.readline()
            size = int(str)
            pdata = self.rfile.read(size, size)
            event = pickle.loads(pdata)
            self.ProcessForDisplay(event)

class TextClientUI(wxFrame):
    aboutText = """PyText 1.0 -- a simple text client in wxPython and pyGlobus.
        This has been developed as part of the Access Grid project."""
    bufferSize = 128

    def __init__(self, *args, **kwds):
        self.location = kwds["location"]
        del kwds["location"]
        self.host = self.location[0]
        self.port = self.location[1]

        self.venueId = kwds["venueId"]
        del kwds["venueId"]
        
        # begin wxGlade: TextClientUI.__init__
        kwds["style"] = wxDEFAULT_FRAME_STYLE
        wxFrame.__init__(self, *args, **kwds)
        self.TextFrame_statusbar = self.CreateStatusBar(1)

        # Menu Bar
        self.TextFrame_menubar = wxMenuBar()
        self.SetMenuBar(self.TextFrame_menubar)
        self.File = wxMenu()
        self.fileCloseId = wxNewId()
        self.File.Append(self.fileCloseId, "Close", "Quit the application.")
        self.TextFrame_menubar.Append(self.File, "File")
        self.Options = wxMenu()
        self.localEchoId = wxNewId()
        self.Options.Append(self.localEchoId, "Local Echo",
                            "Echo input locally?", wxITEM_CHECK)
        self.TextFrame_menubar.Append(self.Options, "Options")
        self.Help = wxMenu()
        self.helpAboutId = wxNewId()
        self.Help.Append(self.helpAboutId, "About",
                        "Open the about dialog box.")
        self.TextFrame_menubar.Append(self.Help, "Help")
        # Menu Bar end
        self.textOutId = wxNewId()
        self.TextOutput = wxTextCtrl(self, self.textOutId, "", style=wxTE_MULTILINE|wxTE_READONLY|wxHSCROLL)
        self.textInId = wxNewId()
        self.TextInput = wxTextCtrl(self, self.textInId, "", style=wxTE_PROCESS_ENTER|wxHSCROLL)

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

        # We get a host/port tuple from the constructor
        self.attr = CreateTCPAttrAlwaysAuth()
        self.socket = GSITCPSocket()
        self.socket.connect(self.host, self.port, self.attr)
        self.Processor = SimpleTextProcessor(self.socket, self.venueId,
                                             self.TextOutput)

        self.localEcho = 0

        EVT_MENU(self, self.fileCloseId, self.FileClose)
        EVT_MENU(self, self.helpAboutId, self.HelpAbout)
        EVT_MENU(self, self.localEchoId, self.LocalEcho)
        EVT_TEXT_ENTER(self, self.textInId, self.LocalInput)

    def __set_properties(self):
        # begin wxGlade: TextClientUI.__set_properties
        self.SetTitle("PyText 1.0")
        self.SetSize((375, 225))
        self.TextFrame_statusbar.SetStatusWidths([-1])
        # statusbar fields
        TextFrame_statusbar_fields = ['Status Goes Here...']
        for i in range(len(TextFrame_statusbar_fields)):
            self.TextFrame_statusbar.SetStatusText(TextFrame_statusbar_fields[i], i)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: TextClientUI.__do_layout
        TextSizer = wxBoxSizer(wxVERTICAL)
        TextSizer.Add(self.TextOutput, 2, wxEXPAND|wxALIGN_CENTER_HORIZONTAL, 0)
        TextSizer.Add(self.TextInput, 0, wxEXPAND|wxALIGN_BOTTOM, 0)
        self.SetAutoLayout(1)
        self.SetSizer(TextSizer)
        self.Layout()
        # end wxGlade

    def FileClose(self, event):
        self.Processor.Stop()
        self.Close()
#        os._exit(0)

    def HelpAbout(self, event):
        """ About dialog!"""
        dlg = wxMessageDialog(self, self.aboutText, 'About Box...', wxOK)
        dlg.ShowModal()
        dlg.Destroy()

    def LocalEcho(self, event):
        """ """
        self.localEcho = ~self.localEcho

    def LocalInput(self, event):
        """ User input """
        if self.localEcho:
            self.Processor.ProcessForLocalDisplay(event.GetString())
        self.Processor.ProcessForSending(event)
        self.TextInput.Clear()

if __name__ == "__main__":
    pyText = wxPySimpleApp()
    wxInitAllImageHandlers()
    TextFrame = TextClientUI(None, -1, "", host = sys.argv[1],
                                           port = int(sys.argv[2]))
    pyText.SetTopWindow(TextFrame)
    TextFrame.Show(1)
    pyText.MainLoop()
