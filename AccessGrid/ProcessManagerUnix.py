#-----------------------------------------------------------------------------
# Name:        ProcessManagerUnix.py
# Purpose:     
#
# Author:      Robert D. Olson
#
# Created:     2003/08/02
# RCS-ID:      $Id: ProcessManagerUnix.py,v 1.7 2003-05-19 22:44:19 eolson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
import signal
import string
import os
import time

class ProcessManagerUnix:

    def __init__(self):
        self.processes = []

    def start_process(self, command, arglist):
        """
        Start a new process.
        Command is the name of the command to be started. It can either be a full pathname
        or a command name to be found on the default path.
        Arglist is a list of the arguments to the command.
         """

        arglist.insert(0, command)

        arglist = map(lambda a: str(a), arglist)
        pid = os.spawnvp(os.P_NOWAIT, command, arglist)

        self.processes.append(pid)

        return pid

    def terminate_all_processes(self):
        for pid in self.processes:
            try:
                self._terminate_process(pid)   
            except OSError, e:
                print "couldn't terminate process: ", e

        self.processes = []

    def terminate_process(self, pid):
        try:
            self._terminate_process(pid)    
            self.processes.remove(pid)
        except OSError, e:
            print "couldn't terminate process: ", e
    
    def _terminate_process(self, pid):
        os.kill(pid, signal.SIGINT)
        elapsedWaits = 0
        maxWaits = 5
        waitTime = 1
        retpid = 0
        try:
            while elapsedWaits < maxWaits:
                (retpid,status) = os.waitpid(pid, os.WNOHANG )
                #print "waitpid returns ", retpid, status
                if retpid == pid and os.WIFEXITED(status):
                    break
                time.sleep(waitTime)
                elapsedWaits += 1
        except OSError, e:
                print "_terminate_process(",pid,"):", e

        if retpid == pid:
            if os.WIFEXITED(status):
                rc = os.WEXITSTATUS(status)
            elif os.WIFSIGNALED(status):
                sig = os.WTERMSIG(status)
        else:
            self._kill_process(pid)

    def kill_all_processes(self):
        for pid in self.processes:
            try:
                self._kill_process(pid)   
            except OSError, e:
                print "couldn't kill process: ", e

        self.processes = []

    def _kill_process(self, pid):
       os.kill(pid,signal.SIGKILL)
       maxWaits = 5
       waitTime = 1
       elapsedWaits = 0
       retpid = 0
       try:
           while elapsedWaits < maxWaits:
               (retpid,status) = os.waitpid(pid, os.WNOHANG )
               if retpid == pid and os.WIFSIGNALED(status):
                   break
               time.sleep(waitTime)
               elapsedWaits += 1
       except OSError, e:
           print "_kill_process, waitpid",pid,":", e
       if retpid == pid:
           if os.WIFEXITED(status):
               rc = os.WEXITSTATUS(status)
           elif os.WIFSIGNALED(status):
               sig = os.WTERMSIG(status)
       else:
           print "_kill_process, process",pid ,"not killed or waitpid() failed."


if __name__ == "__main__":

    import time

    mgr = ProcessManagerUnix()
    mgr.start_process("date",[])

    time.sleep(3)

    mgr.terminate_all_processes()

    
