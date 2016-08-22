# -*- coding: utf-8 -*-
import tornado.ioloop
import tornado.tcpserver

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

def handle_connection(connection, address):
    LOG.debug("Handle connection")
    LOG.debug(connection)
    LOG.debug(address)

def connection_ready(sock, fd, events):
    LOG.debug("Connection ready")
    while True:
        try:
            connection, address = sock.accept()
        except socket.error as e:
            if e.args[0] not in (errno.EWOULDBLOCK, errno.EAGAIN):
                raise
            return
        connection.setblocking(0)
        handle_connection(connection, address)
 
''' 
class IEC104ServerX(object):
    def __init__(self):
        pass
    
    def listen(self, port = 2404):
        self.ssn = 0
        self.rsn = 0
        self.recived = 0
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(0)
        sock.bind(("", port))
        sock.listen(128)

        io_loop = tornado.ioloop.IOLoop.current()
        callback = functools.partial(connection_ready, sock)
        io_loop.add_handler(sock.fileno(), callback, io_loop.READ)
        io_loop.start()
'''

class C1(tornado.tcpserver.TCPServer):
    def __init__(self):
        super(C1, self).__init__()
        self.ssn = 0
        self.rsn = 0
        self.recived = 0
   
    @engine
    def receive(self, data):
        #yield Task(self.send, acpi.s_frame2(self.ssn + 1))
        
        self.recived = time.time()
        start, length = struct.unpack('2B', data)
        #print self.port, " len:", length
        data = yield Task(self.stream.read_bytes, length)
        s_acpi = ''.join(struct.unpack_from('4s', data))  # keep 0x00
        acpi_control = struct.unpack_from('B', data)[0]

        if acpi_control & 1 == 0:  # I-FRAME
            self.ssn, self.rsn = acpi.parse_i_frame(s_acpi)
            LOG.debug("ssn: {}, rsn: {}".format(self.ssn, self.rsn))
            s_asdu = ConstBitStream(bytes=data, offset=4*8)
            o_asdu = asdu.ASDU(s_asdu)
            #LOG.debug(">>>>>>>>>>>>>>>>>.Send S-FRAME ssn: {}".format(self.ssn + 1))
            yield Task(self.send, acpi.s_frame2(self.ssn + 1))
            

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
                
        #yield Task(self.send, acpi.s_frame2(self.ssn + 1))
        self.stream.read_bytes(2, self.receive)
 
    @engine
    def connect_callback(self):
        print self.port, "connect"
        LOG.debug("Send STARTDT_ACT")
        try:
        #if not self.stream.closed():
            #yield Task(self.send, acpi.STARTDT_ACT)
            yield Task(self.send, acpi.STARTDT_CON)
            self.stream.read_bytes(2, self.receive)
        except Exception as err:
            print err

    def send(self, data, callback):
        self.stream.write("\x68" + struct.pack("B", len(data)) + data, callback)
        
class IEC104Server(tornado.tcpserver.TCPServer):

    connections = []
    
    @engine
    def handle_stream(self, stream, address):
        LOG.debug("Handle stream")
        LOG.debug(address)
        LOG.debug(address[1])
        
        c = C1()
        c.address = address[0]
        c.port = address[1]
        c.stream = stream
        c.connect_callback()
        self.connections.append(c)
        
import signal

def handle_signal(sig, frame):
    tornado.ioloop.IOLoop.instance().add_callback(tornado.ioloop.IOLoop.instance().stop)
'''    
def test():
    print 'periodical----------------------------'

    global server


    
    for c in server.connections:
        
        if time.time() - c.recived > 4:
            LOG.debug("No connection to %s:%s?", c.address, c.port)
            server.connections.remove(c)
            #tornado.ioloop.IOLoop.instance().close()
            #tornado.ioloop.IOLoop.instance().stop()
            #iec.close()
            #iec.connect('127.0.0.1')
        else:    
            yield Task(c.send, acpi.s_frame2(c.ssn + 1))
            #LOG.debug("Send I-FRAME")
            #Task(c.send, acpi.i_frame2(c.rsn, c.ssn) + '\x24\x01\x03\x00\x14\x29\xcb\xb2\x02\xcd\xcc\x2c\x3e\x00\x94\xdc\x02\x8a\x23\x0a\x0b')
            ##Task(c.send, acpi.TESTFR_ACT)
            pass
            
            
            #print "scheduled event fired"
            #Task(c.send, acpi.TESTFR_ACT)
        
            #Task(server.send, server.id, '\x43\x00\x00\x00')
            #c.rsn , c.ssn
            #print binascii.hexlify(acpi.i_frame2(16150, 23713) + '\x24\x01\x03\x00\x14\x29\xcb\xb2\x02\xcd\xcc\x2c\x3e\x00\x94\xdc\x02\x8a\x23\x0a\x0b')
            
            #IEC 60870-5-104-Asdu: ASDU=10516 M_ME_TF_1 Spont IOA=176843 'measured value, short floating point number with time tag CP56Time2a' Value: 0.16875
            #https://www.cloudshark.org/captures/a4ea80e9b1f8
            #no. 7
'''

