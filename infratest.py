#!/usr/bin/python
# -*- coding: utf-8 -*-


import unittest
import logging
import os
import sys

import paramiko
 
import conf

from optparse import OptionParser


_VERSION_ = '0.0.1'

#
# log setup
#

if os.path.exists('infratest.log'):  # FIXME: proper log config
    os.remove('infratest.log')

logging.basicConfig(format='%(levelname)s\t%(funcName)s\t%(lineno)d\t%(message)s', level=logging.DEBUG, filename='infratest.log')
log = logging.getLogger("infratest")

console = logging.StreamHandler()
console.setLevel(logging.INFO)

log.addHandler(console) 

from notifier import Notifier

#
# mock setup
#

if sys.version_info[0] == 3:
    
    from unittest.mock import MagicMock
    
else:
    
    from mock import MagicMock


#
# main module functional
#

class myNotifier:
    
    def sendMessage(self, subj, text):

        Notifier().NotifyRaw(subj, text)


class customCheck:
    
    _notifier = None
    _config = {}
    
    def __init__(self, config):
        self._config = config
        
    def setNotifier(self, notifierClass):
        
        self._notifier = notifierClass
        
    
        
    def doAll(self, id=None):
        
        textToSend = ''
        

        for item in self._config:
            
            ty = item.get('type', False)
            if ty:
                
                chk = item.get('check')
                
                host = item.get('host') 
                
                log.info('processing %s/%s', host, ty)
                
                client = paramiko.SSHClient()
                client.load_system_host_keys()
		log.info("connecting %s:%s" % (host, item.get('login')))
                client.connect(host, username=item.get('login'))
                
                for i in chk: 
                    
                    if id != i.get('id'):
                        log.debug('id mismatch %s != %s', id, i.get('id'))
                        continue
                                    
                    
                    log.info("executing: %s", i['do'])       
                                        
                    stdin, stdout, stderr = client.exec_command(i['do'])
                    out = stdout.read()

                    log.debug(out)
                    
                    textIn = i.get('checkTextIn', None)
                    
                    if textIn:
                    
                        cmp = textIn
                        
                        if type(cmp) == str:
                            
                            if not cmp in out:
                                
                                textToSend += "%s error:\nThere is no pattern: %s\n in result data:\n'%s'" % \
                                    (host, cmp, out)
                                
                                log.error(textToSend)
                                                             
                            else:
                                
                                log.debug('%s checked ok', cmp)
                                
                        elif type(cmp) == list:
                            
                            for c in cmp:
                                
                                if not c in out:
                                
                                    textToSend += "%s error:\nThere is no pattern: %s\n in result data:\n'%s'" % \
                                        (host, c, out)
                                        
                                    log.error(textToSend)
                                   
                                else:
                                    
                                    log.debug('%s checked ok', c)
                    
                    textOut = i.get('checkTextOut', None)
                    
                    if textOut:
                         
                        cmp = textOut
                        
                        if type(cmp) == str:
                            
                            if cmp in out:
                                
                                textToSend += "%s error:\nThere is pattern: %s\n in result data:\n'%s'" % \
                                    (host, cmp, out)
                                
                                log.error(textToSend)
                                                             
                            else:
                                
                                log.debug('%s checked ok', cmp)
                                
                        elif type(cmp) == list:
                            
                            for c in cmp:
                                
                                if c in out:
                                
                                    textToSend += "%s error:\nThere is pattern: %s\n in result data:\n'%s'" % \
                                        (host, c, out)
                                        
                                    log.error(textToSend)
                                   
                                else:
                                    
                                    log.debug('%s checked ok', c)      
                    
        if textToSend:
            self._notifier().sendMessage("infratest error", textToSend)   

class testSimple(unittest.TestCase):
    
    def runTest(self):

        checkCase = conf.INFRA_TEST

        cc = customCheck(config=checkCase)
        cc.setNotifier(myNotifier)
        
        cc.doAll()
       
        
       


#
# main entry
#

if __name__ == "__main__":

    parser = OptionParser(usage="usage: %prog [options]", version="%prog " + _VERSION_)
    
    parser.add_option("-v", "--verbose",
                  action="store_true", dest="verbose", default=False,
                  help="Show debug messages")
   
    parser.add_option("-i", "--id",
                  action="store", dest="id", default=None,
                  help="Run only tests with current id")
    
    (options, args) = parser.parse_args()

    if options.verbose:
        console.setLevel(logging.DEBUG) 
    
    if options.id:
        log.info("Running only %s tests...", options.id)
    else:
        log.info("Running default tests")
    
    cc = customCheck(config=conf.INFRA_TEST)
    cc.setNotifier(myNotifier)
    
    cc.doAll(id=options.id)
   
 
