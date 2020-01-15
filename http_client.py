#!/usr/bin/python

import socket
import sys

def receive(client):  # take client socket and keep reading message until the end
    output = ''
    while 1:
        msg=client.recv(2048)
        if(len(msg)==0):
            break
        output+=msg.decode("utf-8")
        
    return output

def parseWeb(url): # parse the url into hostname, path, port number
    
    if url[0:7] != 'http://':
        sys.exit(1)
    
    domain,path,port ='','/',80
    
    
    url_no_header = url.split('//')[1]
    two_part_url= url_no_header.split('/',1)
    
    if(len(two_part_url)==1):
        path_port = two_part_url[0].split(':')
        if(len(path_port)==1):
            domain = path_port[0]
        else:
            domain = path_port[0]
            port=int(path_port[1])
        
    else:
        path_port = two_part_url[1].split(':')
        if(len(path_port)==1):
            if(not two_part_url[1]):
                domain = two_part_url[0]
                if(len(domain.split(':'))>1):
                    domain=domain.split(':')[0]
            else:
                domain = two_part_url[0]
                if(len(domain.split(':'))>1):
                    domain=domain.split(':')[0]
                path += path_port[0]
        else:
            if(not path_port[0]):
                domain = two_part_url[0]
                if(len(domain.split(':'))>1):
                    domain=domain.split(':')[0]
                port=int(path_port[1])
            else:
                domain = two_part_url[0]
                if(len(domain.split(':'))>1):
                    domain=domain.split(':')[0]
                path+=path_port[0]
                port=int(path_port[1])
    
    return domain,path,port

def request(url): # send out the http request, and send the result into curl for the next step
    
    HOST, path, port = parseWeb(url)
    client =  socket.socket(socket.AF_INET,socket.SOCK_STREAM) #AF_INET is stand for IPv4, and SOCK_STREAM stands for TCP
    client.connect((HOST,port))
    
    rqs='GET '+ path
    rqs+=' HTTP/1.0'
    rqs+='\r\n'
    rqs+='Host: insecure.stevetarzia.com'
    rqs+='\r\n\r\n'
    
    client.send(rqs.encode())
    msg = receive(client)
    client.close()
    return curl(msg)



def curl(msg):
    global redirect_count
    check_status = msg.split(' ',2)
    status = int(check_status[1])
    
    if  status >= 400:
        formatHTML(msg)
        sys.exit(1)
        
    if status == 301 or status == 302: # should I just exit ? or warning too many redirect instead
        if(redirect_count >= 10):
            print('Way too many redirect !', file=sys.stderr)
            sys.exit(1)
        redirect_count +=1
        red_url = check_status[2].split('Location: ')[1].split('\r\n',1)[0]
        print('Redirected to: '+red_url, file=sys.stderr)
        request(red_url)
    
    else:
        formatHTML(msg)
        sys.exit()
        

def formatHTML(msg):
    twoPart = msg.split('Content-Type: ',1)
    if(len(twoPart)<=1):
        sys.exit(1)
    elif (twoPart[1].split(';')[0]!='text/html'):
        sys.exit(1)
    else:
        print(twoPart[1].split(';',1)[1].split('\r\n',1)[1])
        
redirect_count = 0
request(sys.argv[1])  
        
