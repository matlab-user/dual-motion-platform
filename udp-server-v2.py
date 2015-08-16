# coding: utf-8

import socket
import select
import sys
import time
import json
#import RPi.GPIO as GPIO

class UPPER_PC:
	ip = ''
	port = 0
	
class scan_info:
	cur_mode = 'I'		# 当前运动模式
	cur_d = 1			# 当前运动方向
	cur_loop = 0		# 当前运动次数
	loop = 5			# 应进行的运动次数
	t1 = 5
	pulse_num = 20
	res = ''
	
class MOTOR:
	mode = 'I'			# 当前正在执行的指令 		SP-速度模式 P-位置模式 I-空闲模式 SCAN-扫描模式
	d = -1				# 电机运行方向，远离电机为 1，接近电机为0， 其余值为停止
	p_lt = 0.5			# 位置模式下，H（或L）脉冲持续时间，单位秒
	pulse = 0			# 当前脉冲电平
	ct = 0				# 上一次脉冲电平转换时间
	t1 = 0				# 速度模式下，为应该持续运动的时间数/位置模式下为应该发送的总脉冲数
	t2 = 0				# 速度模式下，为指令启动时间/位置模式下，为已经发送了多少脉冲数
	lt0 = 0				# 0/1限位开关状态，0 未触发
	lt1 = 0				
	stop = 0			# 0 - not order to stop;	1 - order to stop 
	done = 0			# done==1 引脚控制信号已经产生 
	s_info = None
	res = ''			# 当前操作结果反馈
	
# 指令集
# [ uid, H ]
# [ uid, SP, H+/H-/V+/V-, 5 ]			速度模式，电机和方向，持续时间
# [ uid, P, H+/H-/V+/V-, 5 ]			位置模式，电机和方向，脉冲数
# [ uid, STOP，H/V/A ]
# [ uid, ST ]							电机状态查询
# [uid, SCAN]							扫描模式

def parse_order( str ):
	str = str.replace( '[', '' )
	str = str.replace( ']', '' )
	str = str.replace( ' ', '' )
	return str.split( "," )

# 仅将电机信息数据结构设置为stop状态
def set_motor_info_idel( MOTOR_INFO ):
	MOTOR_INFO.mode = 'I'
	MOTOR_INFO.d = -1
	MOTOR_INFO.stop = 0
	MOTOR_INFO.t1 = 0
	MOTOR_INFO.t2 = 0
	MOTOR_INFO.done = 0
	
