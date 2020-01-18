import socket
import os
import sys
import select


def load_file(file):
    f=open(file,'r')
    out = f.read()
    return out
    
    
def receive(client):
    output=''
    while True:
        msg=client.recv(2048).decode('utf-8')
        if(msg==None):
            break
        output += msg
        if(output[-4:]=='\r\n\r\n'):
            break
    return output

def parse(req):
    return req.split(' ',2)[1].split('/',1)[1]
    

def response(req):
    path = parse(req)
    
    output='HTTP/1.1 '
    if(path.split('.')[-1]!='html' and path.split('.')[-1]!='htm'):
        output+='403 Forbidden\r\nConnection: Close\r\n\r\n'
        return output
    else:
         if(not os.path.exists(path)):
            output+='404 Not Found\r\nConnection: Close\r\n\r\n'
            return output
         else:
            body=load_file(path)
            output+='200 OK\r\nContent-Length: '+str(len(body))+'\r\nConnection: close\r\nContent-Type: text/html; charset=UTF-8\r\n'+body
            return output
        

def multi_connection(port):
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server.setblocking(False)
    server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    server.bind(('',port))
    server.listen(5)
    print('The server is ready to receive')
    open_connections=[server]
    while open_connections:
        readable, writable, exceptional = select.select(open_connections,
                                                    [],
                                                    open_connections)
        for conn in readable:
            print(conn)
            print(open_connections)
            if conn is server:
                print("test")
                connection_socket,addr = conn.accept()
                connection_socket.setblocking(1)
                open_connections.append(connection_socket)
            else:
                
                rqs = receive(conn)
                resp = response(rqs)
                conn.send(bytes(resp,'utf-8'))
                open_connections.remove(conn)
                conn.close()
                
        for s in exceptional:
            print('exception condition on', s.getpeername(),
                  file=sys.stderr)
            # Stop listening for input on the connection
            conn.remove(s)
            s.close()
    
multi_connection(int(sys.argv[1]))
