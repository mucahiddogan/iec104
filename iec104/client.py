# -*- coding: utf-8 -*-
import tornado.ioloop
import tornado.iostream
import socket
import binascii
import acpi
import asdu
import struct
import logging
from bitstring import ConstBitStream
from tornado.gen import Task, engine

import time

import struct

LOG = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)

import functools

class IEC104Client(object):

    def __init__(self):
        pass
        

    def connect(self, ip, port=2404):
        self.ssn = 0
        self.rsn = 0
        #self.stream = tornado.iostream.IOStream(self.socket)
        self.recived = 0
        self.socket = socket.socket()
        self.stream = tornado.iostream.IOStream(self.socket)
        self.stream.connect((ip, port), self.connect_callback)
        
    def close(self):
        self.stream.close()

    @engine
    def receive(self, data):
        self.recived = time.time()
    
        start, length = struct.unpack('2B', data)
        #print "len:", length
        data = yield Task(self.stream.read_bytes, length)
        s_acpi = ''.join(struct.unpack_from('4s', data))  # keep 0x00
        acpi_control = struct.unpack_from('B', data)[0]

        if acpi_control & 1 == 0:  # I-FRAME
            self.ssn, self.rsn = acpi.parse_i_frame(s_acpi)
            LOG.debug("ssn: {}, rsn: {}".format(self.ssn, self.rsn))
            #s_asdu = ConstBitStream(bytes=data, offset=5*8)
            s_asdu = ConstBitStream(bytes=data, offset=4*8)
            o_asdu = asdu.ASDU(s_asdu)
            
            ###
            for o in o_asdu.objs:
                if o is asdu.MMeTf1:
                    print o.val
                if o is asdu.MSpTb1:
                    print o.val
            
            
            #self.rsn = ssn + 1
                
            #LOG.debug("send>>>>>: ssn: {}, rsn: {}".format(self.ssn, self.rsn))
            #yield Task(self.send, struct.pack('<1BHHHHH', 0x10, self.ssn, self.rsn, 0x0, 0x33, 0x16))
            #print 'send>>>>>> ' + str(ssn +1)
            #yield Task(self.sendfixed, acpi.s_frame(ssn +1))
            #print  struct.pack('<3BHHHH', 0x10, 0x01, 0x00, ssn +1, 0x0, 0x33, 0x16)
            #yield Task(self.sendraw, struct.pack('BBBHBB', 0x10, 0x01, 0x0,  0x03, 0x0, 0x16))
            yield Task(self.send, acpi.s_frame2(self.ssn + 1))
            #self.ssn += 1

        elif acpi_control & 3 == 1:  # S-FRAME
            print "S-FRAME"
            self.rsn = acpi.parse_s_frame(s_acpi)
            print self.rsn

        elif acpi_control & 3 == 3:  # U-FRAME
            print "U-FRAME"
            if s_acpi == acpi.STARTDT_CON:
                print 'connected'

            if s_acpi == acpi.TESTFR_ACT:
                print 'ping'
                yield Task(self.send, acpi.TESTFR_CON)
        self.stream.read_bytes(2, self.receive)

    @engine
    def connect_callback(self):
        print "connect"
        LOG.debug("Send STARTDT_ACT")
        #print 'testC'
        #print self.stream.closed()
        try:
        #if not self.stream.closed():
            yield Task(self.send, acpi.STARTDT_ACT)
            self.stream.read_bytes(2, self.receive)
        except Exception as err:
            print err
        #print self.stream.closed()
        
    def send(self, data, callback):
        self.stream.write("\x68" + struct.pack("B", len(data)) + data, callback)
        
    #def sendraw(self, data, callback):
    #    self.stream.write(data, callback)

import datetime
        
def test():
    global iec

    if time.time() - iec.recived > 4:
        LOG.debug("Connection broken?")
        #tornado.ioloop.IOLoop.instance().close()
        #tornado.ioloop.IOLoop.instance().stop()
        iec.close()
        iec.connect(IP)
    else:    

        LOG.debug("Send TESTFR_ACT")
        #print "scheduled event fired"
        Task(iec.send, acpi.TESTFR_ACT)

import signal

def handle_signal(sig, frame):
    tornado.ioloop.IOLoop.instance().add_callback(tornado.ioloop.IOLoop.instance().stop)
 
IP = '10.222.27.27'
IP = '127.0.0.1'

if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    iec = IEC104Client()
    #iec.connect('127.0.0.1')
    iec.connect(IP)
    
    tornado.ioloop.PeriodicCallback(test, 2000).start()
    tornado.ioloop.IOLoop.instance().start()
    
    #iec = IEC104Server()
    #iec.listen(2404)