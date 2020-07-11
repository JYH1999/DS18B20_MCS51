#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  DS18B20上位机.py
#  
#  Copyright 2019 金煜航 <jinyuhang@whut.edu.cn>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  
from tkinter import *
import threading
import serial
import serial.tools.list_ports
import time
import random
import itchat
from tkinter import scrolledtext
import sqlite3
import os
import base64
#各种变量
tmpctl=0#温度检测开启变量
wechatctl=0#微信开启变量
tmp=4000#全局温度变量
tmp_high=0#报警温度上限
tmp_low=0#报警温度下限
nickname=[]#微信昵称
remarkname=[]#微信备注
wechat_target='Silicon Fish'
db_status=0
db_warn=0
db_warn_cursor=0#微信提醒目标账号
#各种函数
def usr_login():#微信登录函数
	global wechatctl
	global wechat_target
	itchat.auto_login(hotReload=True)
	friends=itchat.get_friends(update=True)
	global nickname
	global remarkname
	t=0
	flag=0
	text1.config(state=NORMAL)
	text1.insert(INSERT,'微信登录成功！\n')
	#text1.insert(INSERT,'可选警告发送对象:\n')
	for x in friends:
		t=t+1
	for i in range(t):
		#non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)
		#text1.insert(INSERT,str(friends[i]["RemarkName"]+"-"+friends[i]["NickName"]).translate(non_bmp_map))
		#text1.insert(INSERT,'\n')
		nickname.append(friends[i]["NickName"])
		remarkname.append(friends[i]["RemarkName"])
	if wechat_target in nickname:
		text1.insert(INSERT,'检测到警告提醒账号！\n微信提醒开启成功！\n')
	elif wechat_target in remarkname:
		text1.insert(INSERT,'检测到警告提醒账号！\n微信提醒开启成功！\n')
	else:
		text1.insert(INSERT,'未检测到警告提醒账号！\n微信提醒开启失败！\n')
	wechatctl=1
	if wechatctl==0:
		text1.insert(INSERT,'微信提醒开启失败，请重试！\n')
	text1.config(state=DISABLED)
	#temp='正在登录...请扫描二维码'
def com_scan():#串口扫描
	#text1.delete('1.0', 'end')#清空text1
	text1.config(state=NORMAL)
	port_list=list(serial.tools.list_ports.comports())
	#print(port_list)
	if len(port_list)==0:
		text1.insert(INSERT,'未检测到可用串口设备！\n温度读取失败，请检查连接并重新启动本程序！\n')
	else:
		text1.insert(INSERT,'检测到以下串口设备：\n')
		for i in port_list:
			text1.insert(INSERT,i)
		text1.insert(INSERT,'\n')
	text1.config(state=DISABLED)
def com_read(portx,bps,time_out):#读取串口
	global tmp
	ser_read=serial.Serial(portx,bps,time_out)
	#ser_read.open()
	tmp_read=ser_read.read(4)
	tmp_read_return=bytes.decode(tmp_read)#将字节转换成字符串
	#print(float(tmp_read))#测试代码
	ser_read.close()
	tmp=float(tmp_read_return)
	#print(tmp)测试代码
	return tmp_read_return				
def com_read_threads():#读取串口线程函数
	text1.config(state=NORMAL)
	text1.insert(INSERT,'程序初始化成功！\n')
	text1.config(state=DISABLED)
	#temp_init=0
	while 1:
		temp_com_read=com_read('COM8',9600,8)#延时必须设置为8，用于接收字符串，否则会产生SizeError!
		temp_com_read='实时温度:'+temp_com_read+'℃'
		label_tmp.config(text=temp_com_read)
		time.sleep(0.5)	
def tmpctl_on():#温度警报启动函数
	global tmpctl
	global tmp
	global tmp_high
	global tmp_low
	text1.config(state=NORMAL)
	#text1.insert(INSERT,str(tmp))
	if tmp==4000:
		text1.insert(INSERT,'传感器温度尚未获得，报警开启失败！\n')
		return
	if tmpctl==1:
		text1.insert(INSERT,'温度报警已经处于开启模式！\n')
	else:
		#tmp_temp=tmp
		tmp_high_temp=scale_up.get()
		tmp_low_temp=scale_down.get()
		if tmp_high_temp<tmp_low_temp:
			text1.insert(INSERT,'报警温度范围设置错误，报警开启失败！\n')
		else:
			tmp_high=tmp_high_temp
			tmp_low=tmp_low_temp
			tmpctl=1
			text_send='温度报警开启！\n'+'已设定温度上限：'+str(tmp_high_temp)+'℃\n'+'已设定温度下限：'+str(tmp_low_temp)+'℃\n'
			if tmpctl==0:
				text1.insert(INSERT,'温度报警开启失败！\n')
			else:
				text1.insert(INSERT,text_send)
	text1.config(state=DISABLED)		
