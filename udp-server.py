import socket
import select

class UPPER_PC:
	ip = ''
	port = 0
	
UDP_IP = ''
UDP_PORT = 5005

sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
sock.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
sock.setblocking( 0 )
sock.bind( (UDP_IP, UDP_PORT) )

PC = UPPER_PC()				# 用于记录控制计算机网络地址

epoll = select.epoll()
epoll.register( sock.fileno(), select.EPOLLIN )

while 1:
	try:
		message, address = sock.recvfrom( 1400 )
		print "Got data from", address, ": ", message
		sock.sendto( message, address )
		
	except( KeyboardInterrupt, SystemExit ):
		raise
 
 