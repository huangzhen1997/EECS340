# do not import anything else from loss_socket besides LossyUDP
from lossy_socket import LossyUDP
# do not import anything else from socket except INADDR_ANY
from socket import INADDR_ANY


class Streamer:
    def __init__(self, dst_ip, dst_port,
                 src_ip=INADDR_ANY, src_port=0):
        """Default values listen on all network interfaces, chooses a random source port,
           and does not introduce any simulated packet loss."""
        self.socket = LossyUDP()
        self.socket.bind((src_ip, src_port))
        self.dst_ip = dst_ip
        self.dst_port = dst_port

        self.recvBuff = {}
        self.seqNum = 0
        self.recNum = 0

    def send(self, data_bytes: bytes):
        """Note that data_bytes can be larger than one packet."""
        # Your code goes here!  The code below should be changed!

        # for now I'm just sending the raw application-level data in one UDP payload
        i=0
        j=len(data_bytes)
        seq = (str(self.seqNum)+' ').encode()

        if((j+len(seq))>1472):
            while((j-i-len(seq))>1472):
                self.socket.sendto(seq+data_bytes[i:i+1472-len(seq)], (self.dst_ip, self.dst_port))
                i=i+1472-len(seq)
                self.seqNum=1+self.seqNum
                seq = (str(self.seqNum)+' ').encode()
            self.socket.sendto(seq+data_bytes[i:j], (self.dst_ip, self.dst_port))
        else:
            self.socket.sendto(seq+data_bytes, (self.dst_ip, self.dst_port))
            self.seqNum+=1

    def recv(self) -> bytes:
        """Blocks (waits) if no data is ready to be read from the connection."""
        # your code goes here!  The code below should be changed!
        
        # this sample code just calls the recvfrom method on the LossySocket


        while(True):
            data, addr = self.socket.recvfrom()
            output=''.encode()
            d=data.decode().split(' ',1)
            if d[0]==str(self.recNum):
                output = d[1].encode()
                self.recNum=self.recNum+1
                while(self.recNum in self.recvBuff):
                    output += self.recvBuff[self.recNum]
                    self.recNum+=1
                return output
            else:
                self.recvBuff[self.recNum] = d[1].encode()


