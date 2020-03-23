#!/usr/bin/env python
import numpy as np
import base64

class LFSR():
    def __init__(self, fpoly=[5,2], initstate='ones', verbose=False):
        if isinstance(initstate, str):
            if initstate=='ones':
                initstate = np.ones(np.max(fpoly))
            elif initstate=='random':
                initstate = np.random.randint(0,2,np.max(fpoly))
            else:
                raise Exception('Unknown initial state')

        self.initstate = initstate
        self.fpoly  = fpoly
        self.state  = initstate.astype(int)
        self.count  = 0
        self.seq    = np.array(-1)
        self.outbit = -1
        self.feedbackbit = -1
        self.verbose = verbose
        self.M = self.initstate.shape[0]
        self.expectedPeriod = 2**self.M -1
        self.fpoly.sort(reverse=True)
        feed = ' '
        for i in range(len(self.fpoly)):
            feed = feed + 'x^'+str(self.fpoly[i])+' + '
        feed = feed + '1'
        self.feedpoly = feed

    def set(self,fpoly,state='ones'):
        self.__init__(fpoly=fpoly,initstate=state)

    def reset(self):
        self.__init__(initstate=self.initstate,fpoly=self.fpoly)

    def changeFpoly(self, newfpoly, reset=False):
        newfpoly.sort(reverse=True)
        self.fpoly =newfpoly
        feed = ' '
        for i in range(len(self.fpoly)):
            feed = feed + 'x^'+str(self.fpoly[i])+' + '
        feed = feed + '1'
        self.feedpoly = feed

        self.check()
        if reset:
            self.reset()

    def next(self):
        b = np.logical_xor(self.state[self.fpoly[0]-1],self.state[self.fpoly[1]-1])
        if len(self.fpoly)>2:
            for i in range(2,len(self.fpoly)):
                b = np.logical_xor(self.state[self.fpoly[i]-1],b)

        self.state = np.roll(self.state, 1)
        self.state[0] = b*1
        self.feedbackbit = b*1
        if self.count==0:
            self.seq = self.state[-1]
        else:
            self.seq = np.append(self.seq,self.state[-1])
        self.outbit = self.state[-1]
        self.count +=1
        if self.verbose:
            print('S: ',self.state)
        return self.state[-1]

    def runFullCycle(self):
        for i in range(self.expectedPeriod):
            self.next()
        return self.seq

    def runKCycle(self,k):
        tempseq =np.ones(k)*-1
        for i in range(k):
            tempseq[i] = self.next()

        return tempseq

fpoly1 = [8,4,1]
fpoly2 = [13,6,3]

def try_decrypt(state1, state2, encoded):
    A = LFSR(fpoly=fpoly1, initstate =state1)
    B = LFSR(fpoly=fpoly2, initstate =state2)

    size = len(encoded)
    decoded = bytearray(size)

    for i in range(size):
        newbyte1=0
        newbyte2=0
        for x in range(8):
            A.next()
            B.next()
            newbyte1 += A.outbit*pow(2,x)
            newbyte2 += B.outbit*pow(2,x)

        xorbyte=(newbyte1+newbyte2)%256

        decoded[i] = encoded[i] ^ xorbyte

    return decoded

encoded = "DKZTX9KkUPyLum+Ic0YPXlNf/6oO98xmpVfV7XugAXoCLGsgVSao3/8tcNNEAN828fpziH0sQ8dUEAmTKXbFfSdZRvqhqA8iAozuFPJ+"

xord_byte_array = base64.b64decode(encoded)

flag_prefix = "Well done! You got the flag. The flag is HackTrinity{".encode('ascii')

state1_len = 13
state2_len = 19

stSz = 2**state1_len

status_len = 30

for i in range(2**state1_len):
    if i % 50 == 0:
        progress = round((i / stSz) * status_len)
        print('\rProgress: [{0}] {1:.2f}'.format('=' * progress + ' ' * (status_len - progress), (i / stSz) * 100), end='')
    state1 = np.array([int(b) for b in np.binary_repr(i, state1_len)], dtype=np.int8)
    A = LFSR(fpoly=fpoly1, initstate =state1)

    state2 = np.zeros(state2_len, dtype=np.int8)
    i = 0
    for enc, dec in zip(xord_byte_array, flag_prefix):
        xorbyte = enc ^ dec
        newbyte1 = 0
        for x in range(8):
            A.next()
            newbyte1 += A.outbit*pow(2,x)

        newbyte2 = (xorbyte - newbyte1) % 256

        for b in np.binary_repr(newbyte2, 8)[::-1]:
            state2[state2_len-i-2] = int(b)
            i += 1
            if i >= state2_len-1:
                break
        if i >= state2_len:
            break
    if try_decrypt(state1, state2, xord_byte_array[:10]) == flag_prefix[0:10]:
        print("\nstate1 = ", state1)
        print("state2 = ", state2)
        print(try_decrypt(state1, state2, xord_byte_array))
        break
