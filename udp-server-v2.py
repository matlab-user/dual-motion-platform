# coding: utf-8

import socket
import select
import time

class UPPER_PC:
	ip = ''
	port = 0

class MOTOR:
	state = 0			# 0 - idel;   1 - busy
	order = ''			# 当前正在执行的指令
	get_t = 0			# order 指令接收到的时间
	stop = 0			# 0 - not order to stop;	1 - order to stop 
	
UDP_IP = ''
UDP_PORT = 5005

PC = UPPER_PC()			# 用于记录控制计算机网络地址
H_MOTOR = MOTOR()
V_MOTOR = MOTOR()
	
while True:
	sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
	sock.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
	sock.setblocking( 0 )
	sock.bind( (UDP_IP, UDP_PORT) )
	
	epoll = select.epoll()
	epoll.register( sock.fileno(), select.EPOLLIN )

	try:
		while 1:
			print 't1--', time.time()
			events = epoll.poll( 0.5 )
			print 't2--', time.time()
			
			for fileno, event in events:
				if fileno==sock.fileno():
					message, address = sock.recvfrom( 1400 )
					
					if message:						# message is not empty
						print "Got data from", address, ": ", message
						
						# 指令处理代码
						sock.sendto( message, address )
						
					else:
						PC.ip = ''
						PC.port = 0
				
	except( KeyboardInterrupt, SystemExit ):
		raise
		
	epoll.unregister( sock.fileno() )
	epoll.close()
	sock.close()
	time.sleep( 2 )
 



     
    
