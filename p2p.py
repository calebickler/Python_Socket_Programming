#!/usr/bin/env python

import socket
import select
import struct
import json
import random
import argparse

class Buffer():
        def __init__(self):
                self.read  = ''
                self.write = ''

def parseBuffer(buf):
    if len(buf.read) > 10:
        buf.write += buf.read
        buf.read = ''

def parse_args():
    """Return parsed command line arguments."""
    parser = argparse.ArgumentParser(description="NetI P2P Network")
    parser.add_argument('-b', help="Local bind IP", required=True)
    parser.add_argument('-p', help="Local bind port", required=True, type=int)
    parser.add_argument('-t', help="IP of tracker")
    parser.add_argument('-r', help="Port of tracker", type=int)
    parser.add_argument('-f', help="Name of file to seed")
    args = parser.parse_args()


    return args

tracker_ip = ''
args = parse_args()
local_ip = args.b
local_port = args.p
tracker_ip = args.t
tracker_port = args.r
print('Local socket: ', (local_ip, local_port))
print('Tracker: ', (tracker_ip, tracker_port))

# Create a server socket and append it to our sockets list
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.setblocking(0)
server.bind(('', local_port))
server.listen(5)

# Set aside a buffer pair for this socket
buffers = {}
buffers[server] = Buffer()

peerlist = []

if tracker_ip:
        print('connecting to tracker...')
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((tracker_ip, tracker_port))
	
	m = ''
        version = 1
        typeout = 3
        paylen = len(m)
        data = struct.pack('!BBH', version, typeout, paylen)
        s.send(data + m)

	m = json.dumps((local_ip, local_port))
        version = 1
        typeout = 5
        paylen = len(m)
        data = struct.pack('!BBH', version, typeout, paylen)
        s.send(data + m)
	
	hdr = s.recv(4)
	version, typein, paylen = struct.unpack('!BBH', hdr)
	
	m = json.loads(s.recv(paylen))
	for i in m:
		t = tuple(i)
		peerlist.append(t)
	
	print('recieved initial peerlist: ', peerlist) 

while 1:
        interest_write = filter(lambda b: len(buffers[b].write) > 0,buffers.keys())
        ready_read, ready_write, in_error = select.select(buffers.keys(), interest_write, [])

        # Send pending data and remove that data from the buffer
        for sock in ready_write:
                hdr = buffers[sock].write[:4]
                version, typein, paylen = struct.unpack('!BBH', hdr)
		m = buffers[sock].write[4:(paylen+4)]
		boolReply = 0
		buffers[sock].write = buffers[sock].write[(4+paylen):]

                if typein == 1:
                        responce = m
                        Rtype = 0
			boolReply = 1
                if typein == 2:
                        responce = json.dumps(random.random())
                        Rtype = 0
			boolReply = 1
                if typein == 3:
                        responce = json.dumps(peerlist)
                        Rtype = 4
			boolReply = 1
			print('recieved peerlist request')
		if typein == 4:
			listIn = json.loads(m)
			peerlistIn = []
			for z in listIn:
				t = tuple(z)
				peerlistIn.append(t)

			for x in peerlistIn:
				append = 1
				for i in peerlist:
					if x == i or x == (local_ip, local_port):
						append = 0
				if append == 1:
					peerlist.append(x)
			
			print('Recieved peerlist: ', peerlist)
		if typein == 5:
			advert = json.loads(m)
			Tadvert = tuple(advert)
			print('recieved advertisement: ', Tadvert)
			peerlist.append(Tadvert)
			
		if boolReply:
                	Rversion = 1
                	Rpaylen = len(responce)
                	Rdata = struct.pack('!BBH', Rversion, Rtype, Rpaylen)
                	sent = sock.send(Rdata + responce)
			print('sent responce', sent)

        for sock in ready_read:
                if sock != server:
                        buf = sock.recv(4096)
                        if len(buf):
                                buffers[sock].read += buf
                                parseBuffer(buffers[sock])
                        else:
                                del buffers[sock]
                                print "CLIENT CLOSED CONN"
                else:
                        incoming, address = server.accept()
                        incoming.setblocking(0)
                        buffers[incoming] = Buffer()
                        print "ACCEPTED CONNECTION from ", address