# 最小距离监督分类，要有一个使用tif格式的样本，以及一样大小范围的影像。
# 影像需要是多波段的，单波段的出错了，不知道为啥！
# 用到了gdal os numpy  tkinter

from osgeo import gdal
import os
import numpy as np


class GRID:
    # 读图像文件
    def read_img(self, filename):
        dataset = gdal.Open(filename)  # 打开文件

        im_width = dataset.RasterXSize  # 栅格矩阵的列数
        im_height = dataset.RasterYSize  # 栅格矩阵的行数

        im_geotrans = dataset.GetGeoTransform()  # 仿射矩阵
        im_proj = dataset.GetProjection()  # 地图投影信息
        im_data = dataset.ReadAsArray(0, 0, im_width, im_height)  # 将数据写成数组，对应栅格矩阵
        del dataset
        return im_proj, im_geotrans, im_data

    # 写文件，以写成tif为例
    def write_img(self, filename, im_proj, im_geotrans, new_data):
        if 'int8' in new_data.dtype.name:
            datatype = gdal.GDT_Byte
        elif 'int16' in new_data.dtype.name:
            datatype = gdal.GDT_UInt16
        else:
            datatype = gdal.GDT_Float32
        print(new_data.dtype.name)
        # 判读数组维数，并获得波段数、高、宽
        if len(new_data.shape) == 3:
            im_bands, im_height, im_width = new_data.shape
        else:
            im_bands, (im_height, im_width) = 1, new_data.shape

        # 创建文件
        driver = gdal.GetDriverByName("GTiff")  # 数据类型必须有，因为要计算需要多大内存空间
        dataset = driver.Create(filename, im_width, im_height, im_bands, datatype)  # 创建TIF文件
        dataset.SetGeoTransform(im_geotrans)  # 仿射变换参数
        dataset.SetProjection(im_proj)  # 投影
        dataset.GetRasterBand(1).WriteArray(new_data)
        # for i in range(im_bands):
        #     dataset.GetRasterBand(i + 1).WriteArray(im_data[i])  # 写入新的栅格矩阵数据
        del dataset

# 用tkinter打开一个文件管理器，选择要分类的影像
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

# 读取样本
def getsample(sampledata,test_data):
    centerlen = test_data.shape[0] + 2
    MeansCenter = [None]
    for i in range(len(MeansCenter)):
        MeansCenter[i] = [None] * centerlen
    for i in range(0, sampledata.shape[0]):
        for j in range(0, sampledata.shape[1]):
            if sampledata[i, j] != 0:
                pd = 0
                n = 0
                while n < len(MeansCenter) and pd == 0:
                    if MeansCenter[n][0] == sampledata[i, j]:
                        pd = 1
                        MeansCenter[n][1] = MeansCenter[n][1] + 1
                        m = 0
                        for k in range(2,centerlen):
                            MeansCenter[n][k] = int(MeansCenter[n][k] + im_data[m][i][j])
                            m = m + 1
                    elif MeansCenter[n][0] != sampledata[i, j]:
                        pd = 0
                    n = n + 1
                if pd == 0:
                    MeansCenter.append([sampledata[i, j]])
                    for m in range(1,centerlen):
                        MeansCenter[len(MeansCenter)-1].append(0)
    del MeansCenter[0]
    # print(MeansCenter)
    return MeansCenter

# 计算分类中心
def getcenter(center):
    Meancenter = center
    for i in range(0,len(Meancenter)):
        Meancenter[i][0] = center[i][0]
        Meancenter[i][1] = center[i][1]
        for j in range(2,len(Meancenter[i])):
            Meancenter[i][j] = (center[i][j] / center[i][1])
    print(Meancenter)
    return Meancenter

# 排序 
def bullersort(classes,diction):
    for i in range(0,len(diction)):
        for j in range(0,len(diction)-1):
            if diction[j]>diction[j+1]:
                dtemp = diction[j+1]
                diction[j+1] = diction[j]
                diction[j] = dtemp
                ctemp = classes[j+1]
                classes[j+1] = classes[j]
                classes[j] = ctemp

# 计算距离，并分类
def classfity(im_data, new_data, MeansCenter):
    height = im_data.shape[1]
    width = im_data.shape[2]

    for i in range(0,height-1):
        for j in range(0,width-1):
            diction = [0] * len(MeansCenter)
            classes = [0] * len(MeansCenter)
            for k in range(0, len(classes)):
                classes[k] = MeansCenter[k][0]
            for n in range(0,len(MeansCenter)):
                k = 0
                for m in range(2,len(MeansCenter[0])):
                    diction[n] = diction[n] + int(abs(MeansCenter[n][m] - im_data[k][i,j]))
                    k = k + 1
            bullersort(classes,diction)
            print(classes,diction)
            new_data[i][j] = classes[0]
    return new_data


if __name__ == '__main__':
    name ,path = openfile()
    os.chdir(path)
    img = GRID()
    im_proj, im_geotrans, im_data = img.read_img(name)
    sample = GRID()
    sample_proj, sample_geotrans, sample_data=sample.read_img("test.tif")   #这里要是样本
    center = getsample(sample_data,im_data)
    sampleCenter = getcenter(center)

    newdata = sample_data
    classfity(im_data,newdata,sampleCenter)

    img.write_img("testclass2.tif",im_proj,im_geotrans,newdata)
