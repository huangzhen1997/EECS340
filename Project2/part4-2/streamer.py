# do not import anything else from loss_socket besides LossyUDP
from lossy_socket import LossyUDP
# do not import anything else from socket except INADDR_ANY
from socket import INADDR_ANY

from concurrent.futures import ThreadPoolExecutor
from time import sleep
from threading import Timer, Lock
import threading

WAIT = 0.25

class Streamer:
    def __init__(self, dst_ip, dst_port,
                 src_ip=INADDR_ANY, src_port=0):
        """Default values listen on all network interfaces, chooses a random source port,
           and does not introduce any simulated packet loss."""
        self.socket = LossyUDP()
        self.socket.bind((src_ip, src_port))
        self.dst_ip = dst_ip
        self.dst_port = dst_port


        # new code Part2
        self.seqNum = 0
        self.expected = 0
        self.recv_buffer = {}
        self.send_buffer = {}
        self.send_timer = {}
        self.recv_timer = {}

        # new code Part3
        self.FIN_timer = {}
        self.status = 'CONNECTION_ESTABLISHED'


    def generateChecksum(self, data_bytes):
        checksum = 0
        for char in data_bytes:
            checksum = (checksum >> 1) + ((checksum & 1) << 15)
            checksum += char
            checksum &= 0xffff
        return str(checksum)


    def check(self, data):
        try:
            segment = data.decode().split(' ', 2)
        except:
            return ['error']

        if (len(segment) != 3):
            return ['error']
        else:
            checksum = self.generateChecksum(segment[0].encode('utf-8') + b' 00000 ' + segment[2].encode('utf-8'))
            if checksum != segment[1]:
                return ['error']
            else:
                return segment

    
    def sendTimeOutFrame(self, typeFrame, seqNum):
        if (typeFrame == 'dataFrame'):
            self.send_timer[seqNum] = Timer(WAIT, self.sendTimeOutFrame, ['dataFrame', seqNum])
            self.socket.sendto(self.send_buffer[seqNum], (self.dst_ip, self.dst_port))
            self.send_timer[seqNum].start()

    
    def generateOutputFrame(self, data_bytes: bytes):
        seq = str(self.seqNum).encode('utf-8') + b' '
        if (len(data_bytes + seq) + 6 <=1472):
            checksum = self.generateChecksum(seq + b'00000 ' + data_bytes)
            self.send_buffer[self.seqNum] = seq + checksum.encode('utf-8') + b' ' + data_bytes
            self.send_timer[self.seqNum] = Timer(WAIT, self.sendTimeOutFrame, ['dataFrame', self.seqNum])
            self.seqNum = self.seqNum + 1
            seq = str(self.seqNum).encode('utf-8') + b' '
        else:
            while (len(data_bytes + seq) + 6 > 1472):
                sub_data_bytes = data_bytes[0: 1472 - len(seq) - 6]
                checksum = self.generateChecksum(seq + b'00000 ' + sub_data_bytes)
                self.send_buffer[self.seqNum] = seq + checksum.encode('utf-8') + b' ' + sub_data_bytes
                self.send_timer[self.seqNum] = Timer(WAIT, self.sendTimeOutFrame, ['dataFrame', self.seqNum])
                data_bytes = data_bytes[1472 - len(seq) - 6:]
                self.seqNum = self.seqNum + 1
                seq = str(self.seqNum).encode('utf-8') + b' '

            checksum = self.generateChecksum(seq + b'00000 ' + data_bytes)
            self.send_buffer[self.seqNum] = seq + checksum.encode('utf-8') + b' ' + data_bytes
            self.send_timer[self.seqNum] = Timer(WAIT, self.sendTimeOutFrame, ['dataFrame', self.seqNum])
            self.seqNum = self.seqNum + 1
            seq = str(self.seqNum).encode('utf-8') + b' '


    def sendFrameFromSendBuffer(self):
        # send_buffer = {}
        # for elem in self.send_buffer:
        #     send_buffer[i] = self.send_buffer[i]
        
        # for i in send_buffer
        for i in self.send_buffer:
            print('Debug info >> send DataFrame ', i)
            self.socket.sendto(self.send_buffer[i], (self.dst_ip, self.dst_port))
            self.send_timer[i].start()
        
        return True


    def recvFrameForSendBuffer(self):
        while(len(self.send_buffer) > 0):
            data, addr = self.socket.recvfrom()
            segment = self.check(data)
            if (segment[0] == 'error'):
                continue
            elif (segment[0] == 'ACK'):
                self.send_timer[int(segment[2]) - 1].cancel()
                del self.send_timer[int(segment[2]) - 1]
                del self.send_buffer[int(segment[2]) - 1]
                print('Debug info >> recv ACK for DataFrame ', int(segment[2]) - 1)
            else:
                continue
        
        return True

    
    # def recvFrameForRecvBuffer(self):
        
    #     data, addr = self.socket.recvfrom()


    def send(self, data_bytes: bytes):
        """Note that data_bytes can be larger than one packet."""
        # Your code goes here!  The code below should be changed!

        # for now I'm just sending the raw application-level data in one UDP payload
        self.generateOutputFrame(data_bytes)

        with ThreadPoolExecutor(max_workers = 2) as executor:
            futures = [executor.submit(self.sendFrameFromSendBuffer()), executor.submit(self.recvFrameForSendBuffer())]
            for future in futures:
                pass

    

    def recv(self) -> bytes:
        """Blocks (waits) if no data is ready to be read from the connection."""
        
        data, addr = self.socket.recvfrom()
        segment = self.check(data)
        if (segment[0].isdigit()):
            checksum = self.generateChecksum(b'ACK 00000 ' + str(int(segment[0]) + 1).encode('utf-8'))
            self.socket.sendto(b'ACK ' + checksum.encode('utf-8') + b' ' + str(int(segment[0]) + 1).encode('utf-8'), (self.dst_ip, self.dst_port))
            self.recv_buffer[int(segment[0])] = segment[2].encode('utf-8')
        elif (segment[0] == 'FIN'):
            self.status = 'CLOSING_WAIT'
            
        data = bytes()
        while (self.expected in self.recv_buffer):
            data += self.recv_buffer[self.expected]
            del self.recv_buffer[self.expected]
            self.expected = self.expected + 1 

        return data 
    

    def close(self) -> None:
        """Cleans up. It should block (wait) until the Streamer is done with all
           the necessary ACKs and retransmissions"""

        # your code goes here, especially after you add ACKs and retransmissions.
        # if (self.status == 'CONNECTION_ESTABLISHED'):

        #     for i in self.send_timer.keys():
        #         del self.send_timer[i]
        #     for i in self.recv_timer.keys():
        #         del self.recv_timer[i]

        #     checksum = self.generateChecksum(b'FIN 00000 0')
        #     self.FIN_timer[0] = Timer(WAIT, self.sendTimeOutFrame, ['FIN', ''])
        #     self.socket.sendto(b'FIN ' + checksum.encode('utf-8') + b' 0', (self.dst_ip, self.dst_port))
        #     self.status = 'FIN_WAIT_1'

        #     while (self.status != 'TIME_WAIT'):
        #         data, addr = self.socket.recvfrom()
        #         segment = self.check(data)
        #         if (segment[0] == 'error'):
        #             continue
        #         elif (segment[0] == 'ACK' and self.status == 'FIN_WAIT_1'):
        #             self.status = 'FIN_WAIT_2'
        #         elif (segment[0] == 'FIN' and self.status == 'FIN_WAIT_1'):
        #             self.status = 'CLOSING'
        #         elif (segment[0] == 'FIN' and self.status == 'FIN_WAIT_2'):
        #             self.status = 'TIME_WAIT'
        #         elif (segment[0] == 'ACK' and self.status == 'CLOSING'):
        #             self.status = 'TIME_WAIT'

        # elif (self.status == 'CLOSE_WAIT'):