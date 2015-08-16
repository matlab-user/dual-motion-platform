import socket, sys
import select
import time

def scan_server():
	UDP_IP = '255.255.255.255'
	UDP_PORT = 5005

	sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
	sock.setsockopt( socket.SOL_SOCKET, socket.SO_BROADCAST, 1 )
	sock.setblocking( 0 )


	epoll = select.epoll()
	epoll.register( sock.fileno(), select.EPOLLIN )
	sock.sendto( "["+str(time.time())+",H]", (UDP_IP,UDP_PORT) )

	try:
		events = epoll.poll( 10 )
		for fileno, event in events:
			if fileno==sock.fileno():
				message, address = sock.recvfrom( 1400 )
				#print "Got data from", address, ": ", message
				return address
				
	except( KeyboardInterrupt, SystemExit ):
		raise

if __name__ == '__main__':
	ip, port = scan_server()
	print ip, port