from tornado import gen
@gen.coroutine
def minute_loop():
    global server
 
    #sp = asdu.cSIQ()
    sp = asdu.cMSpTb1()
    sp.casdu1 = 45
    sp.casdu2 = 50
    sp.ioa1 = 36
    sp.ioa2 = 68
    sp.ioa3 = 0
    sp.iv = False
    sp.nt = False
    sp.sb = False
    sp.bl = False
    sp.spi = True
    sp.CP56Time2a.year = 16
    sp.CP56Time2a.month = 8
    sp.CP56Time2a.dom = 4
    sp.CP56Time2a.hour = 3
    sp.CP56Time2a.minute = 10
    sp.CP56Time2a.minute = 1234
    
    f = asdu.cMMeTf1()
    f.casdu1 = 45
    f.casdu2 = 50
    f.ioa1 = 36
    f.ioa2 = 68
    f.ioa3 = 0
    
    
    while True:
        sp.spi = not sp.spi
        f.value = f.value + 1
        
    
        #nxt = gen.sleep(10)   # Start the clock.
        #yield test()  # Run while the clock is ticking.
        #yield nxt             # Wait for the timer to run out.
        #yield test()
        #print 'y'
        #yield test()

        nxt = gen.sleep(5)
        for c in server.connections:
            if time.time() - c.recived > 10:
                LOG.debug("No connection to %s:%s?", c.address, c.port)
                server.connections.remove(c)
                #tornado.ioloop.IOLoop.instance().close()
                #tornado.ioloop.IOLoop.instance().stop()
                #iec.close()
                #iec.connect('127.0.0.1')
            else:    
                #LOG.debug("Send S-FRAME ssn: {}".format(c.ssn + 1))
                #yield Task(c.send, acpi.s_frame2(c.ssn + 1))
                #LOG.debug("Send I-FRAME")
                #Task(c.send, acpi.i_frame2(c.rsn, c.ssn) + '\x24\x01\x03\x00\x14\x29\xcb\xb2\x02\xcd\xcc\x2c\x3e\x00\x94\xdc\x02\x8a\x23\x0a\x0b')
                LOG.debug("Send TESTFR_ACT")
                Task(c.send, acpi.TESTFR_ACT)
                
                #DATA
                #sp = asdu.cSIQ()
                #sp_bytes = sp.getBytes()
                Task(c.send, acpi.i_frame2(c.rsn, c.ssn + 1) + sp.bytes())
                c.rsn += 1
                Task(c.send, acpi.i_frame2(c.rsn, c.ssn + 1) + f.bytes())
                c.rsn += 1
                
                #print ">>>>>>"
                #print "hex: ", binascii.hexlify(sp_bytes)
                
                LOG.debug("Send I-FRAME ssn: {}, rsn: {}".format(c.rsn, c.ssn + 1))
                Task(c.send, acpi.i_frame2(c.rsn, c.ssn + 1) + '\x24\x01\x03\x00\x14\x29\xcb\xb2\x02\xcd\xcc\x2c\x3e\x00\x94\xdc\x02\x8a\x23\x0a\x0b')
                c.rsn += 1

        yield nxt
        #yield gen.sleep(2)
 
if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    #tornado.ioloop.PeriodicCallback(test, 2000).start()
    
    # Coroutines that loop forever are generally started with
    # spawn_callback().
    tornado.ioloop.IOLoop.current().spawn_callback(minute_loop)
    
    server = IEC104Server()
    server.listen(2404)
    
    #tornado.ioloop.PeriodicCallback(test, 2000).start()
    tornado.ioloop.IOLoop.instance().start()
    tornado.ioloop.IOLoop.instance().close()

    
    
    
    
    #tornado.ioloop.PeriodicCallback(test, 2000).start()
    #tornado.ioloop.IOLoop.instance().start()
    
    #server = EchoServer()
    #server.bind(2404)
    #server.start(0)  # Forks multiple sub-processes
    #tornado.ioloop.IOLoop.current().start()
    
    #iec = IEC104Server()
    #iec.listen(2404)