#!/usr/bin/python

import sys
import socket
import os
import json

    
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
    
    output=[]
    li = req.split('?')[1].split("&")
    for i in li:
        output.append(i.split('=')[1])
        
    if(req.split(' ')[1].split("?")[0]=='/product'):
        
        return [1,output]
    
    else:
        
        return [0,output]
    
    

def response(req):
    res = parse(req)
    output='HTTP/1.1 '
    operand=[]
    
    if(res[0]==0):
        output+='404 Not Found\r\nConnection: Close\r\n\r\n'
        return output
    else:
        out = 1.00
        for i in res[1]:
            try:
                operand.append(float(i))
                out = out * float(i)
                
            except:
                output+='400 Bad Request\r\nConnection: Close\r\n\r\n'
                return output
            
        body = json.dumps({'operation': 'product', 'operands': str(operand),'result':out}, sort_keys=False, indent=4)
        
        output+='200 OK\r\nContent-Length: '+str(len(body))+'\r\nConnection: close\r\nContent-Type: application/json; charset=UTF-8\r\n'+body
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
        