def tmpctl_off():#温度警报关闭函数
	text1.config(state=NORMAL)	
	global tmpctl
	if tmpctl==0:
		text1.insert(INSERT,'报警已经处于关闭状态！\n')
	else:
		tmpctl=0
		if tmpctl==0:#检验变量是否被其他线程更改，导致开启失败
			text1.insert(INSERT,'温度报警成功关闭！\n')
		else:
			text1.insert(INSERT,'温度报警关闭失败！\n')
	text1.config(state=DISABLED)	
def warning_display():#异常温度显示
	global tmpctl
	global tmp
	global tmp_high
	global tmp_low
	text1.config(state=NORMAL)	
	if tmpctl==1:
		if tmp<tmp_low:
			label_tmp.config(fg='blue')
			label_tmp_down.config(fg='blue')
			label_tmp_down.config(text='温度过低！')
			label_tmp_up.config(fg='black')
			label_tmp_up.config(text='温度上限')
		elif tmp>tmp_high:
			label_tmp.config(fg='red')
			label_tmp_up.config(fg='red')
			label_tmp_up.config(text='温度过高！')
			label_tmp_down.config(fg='black')
			label_tmp_down.config(text='温度下限')
		else:
			label_tmp.config(fg='black')
			label_tmp_up.config(fg='black')
			label_tmp_up.config(text='温度上限')
			label_tmp_down.config(fg='black')
			label_tmp_down.config(text='温度下限')
	else:
		label_tmp.config(fg='black')
		label_tmp_up.config(fg='black')
		label_tmp_up.config(text='温度上限')
		label_tmp_down.config(fg='black')
		label_tmp_down.config(text='温度下限')
	text1.config(state=DISABLED)
def warning_display_threads():#异常温度显示线程
	while True:
		warning_display();
		time.sleep(0.1)
def warning_wechat():#异常温度微信提示
	global tmpctl
	global tmp
	global tmp_high
	global tmp_low
	global wechat_target
	global wechatctl
	if tmpctl==1:
		temp_time=time.strftime("%Y-%m-%d %H:%M:%S")
		if wechatctl==1:
			if tmp<tmp_low:
				if(wechat_target in nickname):
					temp_info=itchat.search_friends(wechat_target)
					temp_ID=temp_info[0]["UserName"]
					temp_wechat_send=temp_time+' 警告：温度过低！目标温度下限'+str(tmp_low)+'℃，当前温度'+str(tmp)+'℃'
					itchat.send(temp_wechat_send,temp_ID)
				elif(wechat_target in remarkname):
					temp_info=itchat.search_friends(nickname[remarkname.index(wechat_target)])
					temp_ID=temp_info[0]["UserName"]
					temp_wechat_send=temp_time+' 警告：温度过低！目标温度下限'+str(tmp_low)+'℃，当前温度'+str(tmp)+'℃'
					itchat.send(temp_wechat_send,temp_ID)			 		
			elif tmp>tmp_high:
				if(wechat_target in nickname):
					temp_info=itchat.search_friends(wechat_target)
					temp_ID=temp_info[0]["UserName"]
					temp_wechat_send=temp_time+' 警告：温度过高！目标温度上限'+str(tmp_high)+'℃，当前温度'+str(tmp)+'℃'
					itchat.send(temp_wechat_send,temp_ID)
				elif(wechat_target in remarkname):
					temp_info=itchat.search_friends(nickname[remarkname.index(wechat_target)])
					temp_ID=temp_info[0]["UserName"]
					temp_wechat_send=temp_time+' 警告：温度过高！目标温度上限'+str(tmp_high)+'℃，当前温度'+str(tmp)+'℃'
					itchat.send(temp_wechat_send,temp_ID)
def warning_wechat_threads():#温度异常微信提醒线程
	while True:
		warning_wechat()
		time.sleep(5)
def db_init():#数据库初始化函数
	global db_status
	global db_warn
	global db_warn_cursor
	text1.config(state=NORMAL)	
	text1.insert(INSERT,'程序目录下未检测到数据库\n')
	text1.insert(INSERT,'新建数据库成功！\n')
	db_warn_cursor.execute('''CREATE TABLE WARNING_RECORD(TIME   TEXT   NOT NULL,STATUS   TEXT   NOT NULL,TMP_DETECTED   TEXT   NOT NULL,TMP_TARGET   TEXT   NOT NULL);''')
	db_warn.commit()
	text1.config(state=DISABLED)
	#db_warn.close()
def db_insert(record_time,record_status,tmp_detected,tmp_target):#数据库写入函数
	global db_status
	global db_warn
	global db_warn_cursor
	db_warn_cursor.execute("INSERT INTO WARNING_RECORD (TIME,STATUS,TMP_DETECTED,TMP_TARGET) VALUES(?,?,?,?)",(str(record_time),str(record_status),str(tmp_detected),str(tmp_target)))
	db_warn.commit()
	#db_warn.close()
