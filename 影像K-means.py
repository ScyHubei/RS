from osgeo import gdal
import os
import numpy as np
import math


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

class ReClass:

    # 读取tif
    def ReadTif(self, filename):  # 读取TIF
        dataset = gdal.Open(filename)  # 打开文件

        im_width = dataset.RasterXSize  # 栅格矩阵的列数
        im_height = dataset.RasterYSize  # 栅格矩阵的行数

        im_geotrans = dataset.GetGeoTransform()  # 仿射矩阵
        im_proj = dataset.GetProjection()  # 地图投影信息
        im_data = dataset.ReadAsArray(0, 0, im_width, im_height)
        new_data = np.array(im_data)  # 将数据写成数组，对应栅格矩阵
        print(im_data.dtype.name)
        # print(im_data.shape)
        # print(im_data)
        del dataset
        return im_proj, im_geotrans, im_data, new_data  # 返回相关参数

    # 线性拉伸到0-255
    def XianXls(self, data):
        max = data.max()
        min = data.min()
        jicha = int(max - min)
        im_height = data.shape[0]
        im_width = data.shape[1]
        for i in range(im_height):
            for j in range(im_width):
                data[i][j] = int((data[i][j] - min) * 255 / jicha)
                if data[i][j] == 0:
                    data[i][j] = 1
        return data

    # 第一次的聚类中心
    def firsrcenter(self, data, c):
        # 聚类中心在一个c*4的矩阵中储存，其中[0]为聚类中心的像素点，[1]为每一个点到此聚类中心的距离，
        # [2]为本次迭代中属于此中心像素点的个数，[3]为属于此中心像素点的总和。
        MeansCenter = [None] * c
        for i in range(len(MeansCenter)):
            MeansCenter[i] = [0] * 4
        max = data.max()
        min = data.min()
        cha = int((max - min) / c)
        fir = cha + min
        for i in range(len(MeansCenter)):
            MeansCenter[i][0] = fir
            MeansCenter[i][1] = 0
            MeansCenter[i][2] = 0
            MeansCenter[i][3] = 0
            fir = fir + cha
        print(MeansCenter)
        return MeansCenter

    # K-means迭代
    def KMeansTif(self, im_data, new_data, km, MeansCenter):
        for k in range(0, km):
            print("第", k, "次中心", MeansCenter)
            im_height = im_data.shape[0]
            im_width = im_data.shape[1]
            print(im_width, im_height)
            # 遍历图像，计算距离
            for i in range(im_height):
                for j in range(im_width):
                    for c in range(len(MeansCenter)):
                        MeansCenter[c][1] = abs((MeansCenter[c][0] - im_data[i][j]))

                    def takeSecond(MeansCenter):
                        return MeansCenter[1]

                    # 排序
                    MeansCenter.sort(key=takeSecond)
                    if k == km - 1:
                        new_data[i][j] = MeansCenter[0][0]  # 生成新图像
                    MeansCenter[0][2] = MeansCenter[0][2] + 1  # 记录同一个的次数
                    MeansCenter[0][3] = MeansCenter[0][3] + im_data[i][j]  # 计算总和

            for i in range(0, len(MeansCenter)):
                if MeansCenter[i][2] != 0:
                    MeansCenter[i][0] = int(MeansCenter[i][3] / MeansCenter[i][2])  # 计算新中心
                for j in range(1, 4):
                    MeansCenter[i][j] = 0

        return new_data

    # 输出
    def WriteTif(self, filename, im_proj, im_geotrans, im_data, new_data):
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
    cl = ReClass()
    name,path = openfile()
    os.chdir(path)  # 图像所在文件夹
    proj, geot, data, newdata = cl.ReadTif(name)
    data = cl.XianXls(data)
    c = int(input("类别个数"))
    d = int(input("迭代次数"))
    classname = input(str("请输入分类文件名"))
    MeansCenter = cl.firsrcenter(data, c)
    newdata1 = cl.KMeansTif(data, newdata, d, MeansCenter)
    print(classname)
    cl.WriteTif(classname, proj, geot, data, newdata1)