def control_motor():
	
	global H_MOTOR, V_MOTOR
	
	# 增加对 限位器 状态的读取代码，并更新电机信息数据
	
	now = time.time()
	
	# 优先处理 STOP 触发
	if H_MOTOR.stop==1:
		# add GPIO control code
		set_motor_info_idel( H_MOTOR )
		H_MOTOR.res = '[res,stopped]'
		
	if V_MOTOR.stop==1:
		# add GPIO control code
		set_motor_info_idel( V_MOTOR )
		H_MOTOR.res = '[res,stopped]'
		
	# 处理 限位开关 触发
	if H_MOTOR.mode!='I':
		if H_MOTOR.lt0==1 and H_MOTOR.d==0:
			# add GPIO control code, stop the motor
			set_motor_info_idel( H_MOTOR )
			H_MOTOR.lt0 = 0
			H_MOTOR.res = '[res,lt0-on-stopped]'
			
		if H_MOTOR.lt1==1 and H_MOTOR.d==1:
			# add GPIO control code, stop the motor
			set_motor_info_idel( H_MOTOR )
			H_MOTOR.lt1 = 0
			H_MOTOR.res = '[res,lt1-on-stopped]'
			
	if V_MOTOR.mode!='I':	
		if V_MOTOR.lt0==1 and V_MOTOR.d==0:
			# add GPIO control code, stop the motor
			set_motor_info_idel( V_MOTOR )
			V_MOTOR.lt0 = 0
			V_MOTOR.res = '[res,lt0-on-stopped]'
			
		if V_MOTOR.lt1==1 and V_MOTOR.d==1:
			# add GPIO control code, stop the motor
			set_motor_info_idel( V_MOTOR )
			V_MOTOR.lt1 = 0
			V_MOTOR.res = '[res,lt1-on-stopped]'
	
	# 执行当前动作
	if H_MOTOR.mode=='SP':			# 水平电机，速度模式
		if (now-H_MOTOR.t2)>=H_MOTOR.t1:		# 达到预定运行时间
			# add GPIO control code, stop the motor
			print '\t\t\t\tH_MOTOR SPEED END '+str(time.time())
			set_motor_info_idel( H_MOTOR )
			H_MOTOR.res = '[res,complete]'
		else:
			# 控制电机以速度方式运行
			if H_MOTOR.done==0:
				print '\t\t\t\tH_MOTOR SPEED START '+str(time.time())
				H_MOTOR.done = 1
			
	if H_MOTOR.mode=='P':			# 水平电机，位置模式
		if H_MOTOR.t2<H_MOTOR.t1:
			if (now-H_MOTOR.ct)>=H_MOTOR.p_lt:
				H_MOTOR.pulse = int(not H_MOTOR.pulse)
				H_MOTOR.t2 += 1
				# 控制电机脉冲运动
				
				H_MOTOR.ct = time.time()
		else:						# 完成位置运动，停止
			# add GPIO control code, stop the motor
			set_motor_info_idel( H_MOTOR )
			H_MOTOR.res = '[res,complete]'
	
	if V_MOTOR.mode=='SP':			# 竖直电机，速度模式
		if (now-V_MOTOR.t2)>=V_MOTOR.t1:
			# add GPIO control code, stop the motor
			print '\t\t\t\tV_MOTOR SPEED END '+str(time.time())
			
			set_motor_info_idel( V_MOTOR )
			V_MOTOR.res = '[res,complete]'
		else:
			# 控制电机以速度方式运行
			if V_MOTOR.done==0:
				print '\t\t\t\tV_MOTOR SPEED START '+str(time.time())
				V_MOTOR.done = 1
	
	if V_MOTOR.mode=='P':			# 竖直电机，位置模式
		if V_MOTOR.t2<V_MOTOR.t1:
			if (now-V_MOTOR.ct)>=V_MOTOR.p_lt:
				V_MOTOR.pulse = int(not V_MOTOR.pulse)
				V_MOTOR.t2 += 1
				# 控制电机脉冲运动
				
				V_MOTOR.ct = time.time()
		else:						# 完成位置运动，停止
			# add GPIO control code, stop the motor
			set_motor_info_idel( V_MOTOR )
			V_MOTOR.res = '[res,complete]'
	
	if H_MOTOR.mode=='SCAN':		# 扫描模式
		if H_MOTOR.s_info.cur_loop<H_MOTOR.s_info.loop and V_MOTOR.s_info.res=='[res,complete]':
			if (now-H_MOTOR.t2)>=H_MOTOR.t1:		# 达到预定运行时间
				# add GPIO control code, stop the motor
				
				H_MOTOR.s_info.res = '[res,complete]'
				H_MOTOR.s_info.cur_loop += 1
				H_MOTOR.t1 = H_MOTOR.s_info.t1
				H_MOTOR.s_info.cur_d = int(not H_MOTOR.s_info.cur_d)
				H_MOTOR.d = H_MOTOR.s_info.cur_d
				H_MOTOR.done = 0
				
				V_MOTOR.s_info.res = ''
				
				print 'H_MOTOR SPEED-' + str(H_MOTOR.s_info.cur_loop) + ' END\t' + str(time.time())
				
			else:
				# 控制电机以速度方式运行
				if H_MOTOR.done==0:
					print 'H_MOTOR SPEED dir-' + str(H_MOTOR.d) + ' START ' + str(time.time())
					H_MOTOR.done = 1
		
		if V_MOTOR.s_info.cur_loop<V_MOTOR.s_info.loop and H_MOTOR.s_info.res=='[res,complete]':	
			if V_MOTOR.t2<V_MOTOR.t1:
				if (now-V_MOTOR.ct)>=V_MOTOR.p_lt:
					V_MOTOR.pulse = int(not V_MOTOR.pulse)
					V_MOTOR.t2 += 1
					# 控制电机脉冲运动
					
					V_MOTOR.ct = time.time()
					print '\t\tV_MOTOR POSITION-MODE PULSE-' + str(V_MOTOR.t2) + '\tOUTPUT-' + str(V_MOTOR.pulse) + '\t' + str(time.time())
			else:						# 完成位置运动，停止
				# add GPIO control code, stop the motor
				
				V_MOTOR.s_info.res = '[res,complete]'
				V_MOTOR.s_info.cur_loop += 1
				V_MOTOR.t1 = V_MOTOR.s_info.pulse_num
				V_MOTOR.t2 = 0
				
				H_MOTOR.t2 = time.time()
				H_MOTOR.s_info.res = ''
				
		if H_MOTOR.s_info.cur_loop>=H_MOTOR.s_info.loop or V_MOTOR.s_info.cur_loop>=V_MOTOR.s_info.loop:
			H_MOTOR.res = '[res,complete]'
			V_MOTOR.res = '[res,complete]'
			H_MOTOR.mode = 'I'
			V_MOTOR.mode = 'I'
			print 'SCAN END \t'+str(time.time())
	
#---------------------------------------------------------------------	
UDP_IP = ''
UDP_PORT = 5005

