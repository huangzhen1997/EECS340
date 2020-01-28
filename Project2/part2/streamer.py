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

        # new code Part2
        self.seqNum = 0
        self.expected = 0
        self.bytes_buffer = {}

    def send(self, data_bytes: bytes):
        """Note that data_bytes can be larger than one packet."""
        # Your code goes here!  The code below should be changed!

        # for now I'm just sending the raw application-level data in one UDP payload

        # new code Part2
        seq = str(self.seqNum).encode() + b' '
        if (len(seq + data_bytes) <= 1472):
            self.socket.sendto(seq + data_bytes, (self.dst_ip, self.dst_port))
            self.seqNum = self.seqNum + 1
        else:
            while(len(seq + data_bytes) > 1472):
                sub_data_bytes = data_bytes[0:1472 - len(seq)]
                self.socket.sendto(seq + sub_data_bytes, (self.dst_ip, self.dst_port))
                data_bytes = data_bytes[1472 - len(seq):]
                self.seqNum = self.seqNum + 1
                seq = str(self.seqNum).encode() + b' '
            
            if (len(data_bytes) > 0):
                self.socket.sendto(seq + data_bytes, (self.dst_ip, self.dst_port))
                self.seqNum = self.seqNum + 1


    def recv(self) -> bytes:
        """Blocks (waits) if no data is ready to be read from the connection."""
        # your code goes here!  The code below should be changed!
        
        # this sample code just calls the recvfrom method on the LossySocket

        # new code Part2

        while (True):
            data, addr = self.socket.recvfrom()

            if data.decode().split(' ', 1)[0] == str(self.expected):
                data = data.decode().split(' ', 1)[1].encode('utf-8')
                self.expected = self.expected + 1                           # round?
                while (self.expected in self.bytes_buffer):
                    data += self.bytes_buffer[self.expected]
                    del self.bytes_buffer[self.expected]
                    self.expected = self.expected + 1                       # round?
                return data
            else:
                self.bytes_buffer[int(data.decode().split(' ', 1)[0])] = data.decode().split(' ', 1)[1].encode('utf-8')
        
        # For now, I'll just pass the full UDP payload to the app
        return data
