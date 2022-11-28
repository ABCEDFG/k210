import sensor, image, lcd, time
import KPU as kpu
import gc, sys
from Maix import GPIO
from fpioa_manager import fm
def lcd_show_except(e):
    """
    lcd显示异常函数
    :param e:
    :return:
    """
    import uio
    err_str = uio.StringIO()
    sys.print_exception(e, err_str)
    err_str = err_str.getvalue()
    img = image.Image(size=(224,224))
    img.draw_string(0, 10, err_str, scale=1, color=(0xff,0x00,0x00))
    lcd.display(img)

def main(labels = None, model_addr="/sd/m.kmodel", sensor_window=(224, 224), lcd_rotation=0, sensor_hmirror=False, sensor_vflip=False):
    # 相关硬件初始化配置
    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA)
    sensor.set_windowing(sensor_window)
    sensor.set_hmirror(sensor_hmirror)
    sensor.set_vflip(sensor_vflip)
    sensor.run(1)
    lcd.init(type=1)
    lcd.rotation(lcd_rotation)
    lcd.clear(lcd.WHITE)
    if not labels:
        # 加载标签
        with open('labels.txt','r') as f:
            exec(f.read())
    if not labels:
        print("no labels.txt")
        img = image.Image(size=(320, 240))
        img.draw_string(90, 110, "no labels.txt", color=(255, 0, 0), scale=2)
        lcd.display(img)
        return 1
    try:
        # 设置开机图片
        img = image.Image("startup.jpg")
        lcd.display(img)
    except Exception:
        # 开机图片异常处理
        img = image.Image(size=(320, 240))
        img.draw_string(90, 110, "loading model...", color=(255, 255, 255), scale=2)
        lcd.display(img)
    # 	注册io 口12，13，14
    fm.register(12, fm.fpioa.GPIO0)
    fm.register(13, fm.fpioa.GPIO1)
    fm.register(14, fm.fpioa.GPIO2)
    # 将注册引脚设置为高电平
    LED_B = GPIO(GPIO.GPIO0, GPIO.OUT,value=1)
    LED_G = GPIO(GPIO.GPIO1, GPIO.OUT,value=1)
    LED_R = GPIO(GPIO.GPIO2, GPIO.OUT,value=1)
    try:
        task = None
        # 加载模型
        task = kpu.load(model_addr)
        while(True):
            # 摄像头输入
            img = sensor.snapshot()
            t = time.ticks_ms()
            # 模型进行图像预测
            fmap = kpu.forward(task, img)
            t = time.ticks_ms() - t
            plist=fmap[:]
            # 索引标签结果
            pmax=max(plist)
            max_index=plist.index(pmax)
            # 将四种类别分别输出到对应引脚，
            if max_index==0:
                LED_R.value(0)
                LED_G.value(1)
                LED_B.value(1)
            elif max_index==1:
                LED_R.value(1)
                LED_G.value(0)
                LED_B.value(1)
            elif max_index==2:
                LED_R.value(1)
                LED_G.value(1)
                LED_B.value(0)
            elif max_index==3:
                LED_R.value(0)
                LED_G.value(1)
                LED_B.value(0)
            elif max_index==4:
                LED_R.value(0)
                LED_G.value(0)
                LED_B.value(0)
            else:
                pass
            # Lcd输出字符结果
            img.draw_string(0,0, "%.2f : %s" %(pmax, labels[max_index].strip()), scale=2, color=(255, 0, 0))
            img.draw_string(0, 200, "t:%dms" %(t), scale=2, color=(255, 0, 0))
            lcd.display(img)
    except Exception as e:
        raise e
    finally:
        if not task is None:
            kpu.deinit(task)
if __name__ == "__main__":
    try:
        labels = ["harmful", "kitchen", "other", "recoverable", "undetected"]
        main(labels=labels, model_addr="/sd/m.kmodel")
    except Exception as e:
        sys.print_exception(e)
        lcd_show_except(e)
    finally:
        gc.collect()
