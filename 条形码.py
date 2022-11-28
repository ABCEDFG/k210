import sensor
import machine
import image


sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.run(1)
sensor.skip_frames(10)
while True:
    img = sensor.snapshot()
    code = img.find_barcodes([0,0,320,240])
    for i in code:
        code_text = i.payload()
        if(code_text=='11111'):

        elif(code_text=='22222'):
            print(22)
        elif(code_text=='33333'):
            print(33)
