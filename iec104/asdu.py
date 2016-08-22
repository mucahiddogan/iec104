# -*- coding: utf-8 -*-
import logging
import binascii

import struct

LOG = logging.getLogger()

def casdu2(asdu):
    return asdu & 0xFF
    
def casdu1(asdu):
    return (asdu >> 8) & 0xFF

def ioa3(ioa):
    return ioa & 0xFF
    
def ioa2(ioa):
    return (ioa >> 8) & 0xFF    

def ioa1(ioa):
    return (ioa >> 16) & 0xFF
    
class cASDU():
    type_id = 30
    sq = 0
    sq_count = 1
    cot = 3
    orig = 0
    
    casdu1 = 0
    casdu2 = 0
    
    #asdu = casdu1 << 7 + casdu2 #10255
    
    def bytes(self):
        return struct.pack('BBBBBB', self.type_id, self.sq_count, self.cot, self.orig, self.casdu1, self.casdu2)
        
    def bytes2(self):
        #return struct.pack('BBBBH', self.type_id, self.sq_count, self.cot, self.orig, self.asdu)
        return struct.pack('BBBBBB', self.type_id, self.sq_count, self.cot, self.orig, self.casdu1, self.casdu2)
        
        
class cInfoObj(cASDU):
    
    ioa1 = 0
    ioa2 = 0
    ioa3 = 0
    
    #ioa = ioa1 << 16 + ioa2 << 8 + ioa3 #9
 
    def bytes(self):
        return cASDU.bytes(self) + struct.pack('BBB', self.ioa1, self.ioa2, self.ioa3)
    
    def bytes2(self):
        #return self.getBytes2() + struct.pack('BBB', ioa1(self.ioa), ioa2(self.ioa), ioa3(self.ioa))
        #return self.getBytes2() + struct.pack('BBB', self.ioa1, self.ioa2, self.ioa3)
        return cASDU.bytes2(self) + struct.pack('BBB', self.ioa1, self.ioa2, self.ioa3)
 
class cSIQ(cInfoObj):

    iv = False
    nt = False
    sb = False
    bl = False
    #res 3 bits
    spi = False
    
    def bytes(self):
        #print '>>> {}'.format(int(self.spi) & 0x1)
        #print '>>> {}'.format(int(struct.pack('B', (int(self.iv) & 0x1) << 7 | (int(self.nt) & 0x1) << 6 | (int(self.sb) & 0x1) << 5 | (int(self.bl) & 0x1) << 4 | (int(self.spi) & 0x1))))
        return cInfoObj.bytes(self) + struct.pack('B', int((self.iv & 0x1) << 7 | (self.nt & 0x1) << 6 | (self.sb & 0x1) << 5 | (self.bl & 0x1) << 4 | (self.spi & 0x1)))
        #return cInfoObj.bytes(self) + struct.pack('B', int((int(self.iv) & 0x1) << 7 | (int(self.nt) & 0x1) << 6 | (int(self.sb) & 0x1) << 5 | (int(self.bl) & 0x1) << 4 | (int(self.spi) & 0x1)))
    
    def bytes2(self):
        #return self.getBytes1() + struct.pack('B', self.spi) + struct.pack('BBBBBBB', 0, 0, 0, 0, 0, 0, 0)
        return cInfoObj.bytes2(self) + struct.pack('B', self.spi) + struct.pack('BBBBBBB', 0, 0, 0, 0, 0, 0, 0)

class cCP56Time2a():
    milis = 0
    iv = False
    minute = 0
    su = False
    hour = 0
    dow = 0
    dom = 0
    month = 0
    year = 0
    
    def bytes(self):
        return struct.pack('HBBBBB', self.milis, int((self.iv & 0b1) << 7 | (self.minute & 0b11111)), int((self.su & 0b1) << 7 | (self.minute & 0b111111)), int((self.dow & 0b111) << 5 | (self.dom & 0x11111)), int(self.month & 0x1111), int(self.year & 0x1111111))
               
class cMSpTb1(cSIQ):

    type_id = 30
    name = 'M_SP_TB_1'
    description = 'Single-point information with time tag CP56Time2a'
    
    CP56Time2a = cCP56Time2a()
    
    def bytes(self):
        #return cSIQ.bytes(self) + struct.pack('BBBBBBB', 0, 0, 0, 0, 0, 0, 0)
        return cSIQ.bytes(self) + self.CP56Time2a.bytes()

