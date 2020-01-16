#!/usr/bin/python

import socket
import sys

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
        server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        server.bind(("", PORT))
        server.listen(10)
        while True:
            conn, addr = server.accept()
            recvData = ''
            print('Connected by: ', addr)                               ## todo: debug info
            recvByteData = conn.recv(2048)
            if not recvByteData : break
            recvData += recvByteData.decode('utf-8')
            print(recvData)
            if (len(recvData.split('\r\n\r\n')) > 1):
                header = recvData.split('\r\n\r\n')[0] + '\r\n\r\n'
                recvData = recvData.split('\r\n\r\n')[1]
                method, file = parseHeader(header)
                print('Method: ', method)                           ## todo: debug info
                print('Request file: ', file)                       ## todo: debug info
                response = buildHttpPackage(file)
                conn.sendall(response.encode('utf-8'))
        conn.close()



if __name__ == '__main__':
    if len(sys.argv) > 1:
        PORT = sys.argv[1]
    else:
        sys.exit(1)
    
    http_server(int(PORT))
