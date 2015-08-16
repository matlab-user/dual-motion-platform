import socket, sys, select
import time
import find_server

host, port = find_server.scan_server()
print "Found the server's address:\t", host, port

#order = "["+str(time.time())+", SP, H+, 10]"
#order = "["+str(time.time())+", SP, V-, 10]"
order = "["+str(time.time())+", SCAN]"
#order = "["+str(time.time())+", STOP, A]"

while True:
	sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
	sock.setblocking( 0 )
	
	epoll = select.epoll()
	epoll.register( sock.fileno(), select.EPOLLIN )

	sock.sendto( "["+str(time.time())+",H]", (host,port) )

	while True:
		events = epoll.poll( 5 )
		for fileno, event in events:
			if fileno==sock.fileno():
				message, address = sock.recvfrom( 1400 )
				if message!='':
					print "Got the message:\t"+message
					message = ''
				
				if order=='':
					epoll.unregister( sock.fileno() )
					epoll.close()
					sock.close()
					sys.exit()
				
				if order!='':
					sock.sendto( order, (host,port) )
					order = ''
	
	epoll.unregister( sock.fileno() )
	epoll.close()
	sock.close()