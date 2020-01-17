#!/usr/bin/python

import sys
import socket
import os


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
        
        
    

def connection(port):
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server.bind(('',port))
    server.listen(5)
    print('The server is ready to receive')

    while True:
        clientsocket, address = server.accept()
        print(f'Connection from {address} has been established!')
        request = receive(clientsocket)
        resp = response(request)
        clientsocket.send(bytes(resp,'utf-8'))
        clientsocket.close()
        
connection(int(sys.argv[1]))