class cMMeTf1(cInfoObj):
    type_id = 36
    name = 'M_ME_TF_1'
    description = 'Measured value, short floating point number with time tag CP56Time2a'
    
    value = 0
    CP56Time2a = cCP56Time2a()
    
    def bytes(self):
        return cInfoObj.bytes(self) + struct.pack('f', self.value) + self.CP56Time2a.bytes()
         

class ASDU(object):
    def __init__(self, data):
        print "hex: ", binascii.hexlify(data.bytes)
        self.type_id = data.read('uint:8')
        sq = data.read('bool')  # Single or Sequence
        sq_count = data.read('uint:7')
        self.cot = data.read('uint:8')
        data.read('uint:8')
        self.asdu = data.read('uint:16')
        #LOG.debug("Type: {}, COT: {}, ASDU: {}".format(self.type_id, self.cot, self.asdu))
        LOG.debug("Type: {}, COT: {}, CASDU: {}, CASDU1: {}, CASDU2: {}".format(self.type_id, self.cot, self.asdu, casdu1(self.asdu), casdu2(self.asdu)))

        self.objs = []
        if not sq:
            for i in xrange(sq_count):
                try:
                    obj = InfoObjMeta.types[self.type_id](data)
                    self.objs.append(obj)
                except:
                    LOG.debug("Unknown Type: {}".format(i))


class QDS(object):
    def __init__(self, data):

        overflow = bool(data & 0x01)
        blocked = bool(data & 0x10)
        substituted = bool(data & 0x20)
        not_topical = bool(data & 0x40)
        invalid = bool(data & 0x80)


class InfoObjMeta(type):
    types = {}

    def __new__(mcs, name, bases, dct):
        re = type.__new__(mcs, name, bases, dct)
        if 'type_id' in dct:
            InfoObjMeta.types[dct['type_id']] = re
        return re


class InfoObj(object):
    __metaclass__ = InfoObjMeta

    
    
    def __init__(self, data):
        self.ioa = data.read("uint:24")
        #print "IOA: ", self.ioa
        LOG.debug("IOA: {}, IAO1: {}, IAO2: {}, IOA:3 {}".format(self.ioa, ioa1(self.ioa), ioa2(self.ioa), ioa3(self.ioa)))
        #data.read("uint:16")
        #d = data.read("int:16")
        #while d:
        #    print d 
        #    d = data.read("int:16")

class SIQ(InfoObj):
    def __init__(self, data):
        super(SIQ, self).__init__(data)
        self.iv = data.read('bool')
        self.nt = data.read('bool')
        self.sb = data.read('bool')
        self.bl = data.read('bool')
        data.read('int:3')  # reserve
        self.spi = data.read('bool')


class DIQ(InfoObj):
    def __init__(self, data):
        super(DIQ, self).__init__(data)
        self.iv = data.read('bool')
        self.nt = data.read('bool')
        self.sb = data.read('bool')
        self.bl = data.read('bool')
        data.read('int:2')  # reserve
        self.dpi = data.read('uint:2')


class MSpNa1(SIQ):
    type_id = 1
    name = 'M_SP_NA_1'
    description = 'Single-point information without time tag'

    def __init__(self, data):
        super(MSpNa1, self).__init__(data)
        LOG.debug('Obj: M_SP_NA_1, Value: {}'.format(self.spi))


class MSpTa1(InfoObj):
    type_id = 2
    name = 'M_SP_TA_1'
    description = 'Single-point information with time tag'

    def __init__(self, data):
        super(MSpTa1, self).__init__(data)


class MDpNa1(DIQ):
    type_id = 3
    name = 'M_DP_NA_1'
    description = 'Double-point information without time tag'

    def __init__(self, data):
        super(MDpNa1, self).__init__(data)
        LOG.debug('Obj: M_DP_NA_1, Value: {}'.format(self.dpi))


class MDpTa1(InfoObj):
    type_id = 4
    name = 'M_DP_TA_1'
    description = 'Double-point information with time tag'


class MStNa1(InfoObj):
    type_id = 5
    name = 'M_ST_NA_1'
    description = 'Step position information'


class MStTa1(InfoObj):
    type_id = 6
    name = 'M_ST_TA_1'
    description = 'Step position information with time tag'


class MBoNa1(InfoObj):
    type_id = 7
    name = 'M_BO_NA_1'
    description = 'Bitstring of 32 bit'


