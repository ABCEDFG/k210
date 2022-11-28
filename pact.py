from machine import UART,Timer
from fpioa_manager import fm

#ӳ�䴮������
fm.register(6, fm.fpioa.UART1_RX, force=True)
fm.register(7, fm.fpioa.UART1_TX, force=True)

#��ʼ������
uart = UART(UART.UART1, 115200, read_buf_len=4096)




# Э�鷢��
def Pact_Send(a,b,c):
    pactx=[]  # ���б� ���ڴ������
    sc=0  # ��У��

    pactx.append(0xAA)  # ֡ͷ
    pactx.append(0xAA)  # ֡ͷ

    pactx.append(8)  # ���ݳ��� �ֽ�

    pactx.append((a>>24) & 0xFF)  # ���ݲ�� ��λ��ǰ
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

    for i in pactx:  # ��У�����
        sc+=i
    pactx.append(sc & 0xFF)

    for i in pactx:  # ����
        uart.write(bytearray([i]))




# Э�����
rei=0
rex=[]
def Pact_Receive(data):
    global rei
    pact_a=0
    pact_b=0
    pact_c=0

    if rei<2:  # ֡ͷ
        if data==0xAA:
            rei+=1
        else:
            rei=0
    else:
        if rei==2:  # ����֡����λ �ֽ�
            rei=3
            rex.append(data)
        else:
            if rei<rex[0]+3:  # ��������λ��У��λ
                rei+=1
                rex.append(data)
            else:
                rex.append(data)
                sc=0
                for i in rex[0:-2]:  # ����У��λ
                    sc+=i
                sc=sc & 0xFF
                print(sc)
                if sc == rex[-1]:  # У��ɹ�
                    x=1+2  # 1 + ���ݳ���
                    pact_a=0
                    for i in range(0+1,x):  # ��һ������λ
                        pact_a<<=8
                        pact_a|=rex[i]

                    y=x+2  # x + ���ݳ���
                    pact_b=0
                    for i in range(x,y):
                        pact_b<<=8
                        pact_b|=rex[i]

                    y=x+4  # x + ���ݳ���
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

