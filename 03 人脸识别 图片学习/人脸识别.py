"""
一、我有的东西：
1、1000张左右以考号为文件名的学生正面相片（报考和毕业照使用，工作需要获得，个人节操保证不外传）
2、两个bit，两个Go，只要其中任意一个即可。
3、一张容量为64G的SD卡、读卡器。使用FAT32格式化。现在windows系统都不支持FAT32格式，可以使用格式工具，大白菜等装机工具自带有。
4、例程（https://blog.sipeed.com/p/1338.html）复制。github也可复制，但备注没那么详细
5、三个模型在https://www.maixhub.com/index/index/detail/id/235.html下载，此页面有详细说明怎样下载。
    这三个模型下载下来后是打包好的文件。不用管它，直接烧进flash。烧完后，好像固件版本是0.4.0，可以用，但最好再烧一次最新版mini固件。

二、实现思路：
1、处理已有相片，主要是处理尺寸问题。kpu可以处理的相片是320*240，如果不是这个尺寸，会报"format error"的错误，因此要把原图缩放到合适尺寸。
    缩放的时候要等比例缩放，否则人脸变形就识别不准了。缩放后大概率铺不满320*240，因为人的脸大多不是扁的。可以把整个图复制到320*240的背景图上。把处理好的图片放时一个文件夹
2、sd卡装进读卡器，插入电脑。把第一步处理好的图片文件夹放进sd卡。把sd卡插到bit或者Go。
3、进入IDE修改代码。主要是用SD卡的图片代替从摄像头获取的图片。使用自己的图片要注意加多一行：img.pix_to_ai()，否则KPU会报格式错误。（厂家技术支持吴工告诉我的）
4、获取文件名作为识别结果的ID号，和人脸识别结果用txt文件保存在SD卡中。我是将id和人脸识别的结果分别保存在不同的txt文件里。
5、人脸识别的结果是二进制码，怎样把它保存进txt文件又是个问题。Sipeed吴工又给我支招：用base64编码保存二进制码转换成字符。用的时候再取出来转换成二进制码。使用ubinascii.b2a_base64自带函数
6、附上主要代码：
"""
   
anchor = (1.889, 2.5245, 2.9465, 3.94056, 3.99987, 5.3658, 5.155437, 6.92275, 6.718375, 9.01025) #anchor for face detect
dst_point = [(44,59),(84,59),(64,82),(47,105),(81,105)] #标准面关键点位置。它们是左眼，右眼，鼻子，左嘴角，右嘴角
a = kpu.init_yolo2(task_fd, 0.5, 0.3, 5, anchor) #init人脸检测模型
pics_directory_exists = 0
feature_file_exists = 0
for v in os.ilistdir('/sd'):#检查sd中的密钥目录或文件卡.sd卡的格式应为fat32
    if v[0] == 'pics' and v[1] == 0x4000:#0x4000 是目录
        pics_directory_exists = 1
    if v[0] == 'features.txt' and v[1] == 0x8000:#0x8000 是文件
        feature_file_exists = 1

record_ftrs = []
ids = []

if not pics_directory_exists:
    sendMsgToCustomer((0,'',0,'No picture directory'))
    return

img_lcd=image.Image() # 设置显示buf
img_face=image.Image(size=(128,128)) #设置 128 * 128 人脸图片buf
a=img_face.pix_to_ai() # 将图片转为kpu接受的格式

for p in list(os.listdir('/sd/pics')):
    record_ftr=[] #空列表 用于存储当前196维特征

    member_id,ext = p.split('.')#p=16200001.jpg, so just split with . and get member id

    ids.append(member_id)

    img = image.Image('/sd/pics/' + p) #从SD卡文件夹中获取一张图片

    a = lcd.display(img) #刷屏显示

    clock.tick() #记录时刻，用于计算帧率
    a = img.pix_to_ai()
    code = kpu.run_yolo2(task_fd, img) # 运行人脸检测模型，获取人脸坐标位置
    if code: # 如果检测到人脸
        for i in code: # 迭代坐标框
            # Cut face and resize to 128x128
            a = img.draw_rectangle(i.rect()) # 在屏幕显示人脸方框
            face_cut=img.cut(i.x(),i.y(),i.w(),i.h()) # 裁剪人脸部分图片到 face_cut
            face_cut_128=face_cut.resize(128,128) # 将裁出的人脸图片 缩放到128 * 128像素
            a=face_cut_128.pix_to_ai() # 将猜出图片转换为kpu接受的格式
            fmap = kpu.forward(task_ld, face_cut_128) # 运行人脸5点关键点检测模型
            plist=fmap[:] # 获取关键点预测结果
            le=(i.x()+int(plist[0]*i.w() - 10), i.y()+int(plist[1]*i.h())) # 计算左眼位置， 这里在w方向-10 用来补偿模型转换带来的精度损失
            re=(i.x()+int(plist[2]*i.w()), i.y()+int(plist[3]*i.h())) # 计算右眼位置
            nose=(i.x()+int(plist[4]*i.w()), i.y()+int(plist[5]*i.h())) #计算鼻子位置
            lm=(i.x()+int(plist[6]*i.w()), i.y()+int(plist[7]*i.h())) #计算左嘴角位置
            rm=(i.x()+int(plist[8]*i.w()), i.y()+int(plist[9]*i.h())) #右嘴角位置
            a = img.draw_circle(le[0], le[1], 4)
            a = img.draw_circle(re[0], re[1], 4)
            a = img.draw_circle(nose[0], nose[1], 4)
            a = img.draw_circle(lm[0], lm[1], 4)
            a = img.draw_circle(rm[0], rm[1], 4) # 在相应位置处画小圆圈
            # align face to standard position
            src_point = [le, re, nose, lm, rm] # 图片中 5 坐标的位置
            T=image.get_affine_transform(src_point, dst_point) # 根据获得的5点坐标与标准正脸坐标获取仿射变换矩阵
            a=image.warp_affine_ai(img, img_face, T) #对原始图片人脸图片进行仿射变换，变换为正脸图像
            a=img_face.ai_to_pix() # 将正脸图像转为kpu格式
            #a = img.draw_image(img_face, (128,0))
            del(face_cut_128) # 释放裁剪人脸部分图片
            # calculate face feature vector
            fmap = kpu.forward(task_fe, img_face) # 计算正脸图片的196维特征值
            feature=kpu.face_encode(fmap[:]) #获取计算结果
            record_ftr = feature
            pl =  ubinascii.b2a_base64(feature)
            record_ftrs.append(pl) #将当前特征添加到已知特征列表
    del(img)
    del(record_ftr)
ff1 = open('/sd/features.txt','w')
for u in range(len(record_ftrs)):
    ff1.write(record_ftrs[u])
    ff1.write('#')
ff1.close()

ff2 = open('/sd/ids.txt','w')
for c in range(len(ids)):
    ff2.write(ids[c])
    ff2.write('#')
ff2.close()

print('store face feature completed')