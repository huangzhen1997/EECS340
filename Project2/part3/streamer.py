# do not import anything else from loss_socket besides LossyUDP
from lossy_socket import LossyUDP
# do not import anything else from socket except INADDR_ANY
from socket import INADDR_ANY

from concurrent.futures import ThreadPoolExecutor
from time import sleep
from threading import Timer

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
        self.wantToClose = False
        self.peerWantToClose = False


    def send(self, data_bytes: bytes):
        """Note that data_bytes can be larger than one packet."""
        # Your code goes here!  The code below should be changed!

        # for now I'm just sending the raw application-level data in one UDP payload

        seq = str(self.seqNum).encode() + b' '
        if (len(seq + data_bytes) <= 1472):
            self.socket.sendto(seq + data_bytes, (self.dst_ip, self.dst_port))
            self.send_buffer[self.seqNum] = seq + data_bytes
            self.send_timer[self.seqNum] = Timer(WAIT, self.sendFrame, [self.seqNum])
            self.send_timer[self.seqNum].start()
            self.seqNum = self.seqNum + 1
        else:
            while(len(seq + data_bytes) > 1472):
                sub_data_bytes = data_bytes[0:1472 - len(seq)]
                self.socket.sendto(seq + sub_data_bytes, (self.dst_ip, self.dst_port))
                self.send_buffer[self.seqNum] = seq + sub_data_bytes
                self.send_timer[self.seqNum] = Timer(WAIT, self.sendFrame, [self.seqNum])
                self.send_timer[self.seqNum].start()
                data_bytes = data_bytes[1472 - len(seq):]
                self.seqNum = self.seqNum + 1
                seq = str(self.seqNum).encode() + b' '
            
            if (len(data_bytes) > 0):
                self.socket.sendto(seq + data_bytes, (self.dst_ip, self.dst_port))
                self.send_buffer[self.seqNum] = seq + data_bytes
                self.send_timer[self.seqNum] = Timer(WAIT, self.sendFrame, [self.seqNum])
                self.send_timer[self.seqNum].start()
                self.seqNum = self.seqNum + 1
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.recvACK)

        while (future.running()):
            continue

        if (not future.running()):
            for i in range(0, future.result()):
                if i in self.send_buffer:
                    del self.send_buffer[i]

    def sendFrame(self, seqNum):
        self.socket.sendto(self.send_buffer[seqNum], (self.dst_ip, self.dst_port))
        self.send_timer[seqNum] = Timer(WAIT, self.sendFrame, [seqNum])
        self.send_timer[seqNum].start()
    
    def recvACK(self):
        while(True):
            try:
                response, addr = self.socket.recvfrom()
                print("receive ACK: ", response.decode())
                # for i in range(0, int(response.decode()), 1):
                #     if (i in self.send_timer):
                #         self.send_timer[int(response.decode()) - 1].cancel()
                #         del self.send_timer[int(response.decode()) - 1]
                self.send_timer[int(response.decode()) - 1].cancel()
                del self.send_timer[int(response.decode()) - 1]
            except InterruptedError:
                return True
            else:
                if len(self.send_timer):
                    continue
                else:
                    return int(response.decode())

    def recv(self) -> bytes:
        """Blocks (waits) if no data is ready to be read from the connection."""
        # your code goes here!  The code below should be changed!
        
        # this sample code just calls the recvfrom method on the LossySocket

        # new code Part3

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.recvfrom)
        
        # these statement for debug
        while (future.running()):
            sleep(0.01)

        # if(future.running()):
        #     return b''

        data = bytes()
        while (self.expected in self.recv_buffer):
            data += self.recv_buffer[self.expected]
            del self.recv_buffer[self.expected]
            self.expected = self.expected + 1 

        return data 
        

    # new code Part3
    def recvfrom(self):
        flag = 0
        while (True):
            try:
                data, addr = self.socket.recvfrom()
                if (data.decode() != 'FIN'):
                    self.recv_buffer[int(data.decode().split(' ', 1)[0])] = data.decode().split(' ', 1)[1].encode('utf-8')
                    flag = int(data.decode().split(' ', 1)[0]) + 1
                    print("send ACK: ", flag)
                    self.socket.sendto(str(flag).encode('utf-8'), (self.dst_ip, self.dst_port))
                elif (data.decode() == 'FIN'):
                    self.socket.sendto(b'DONE', (self.dst_ip, self.dst_port))
                    
            except InterruptedError:
                print("Debug info: InterruptedError")
                continue
            else:
                return True

    def sendFIN(self):
        self.socket.sendto(b'FIN', (self.dst_ip, self.dst_port))
        self.FIN_timer[0] = Timer(WAIT, self.sendFIN)
        self.FIN_timer[0].start()

    def close(self) -> None:
        """Cleans up. It should block (wait) until the Streamer is done with all
           the necessary ACKs and retransmissions"""
        # your code goes here, especially after you add ACKs and retransmissions.

        self.socket.sendto(b'FIN', (self.dst_ip, self.dst_port))
        self.FIN_timer[0] = Timer(WAIT, self.sendFIN)
        self.FIN_timer[0].start()

        data, addr = self.socket.recvfrom()
        while (self.wantToClose == False or self.peerWantToClose == False):
            if data == b'DONE':
                self.FIN_timer[0].cancel()
                del self.FIN_timer[0]
                self.wantToClose = True
                print ("!!!!!Receive DONE!!!!!")
            if data == b'FIN':
                self.peerWantToClose = True
                self.socket.sendto(b'DONE', (self.dst_ip, self.dst_port))
                print ("!!!!!Receive FIN!!!!!")
            if self.wantToClose and self.peerWantToClose:
                break
            else:
                data, addr = self.socket.recvfrom()

        if 0 in self.FIN_timer:
            del self.FIN_timer[0]

        


