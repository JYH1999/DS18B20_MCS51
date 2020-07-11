#include<reg52.h>
#include<intrins.h>
#include<stdio.h>
//fosc@11.0592MHz
#define uchar unsigned char
#define uint unsigned int
sbit ds=P2^2;           //定义ds18b20数据端口
float tmp_float=0;//温度变量
uint flag=0;//标志变量，用于清除不正常数据
void delay(uint z)//延时函数
{
	uint x,y;
	for(x=z;x>0;x--)
		for(y=110;y>0;y--);
}
void ds_init()//ds18b20初始化
{
	uint i;
	ds=1;
	_nop_();//短暂延时
	ds=0;
	i=103;
  while(i>0)
		i--;//；延时
	ds=1;
	i=4;
  while(i>0)
		i--;//延时
}
bit readbit()       //读取1位数据
{
  uint i=0;
  bit temp_bit;
	ds=1;
	_nop_();
	ds=0;
	i++;//延时
	ds=1;
	i++;
	i++;//延时
	temp_bit=ds;//读取位数据
	i=8;
	while(i>0)
		i--;
	return temp_bit;
}
uchar readbyte()//读取1字节数据
{
	uchar temp_byte,i,j;
	temp_byte=0;
	for(i=1;i<=8;i++)
  {
    j=readbit();
    temp_byte=(j<<7)|(temp_byte>>1);   //将位整合为字节
  }
  return(temp_byte);
}
void writebyte(uchar temp_data)   //向ds18b20写1字节
{
  uint i;
  uchar j;
  bit bit_out;
  for(j=1;j<=8;j++)
  {
    bit_out=temp_data&0x01;
    temp_data=temp_data>>1;
    if(bit_out)     //写1
    {
      ds=0;
      i++;
			i++;//延时
      ds=1;
      i=8;
			while(i>0)
				i--;
			ds=1;
    }
    else
    {
      ds=0;       //写0
      i=8;
			while(i>0)
				i--;
      ds=1;
			i++;
			i++;//延时
    }

  }
	ds=1;
}
void tmp_init(void)  //DS18B20开始读取数据
{
  ds_init();
  delay(2);
  writebyte(0xcc);  // 跳过ROM
  writebyte(0x44);  // 启动温度转换
}

float get_tmp()               //获得温度
{
  uchar a,b;
	float temp_tmp_float;
	uint temp;
  ds_init();
  delay(2);
  writebyte(0xcc);
  writebyte(0xbe);
  a=readbyte();//读低8位
  b=readbyte();//读高8位
  temp=b;
  temp<<=8;             //整合两个字节
  temp=temp|a;
  temp_tmp_float=temp*0.0625;
  return temp_tmp_float;
}
void com_init()//串口初始化
{
	TMOD=0x20;
	PCON=0x00;
	SCON=0x50;
	TH1=0xfd;
	TL1=0xfd;
	TR1=1;
}
void send_tmp(char *string_in)//发送字符串
{
	do
	{
		SBUF=*string_in++;
		while(!TI);
		TI=0;
	}while(*string_in);
}
void main()
{
	uchar tmp_out[4];
	com_init();

	while(1)
	{
		tmp_init();
		tmp_float=get_tmp();
		if(flag<=2)//用于清除单片机刚启动时产生的非法温度值
		{
			flag++;
			delay(500);
			continue;
		}
		sprintf(tmp_out,"%f",tmp_float);//把浮点温度值转换为字符
		send_tmp(tmp_out);//发送字符温度值
		delay(500);
	}
}