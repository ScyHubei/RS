# 通过开窗获得窗口内的像素，并对窗口矩阵计算灰度共生矩阵，并选择测度返回出纹理图像。
# 开窗前要进行图像的降级，使用的是线性拉伸的方法进行降级。
# 执行程序前最好对图像做一个直方图均衡化。
#  单波段    遥感影像越小越好，程序效率极低！！！！！




from osgeo import gdal
import os
import numpy as np


def openfile():
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename()
    print(file_path)
    a = file_path.split("/")
    b = str()
    name = a[len(a) - 1]
    for i in range(len(a) - 1):
        if i < (len(a) - 2):
            b = str(b) + str(a[i]) + "\\"
        else:
            b = str(b) + str(a[i])
    filepath = b
    return name, filepath


def opentif(filename):
    dataset = gdal.Open(filename)

    width = dataset.RasterXSize
    height = dataset.RasterYSize

    geotrans = dataset.GetGeoTransform()  # 仿射矩阵

    proj = dataset.GetProjection()  # 地图投影信息
    im_data = dataset.ReadAsArray(0, 0, width, height)
    new_data = np.array(im_data)  # 将数据写成数组，对应栅格矩阵
    print(im_data.dtype.name)
    print(im_data.shape)
    # print(im_data)
    del dataset
    return proj, geotrans, im_data,im_data.shape,new_data


def stch(data,bit):
    max = data.max()
    min = data.min()
    # print(max,min)
    jicha = int(max - min)
    im_height = data.shape[0]
    im_width = data.shape[1]
    for i in range(im_height):
        for j in range(im_width):
            data[i][j] = int((data[i][j] - min) * bit / jicha)
            if data[i][j] >= bit:
                # print(data[i][j])
                data[i][j] = bit-1
    # print(data)
    return data


def getGLCM(tempdata, bit, number,jd):  # 灰度共生矩阵
    GLCM = [0] * bit
    for z in range(len(GLCM)):
        GLCM[z] = [0] * bit
    for i in range(0, number-1):
        for j in range(0, number-1):
            if tempdata[i+1][j+1] != None:
                a = tempdata[i][j]
                if jd == 1:
                    b = tempdata[i][j+1]     # 通过改变b的索引控制灰度共生矩阵的方向
                elif jd == 2:
                    b = tempdata[i+1][j+1]
                elif jd == 3:
                    b = tempdata[i+1][j]
                else:
                    print("方向选择错误")
                if a > bit-1:
                    a = bit-1
                if b > bit-1:
                    b = bit-1
                # print(a,b)
                GLCM[a][b] = GLCM[a][b] + 1
    # print(GLCM)
    return GLCM


def getasm(GLCM, bit):  # 能量
    asm = 0
    for i in range(bit):
        for j in range(bit):
            asm = asm + (GLCM[i][j])**2
    print(asm)
    return asm


def getent(GLCM, bit):# 熵
    import math
    ent = 0
    for i in range(bit):
        for j in range(bit):
            if GLCM[i][j] != 0:
                ent = ent + (GLCM[i][j]*(math.log(GLCM[i][j],10)))
    print(ent)
    return ent


def getidm(GLCM, bit): # 同质性
    idm = 0
    for i in range(bit):
        for j in range(bit):
            if i-j !=0:
                idm = idm + GLCM[i][j]/(1+(i-j)**2)
    print(idm)
    return idm


def getcon(GLCM, bit):  # 对比度
    con = 0
    for i in range(bit):
        for j in range(bit):
            con = con + (GLCM[i][j]*float((i-j)**2))
    print(con)
    return con


def chuank(data, shape, newdata, number, tz, jd):
    list1 = []
    for i in range(0, shape[0]):
        list1.append(i)
    list2 = []
    for i in range(0, shape[1]):
        list2.append(i)
    for i in range(0, shape[0]):
        for j in range(0, shape[1]):
            temp = [0]*number
            for z in range(len(temp)):
                temp[z] = [0]*number
            x = int(number/2) + 1 - number
            y = number-int(number/2)
            for m in range(x, y):   # 提取窗口
                for n in range(x, y):
                    # print(data[i+m][j+n])
                    # print("---------")
                    if i+m not in list1 or j+n not in list2:  # 判断超限情况
                        temp[m + abs(m)][n + abs(m)] = 0
                    else:
                        temp[m + abs(m)][n + abs(m)] = data[i + m][j + n]
            print(temp)
            GLCM = getGLCM(temp, bit, number, jd)
            del temp
            if tz == 1:
                ent = getent(GLCM, bit)  # 熵
                newdata[i][j] = ent
            elif tz == 2:
                asm = getasm(GLCM, bit)     # 能 量
                newdata[i][j] = asm
            elif tz == 3:
                idm = getidm(GLCM, bit)   # 同质性
                newdata[i][j] = idm
            elif tz == 4:
                con = getcon(GLCM, bit)   # 对比度
                newdata[i][j] = con
            else:
                print("特征选择错误！")
                break
    return newdata


def WriteTif(filename, im_proj, im_geotrans, im_data, new_data):
    # 判断栅格数据的数据类型
    if 'int8' in im_data.dtype.name:
        datatype = gdal.GDT_Byte
    elif 'int16' in im_data.dtype.name:
        datatype = gdal.GDT_UInt16
    else:
        datatype = gdal.GDT_Float32
    print(im_data.dtype.name)
    # 判读数组维数，并获得波段数、高、宽
    if len(im_data.shape) == 3:
        im_bands, im_height, im_width = im_data.shape
    else:
        im_bands, (im_height, im_width) = 1, im_data.shape

    # 创建文件
    driver = gdal.GetDriverByName("GTiff")  # 数据类型必须有，因为要计算需要多大内存空间
    dataset = driver.Create(filename, im_width, im_height, im_bands, datatype)  # 创建TIF文件
    dataset.SetGeoTransform(im_geotrans)  # 仿射变换参数
    dataset.SetProjection(im_proj)  # 投影
    dataset.GetRasterBand(1).WriteArray(new_data)
    # for i in range(im_bands):
    #     dataset.GetRasterBand(i + 1).WriteArray(im_data[i])  # 写入新的栅格矩阵数据
    del dataset

    
if __name__ == '__main__':
    name, path = openfile()  # 打开文件管理器
    os.chdir(path) # 切换路径
    proj, geotrans, im_data, im_data.shape, newdata=opentif(name) # 读取遥感影像
    bit = int(input("级数："))  # 选择降级级数
    number = int(input("窗口大小："))  # 设置窗口大小
    jd = int(input("选择方向：（1：0°；2：45°；3：90°）"))  # 选择方向
    tz = int(input("选择特征值：（1：熵；2：能量；3：同质性；4：对比度）"))   # 选择测度
    stchdata = stch(im_data, bit)   # 使用线性拉伸的方法进行降级
    newdata = chuank(stchdata, im_data.shape, newdata, number, tz, jd)  # 主要执行函数
    WriteTif("shang.tif", proj, geotrans, im_data, newdata)  # 写图像
