from machine import UART,Timer
from fpioa_manager import fm

#映射串口引脚
fm.register(6, fm.fpioa.UART1_RX, force=True)
fm.register(7, fm.fpioa.UART1_TX, force=True)

#初始化串口
uart = UART(UART.UART1, 115200, read_buf_len=4096)




# 协议发送
def Pact_Send(a,b,c):
    pactx=[]  # 空列表 用于存放数据
    sc=0  # 和校验

    pactx.append(0xAA)  # 帧头
    pactx.append(0xAA)  # 帧头

    pactx.append(8)  # 数据长度 字节

    pactx.append((a>>24) & 0xFF)  # 数据拆分 高位在前
    pactx.append((a>>16) & 0xFF)
    pactx.append((a>>8)  & 0xFF)
    pactx.append((a>>0)  & 0xFF)

    pactx.append((b>>24) & 0xFF)
    pactx.append((b>>16) & 0xFF)
    pactx.append((b>>8)  & 0xFF)
    pactx.append((b>>0)  & 0xFF)

    pactx.append((c>>24) & 0xFF)
    pactx.append((c>>16) & 0xFF)
    pactx.append((c>>8)  & 0xFF)
    pactx.append((c>>0)  & 0xFF)

    for i in pactx:  # 和校验计算
        sc+=i
    pactx.append(sc & 0xFF)

    for i in pactx:  # 发送
        uart.write(bytearray([i]))




# 协议接受
rei=0
rex=[]
def Pact_Receive(data):
    global rei
    pact_a=0
    pact_b=0
    pact_c=0

    if rei<2:  # 帧头
        if data==0xAA:
            rei+=1
        else:
            rei=0
    else:
        if rei==2:  # 数据帧长度位 字节
            rei=3
            rex.append(data)
        else:
            if rei<rex[0]+3:  # 接受数据位和校验位
                rei+=1
                rex.append(data)
            else:
                rex.append(data)
                sc=0
                for i in rex[0:-2]:  # 计算校验位
                    sc+=i
                sc=sc & 0xFF
                print(sc)
                if sc == rex[-1]:  # 校验成功
                    x=1+2  # 1 + 数据长度
                    pact_a=0
                    for i in range(0+1,x):  # 第一个数据位
                        pact_a<<=8
                        pact_a|=rex[i]

                    y=x+2  # x + 数据长度
                    pact_b=0
                    for i in range(x,y):
                        pact_b<<=8
                        pact_b|=rex[i]

                    y=x+4  # x + 数据长度
                    pact_c=0
                    for i in range(x,y):
                        pact_c<<=8
                        pact_c|=rex[i]

                    rei=0
                    rex.clear()
                    return 1,pact_a,pact_b,pact_c

                rei=0
                rex.clear()

    return 0,pact_a,pact_b,pact_c

if __name__=='__main__':
    while 1:
        #Pact_Send(0xaabb,0,0)

        txt=uart.read()
        if txt:
            print(int(txt))