class MBoTa1(InfoObj):
    type_id = 8
    name = 'M_BO_TA_1'
    description = 'Bitstring of 32 bit with time tag'


class MMeNa1(InfoObj):
    type_id = 9
    name = 'M_ME_NA_1'
    description = 'Measured value, normalized value'

    def __init__(self, data):
        super(MMeNa1, self).__init__(data)
        self.nva = data.read('int:8')
        self.nva = data.read('int:16')
        LOG.debug('Obj: M_ME_NA_1, Value: {}'.format(self.nva))


class MMeTa1(InfoObj):
    type_id = 10
    name = 'M_ME_TA_1'
    description = 'Measured value, normalized value with time tag'


class MMeNb1(InfoObj):
    type_id = 11
    name = 'M_ME_NB_1'
    description = 'Measured value, scaled value'


class MMeTb1(InfoObj):
    type_id = 12
    name = 'M_ME_TB_1'
    description = 'Measured value, scaled value with time tag'


class MMeNc1(InfoObj):
    type_id = 13
    name = 'M_ME_NC_1'
    description = 'Measured value, short floating point number'
    length = 5

    def __init__(self, data):
        super(MMeNc1, self).__init__(data)
        print binascii.hexlify(data.bytes)


        val = data.read("floatle:32")


        #qds = QDS(struct.unpack_from('B', data[7:])[0])
        #LOG.debug("Value: {}".format(val))
        LOG.debug('Obj: M_ME_NC_1, Value: {}'.format(self.val))
        
        #print "val", val


class MMeTc1(InfoObj):
    type_id = 14
    name = 'M_ME_TC_1'
    description = 'Measured value, short floating point number with time tag'


class MItNa1(InfoObj):
    type_id = 15
    name = 'M_IT_NA_1'
    description = 'Integrated totals'


class MItTa1(InfoObj):
    type_id = 16
    name = 'M_IT_TA_1'
    description = 'Integrated totals with time tag'


class MEpTa1(InfoObj):
    type_id = 17
    name = 'M_EP_TA_1'
    description = 'Event of protection equipment with time tag'


class MEpTb1(InfoObj):
    type_id = 18
    name = 'M_EP_TB_1'
    description = 'Packed start events of protection equipment with time tag'


class MEpTc1(InfoObj):
    type_id = 19
    name = 'M_EP_TC_1'
    description = 'Packed output circuit information of protection equipment with time tag'


class MPsNa1(InfoObj):
    type_id = 20
    name = 'M_PS_NA_1'
    description = 'Packed single-point information with status change detection'


class MMeNd1(InfoObj):
    type_id = 21
    name = 'M_ME_ND_1'
    description = 'Measured value, normalized value without quality descriptor'


#class MSpTb1(InfoObj):
class MSpTb1(SIQ):

    type_id = 30
    name = 'M_SP_TB_1'
    description = 'Single-point information with time tag CP56Time2a'
    
    def __init__(self, data):
        super(MSpTb1, self).__init__(data)
        LOG.debug('Obj: M_SP_TB_1, Value: {}'.format(self.spi))
        #print "spi", self.spi
    '''
    def __init__(self, data):
        super(MSpTb1, self).__init__(data)
        #print binascii.hexlify(data.bytes)
        self.val = data.read("bool")
        #qds = QDS(struct.unpack_from('B', data[7:])[0])
        print "spi", self.val
    '''

class MDpTb1(InfoObj):
    type_id = 31
    name = 'M_DP_TB_1'
    description = 'Double-point information with time tag CP56Time2a'


class MStTb1(InfoObj):
    type_id = 32
    name = 'M_ST_TB_1'
    description = 'Step position information with time tag CP56Time2a'


class MBoTb1(InfoObj):
    type_id = 33
    name = 'M_BO_TB_1'
    description = 'Bitstring of 32 bits with time tag CP56Time2a'


class MMeTd1(InfoObj):
    type_id = 34
    name = 'M_ME_TD_1'
    description = 'Measured value, normalized value with time tag CP56Time2a'


class MMeTe1(InfoObj):
    type_id = 35
    name = 'M_ME_TE_1'
    description = 'Measured value, scaled value with time tag CP56Time2a'


class MMeTf1(InfoObj):
    type_id = 36
    name = 'M_ME_TF_1'
    description = 'Measured value, short floating point number with time tag CP56Time2a'
    
    def __init__(self, data):
        super(MMeTf1, self).__init__(data)
        #print binascii.hexlify(data.bytes)
        self.val = data.read("floatle:32")
        #qds = QDS(struct.unpack_from('B', data[7:])[0])
        #print "val", self.val
        LOG.debug('Obj: M_ME_TF_1, Value: {}'.format(self.val))