def warning_db_insert():#警报写入函数
	global db_status
	global db_warn
	global db_warn_cursor
	global tmpctl
	global tmp
	global tmp_high
	global tmp_low
	if tmpctl==1:
		temp_time_db=time.strftime("%Y-%m-%d %H:%M:%S")
		if tmp<tmp_low:
			db_insert(temp_time_db,'Low',str(tmp),str(tmp_low))
			#text1.insert(INSERT,'温度过低警报写入数据库\n')
		elif tmp>tmp_high:
			db_insert(temp_time_db,'High',str(tmp),str(tmp_high))
			#text1.insert(INSERT,'温度过高警报写入数据库\n')
def warning_db_insert_threads():#警报写入线程函数
	global db_status
	global db_warn
	global db_warn_cursor
	while True:
		db_status=os.path.exists('warning_record.db')
		db_warn=sqlite3.connect('warning_record.db')
		db_warn_cursor=db_warn.cursor()
		if db_status==False:
			db_init()
		warning_db_insert()
		time.sleep(5)

#主窗体设置
main_window=Tk()
main_window.title('DS18B20监测程序')
main_window_width=800#主窗口宽度
main_window_height=600#主窗口高度
screen_width=main_window.winfo_screenwidth()#屏幕宽度
screen_height=main_window.winfo_screenheight()#屏幕高度
main_window_alignstr='%dx%d+%d+%d'%(main_window_width,main_window_height,(screen_width-main_window_width)/2,(screen_height-main_window_height)/2)#窗体数据
main_window.geometry(main_window_alignstr)#窗体居中
main_window.resizable(width=False,height=False)#主窗体更改大小设置
temp_icon = open("temp.ico", "wb+")#临时写入icon
temp_icon.write(base64.b64decode('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'))
# temp_icon.write(base64.b64decode('粘贴窗体图标编码内容'))
temp_icon.close()#解除temp_icon对于temp.ico占用
main_window.iconbitmap("temp.ico")#调用临时icon生成窗体图标，免除外部资源打包
os.remove("temp.ico")  #删除临时icon文件

#label控件设置
#温度显示label控件设置
label_tmp=Label(main_window, text="无温度数据,请检查温度设备！",font=('微软雅黑',35))
label_tmp.pack()
label_tmp.place(x=0,y=0)
#温度范围label控件设置
label_tmp_notice=Label(main_window, text="报警温度范围设置(℃)",font=('黑体',20))
label_tmp_notice.pack()
label_tmp_notice.place(x=50,y=80)
#状态显示label控件设置
label_status=Label(main_window, text="设备状态",font=('黑体',20))
label_status.pack()
label_status.place(x=430,y=80)
#温度上限label控件设置
label_tmp_up=Label(main_window, text="温度上限",font=('黑体',15))
label_tmp_up.pack()
label_tmp_up.place(x=80,y=120)
#温度下限label控件设置
label_tmp_down=Label(main_window, text="温度下限",font=('黑体',15))
label_tmp_down.pack()
label_tmp_down.place(x=200,y=120)

#scale控件设置
#温度上限scale控件设置
scale_up=Scale(main_window, from_=100, to=0, orient=VERTICAL, tickinterval=1, length=250)
scale_up.pack()
scale_up.place(x=80,y=150)
#温度下限scale控件设置
scale_down=Scale(main_window, from_=100, to=0, orient=VERTICAL, tickinterval=1, length=250)
scale_down.pack()
scale_down.place(x=200,y=150)

#button控件设置
#温度范围检测打开button控件设置
button_tmpctl_on=Button(main_window, text="报警打开", command=tmpctl_on, width=10, height=2)
button_tmpctl_on.pack()
button_tmpctl_on.place(x=380,y=400)
#温度范围检测关闭button控件设置
button_tmpctl_off=Button(main_window, text="报警关闭", command=tmpctl_off, width=10, height=2)
button_tmpctl_off.pack()
button_tmpctl_off.place(x=530,y=400)
#串口检测button控件设置
button_uart_scan=Button(main_window, text="串口检测", command=com_scan, width=10, height=2)
button_uart_scan.pack()
button_uart_scan.place(x=380,y=500)
#微信登录button控件设置
button_tmpctl_off=Button(main_window, text="微信登录", command=usr_login, width=10, height=2)
button_tmpctl_off.pack()
button_tmpctl_off.place(x=530,y=500)

#text控件设置
#状态text控件设置
text1=scrolledtext.ScrolledText(main_window,width=40,height=20)
text1.pack()
text1.place(x=360,y=120)

#线程设置
#串口温度读取线程设置
com_read_threading=threading.Thread(target=com_read_threads,name='com_read_thread')
com_read_threading.daemon =True
com_read_threading.start()
#串口温度警报显示线程设置
warning_display_threading=threading.Thread(target=warning_display_threads,name='warning_display_thread')
warning_display_threading.daemon =True
warning_display_threading.start()
#串口温度警报微信线程设置
warning_wechat_threading=threading.Thread(target=warning_wechat_threads,name='warning_wechat_thread')
warning_wechat_threading.daemon =True
warning_wechat_threading.start()
#串口温度警报数据库线程设置
warning_db_threading=threading.Thread(target=warning_db_insert_threads,name='warning_db_thread')
warning_db_threading.daemon =True
warning_db_threading.start()
main_window.mainloop()
