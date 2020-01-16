#!/usr/bin/python

import socket
import sys
import select
import queue

def parseHeader(header):
    firstLine = header.split('\r\n', 1)[0]
    method, file = firstLine.split(' ')[:2]
    file = file.strip('/')
    return method, file

def buildHttpPackage(file):
    if (file[-5:] != '.html' and file[-4:] != '.htm'):
        header = 'HTTP/1.0 403 Forbidden\r\nContent-Type: text/html\r\n\r\n'
        body = '<html><head><title>403 Forbidden</title></head><body><h1>Forbidden</h1></body></html>'
        package = header + body
        return package
    
    try:
        with open(file, 'r') as f:
            header = 'HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n'
            package = header + f.read()
    except FileNotFoundError:
        header = 'HTTP/1.0 404 Not Found\r\nContent-Type: text/html\r\n\r\n'
        body = '<html><head><title>404 Not Found</title></head><body><h1>Not Found</h1><p>The requested file ' + file +  ' was not found on this server.</p></body></html>'
        package = header + body
    return package


def http_server(PORT):
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as server:
        server.setblocking(False)
        server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        server.bind(("", PORT))
        server.listen(10)
        inputs = [server]
        outputs = []
        message_queue = {}
        recvData = ''

        while inputs:
            readable, writable, exceptional = select.select(inputs, outputs, inputs)
            for entity in readable:
                if entity is server:
                    conn, addr = entity.accept()
                    #debug info
                    print('Connected by: ', addr)   
                    conn.setblocking(False)
                    inputs.append(conn)
                    message_queue[conn] = queue.Queue()
                else:
                    recvByteData = entity.recv(2048)
                    if recvByteData != b'':
                        recvData += recvByteData.decode("utf-8")
                        ## debug info
                        #print(recvData)
                        if (len(recvData.split('\r\n\r\n')) > 1):
                            header = recvData.split('\r\n\r\n', 1)[0] + '\r\n\r\n'
                            recvData = recvData.split('\r\n\r\n', 1)[1]
                            method, file = parseHeader(header)
                            ## debug info
                            print('Method: ', method)                           
                            print('Request file: ', file)
                            response = buildHttpPackage(file)
                            message_queue[entity].put(response)
                        if entity not in outputs:
                            outputs.append(entity)
                    else:
                        print ('closing', addr)
                        if entity in outputs:
                            outputs.remove(entity)
                        inputs.remove(entity)
                        entity.close()

                        del message_queue[entity]

            for entity in writable:
                try:
                    response = message_queue[entity].get_nowait()
                except:
                    outputs.remove(entity)
                else:
                    entity.sendall(response.encode("utf-8"))
                    print ('closing', addr)
                    if entity in outputs:
                        outputs.remove(entity)
                    inputs.remove(entity)
                    entity.close()
            
            for entity in exceptional:
                inputs.remove(entity)
                if entity in outputs:
                    outputs.remove(entity)
                entity.close()

                del message_queue[entity]



if __name__ == '__main__':
    if len(sys.argv) > 1:
        PORT = sys.argv[1]
    else:
        sys.exit(1)
    
    http_server(int(PORT))