PC = UPPER_PC()			# 用于记录控制计算机网络地址
H_MOTOR = MOTOR()
V_MOTOR = MOTOR()

#obj = [[1,2,3],123,123.123,'abc',{'key1':(1,2,3),'key2':(4,5,6)}]
#encodedjson = json.dumps(obj)
#print repr(obj)
#print encodedjson

#sys.exit()

while True:
	sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
	sock.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
	sock.setblocking( 0 )
	sock.bind( (UDP_IP, UDP_PORT) )
	
	epoll = select.epoll()
	epoll.register( sock.fileno(), select.EPOLLIN )

	print "MOTORS-CONTROL UDP SERVER IS RUNNING!"
	
	try:
		while 1:
			#print 't1--', time.time()
			events = epoll.poll( 0.1 )
			#print 't2--', time.time()
			
			for fileno, event in events:
				if fileno==sock.fileno():
					message, address = sock.recvfrom( 1400 )
					
					if message:						# message is not empty
						print "Got data from", address, ": ", message
						
						# 指令处理代码
						order = parse_order( message )
						if order:
							if order[1]=='H':		# upper pc show identitiy
								PC.ip = address[0]
								PC.port = address[1]
								message = '[H,OK]'
								
							if order[1]=='SP':		# motor speed mode move		
								
								order_d = -1
								if order[2][1]=='+':
									order_d = 1
								else:
									order_d = 0
									
								if order[2][0]=='H' and (H_MOTOR.mode!='SP' or H_MOTOR.d!=order_d):		# 保证同类型运动指令仅执行最先收到的
								
									H_MOTOR.mode = 'SP'
									H_MOTOR.t1 = float( order[3] )
									H_MOTOR.t2 = time.time()
									
									if order[2][1]=='+':
										H_MOTOR.d = 1
									else:
										H_MOTOR.d = 0
									
								if order[2][0]=='V' and (V_MOTOR.mode!='SP' or V_MOTOR.d!=order_d):
								
									V_MOTOR.mode = 'SP'
									V_MOTOR.t1 = float( order[3] )
									V_MOTOR.t2 = time.time()
									
									if order[2][1]=='+':
										V_MOTOR.d = 1
									else:
										V_MOTOR.d = 0
										
								message = '[SP,'+order[2]+',OK]'
																	
							if order[1]=='P':		# motor position mode move
							
								order_d = -1
								if order[2][1]=='+':
									order_d = 1
								else:
									order_d = 0
									
								if order[2][0]=='H' and (H_MOTOR.mode!='P' or H_MOTOR.d!=order_d):
								
									H_MOTOR.mode = 'P'
									H_MOTOR.t1 = float( order[3] )
									H_MOTOR.t2 = 0
									
									if order[2][1]=='+':
										H_MOTOR.d = 1
									else:
										H_MOTOR.d = 0
										
								if order[2][0]=='V' and (V_MOTOR.mode!='P' or V_MOTOR.d!=order_d):
								
									V_MOTOR.mode = 'P'
									V_MOTOR.t1 = float( order[3] )
									V_MOTOR.t2 = 0
									
									if order[2][1]=='+':
										V_MOTOR.d = 1
									else:
										V_MOTOR.d = 0
							
							if order[1]=='STOP':	# stop motor moving
								if order[2]=='H':
									H_MOTOR.stop = 1					
								if order[2]=='V':
									V_MOTOR.stop = 1			
								if order[2]=='A':
									H_MOTOR.stop = 1
									V_MOTOR.stop = 1
							
							if order[1]=='ST':		# return motor state
								#message
								pass
							
							if order[1]=='SCAN' and H_MOTOR.mode!='SCAN':
								H_MOTOR.mode = 'SCAN'
								V_MOTOR.mode = 'SCAN'
								
								H_MOTOR.s_info = scan_info()
								V_MOTOR.s_info = scan_info()
								
								H_MOTOR.s_info.cur_mode = 'SP'
								H_MOTOR.t2 = time.time()
								V_MOTOR.s_info.cur_mode = 'P'
								
								H_MOTOR.t1 = H_MOTOR.s_info.t1
								V_MOTOR.t1 = V_MOTOR.s_info.pulse_num
								V_MOTOR.s_info.res = '[res,complete]'
								
							sock.sendto( message, (PC.ip,PC.port) )		# 反馈给上位机[OK] 或 状态，指令已经处理
						
					else:
						PC.ip = ''
						PC.port = 0
			
			# 控制电机运动
			control_motor()
			#sock.sendto( message, address )		# 反馈给上位机，指令执行完毕及结果
			
	except( KeyboardInterrupt, SystemExit ):
		raise
		
	epoll.unregister( sock.fileno() )
	epoll.close()
	sock.close()
	time.sleep( 2 )
 



     
    