class MItTb1(InfoObj):
    type_id = 37
    name = 'M_IT_TB_1'
    description = 'Integrated totals with time tag CP56Time2a'


class MEpTd1(InfoObj):
    type_id = 38
    name = 'M_EP_TD_1'
    description = 'Event of protection equipment with time tag CP56Time2a'


class MEpTe1(InfoObj):
    type_id = 39
    name = 'M_EP_TE_1'
    description = 'Packed start events of protection equipment with time tag CP56Time2a'


class MEpTf1(InfoObj):
    type_id = 40
    name = 'M_EP_TF_1'
    description = 'Packed output circuit information of protection equipment with time tag CP56Time2a'


class CScNa1(InfoObj):
    type_id = 45
    name = 'C_SC_NA_1'
    description = 'Single command'


class CDcNa1(InfoObj):
    type_id = 46
    name = 'C_DC_NA_1'
    description = 'Double command'


class CRcNa1(InfoObj):
    type_id = 47
    name = 'C_RC_NA_1'
    description = 'Regulating step command'


class CSeNa1(InfoObj):
    type_id = 48
    name = 'C_SE_NA_1'
    description = 'Set-point command, normalized value'


class CSeNb1(InfoObj):
    type_id = 49
    name = 'C_SE_NB_1'
    description = 'Set-point command, scaled value'


class CSeNc1(InfoObj):
    type_id = 50
    name = 'C_SE_NC_1'
    description = 'Set-point command, short floating point number'


class CBoNa1(InfoObj):
    type_id = 51
    name = 'C_BO_NA_1'
    description = 'Bitstring of 32 bit'


class MEiNa1(InfoObj):
    type_id = 70
    name = 'M_EI_NA_1'
    description = 'End of initialization'


class CIcNa1(InfoObj):
    type_id = 100
    name = 'C_IC_NA_1'
    description = 'Interrogation command'


class CCiNa1(InfoObj):
    type_id = 101
    name = 'C_CI_NA_1'
    description = 'Counter interrogation command'


class CRdNa1(InfoObj):
    type_id = 102
    name = 'C_RD_NA_1'
    description = 'Read command'


class CCsNa1(InfoObj):
    type_id = 103
    name = 'C_CS_NA_1'
    description = 'Clock synchronization command'


class CTsNa1(InfoObj):
    type_id = 104
    name = 'C_TS_NA_1'
    description = 'Test command'


class CRpNa1(InfoObj):
    type_id = 105
    name = 'C_RP_NA_1'
    description = 'Reset process command'


class CCdNa1(InfoObj):
    type_id = 106
    name = 'C_CD_NA_1'
    descripiton = 'Delay acquisition command'


class PMeNa1(InfoObj):
    type_id = 110
    name = 'P_ME_NA_1'
    description = 'Parameter of measured values, normalized value'


class PMeNb1(InfoObj):
    type_id = 111
    name = 'P_ME_NB_1'
    description = 'Parameter of measured values, scaled value'


class PMeNc1(InfoObj):
    type_id = 112
    name = 'P_ME_NC_1'
    description = 'Parameter of measured values, short floating point number'


class PAcNa1(InfoObj):
    type_id = 113
    name = 'P_AC_NA_1'
    description = 'Parameter activation'


class FFrNa1(InfoObj):
    type_id = 120
    name = 'F_FR_NA_1'
    description = 'File ready'


class FSrNa1(InfoObj):
    type_id = 121
    name = 'F_SR_NA_1'
    description = 'Section ready'


class FScNa1(InfoObj):
    type_id = 122
    name = 'F_SC_NA_1'
    description = 'Call directory, select file, call file, call section'


class FLsNa1(InfoObj):
    type_id = 123
    name = 'F_LS_NA_1'
    description = 'Last section, last segment'


class FAdNa1(InfoObj):
    type_id = 124
    name = 'F_AF_NA_1'
    description = 'ACK file, ACK section'


class FSgNa1(InfoObj):
    type_id = 125
    name = 'F_SG_NA_1'
    description = 'Segment'


class FDrTa1(InfoObj):
    type_id = 126
    name = 'F_DR_TA_1'
    description = 'Directory'
    