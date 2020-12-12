from osgeo import gdal
import os
import numpy as np


class Convo:
    def read_img(self, filename):  # 读取TIF
        dataset = gdal.Open(filename)  # 打开文件

        im_width = dataset.RasterXSize  # 栅格矩阵的列数
        im_height = dataset.RasterYSize  # 栅格矩阵的行数

        im_geotrans = dataset.GetGeoTransform()  # 仿射矩阵
        im_proj = dataset.GetProjection()  # 地图投影信息
        im_data = dataset.ReadAsArray(0, 0, im_width, im_height)  # 将数据写成数组，对应栅格矩阵
        new_data1 = np.array(im_data)  # 新矩阵，用于储存卷积后的栅格
        print(im_data.dtype.name)
        print(im_data.shape)
        # print(im_data)
        del dataset
        return im_proj, im_geotrans, im_data, new_data1, im_width, im_height  # 返回相关参数

    def convolotion(self, He, im_data, new_data, im_width, im_height):
        list1 = []
        list2 = []
        for i in range(0, im_height):
            list1.append(i)
        for j in range(0, im_width):
            list2.append(j)
        for k in range(0, 4):  #遍历每一个波段
            for i in range(0, im_height):
                for j in range(0, im_width):  # 遍历每一个点
                    sum = 0
                    num = 1
                    for n in range(-1, 1):
                        for m in range(-1, 1):  # 遍历卷积核
                            if i + n not in list1 or j + m not in list2:
                                sum = sum + 0
                            else:
                                sum = sum + im_data[k][i + n][j + m] * He[n + 1][m + 1]  # 8邻域加权相乘相加
                                num = num + 1
                    new_data[k][i][j] = int(sum / num)    # 新的像素值
        print("卷积完成")
        print(new_data)
        return new_data

    # 写文件，以写成tif为例
    def WriteTif(self, filename, im_proj, im_geotrans, im_data, new_data):
        # 判断栅格数据的数据类型
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
        dataset = driver.Create(filename, im_width, im_height, im_bands,datatype)  # 创建TIF文件
        dataset.SetGeoTransform(im_geotrans)  # 仿射变换参数
        dataset.SetProjection(im_proj)  # 投影
        # dataset.GetRasterBand(1).WriteArray(new_data)
        for i in range(im_bands):
            dataset.GetRasterBand(i + 1).WriteArray(new_data[i])  # 写入新的栅格矩阵数据
        del dataset


if __name__ == "__main__":
    os.chdir(r'D:\Desktop\S2A_MSIL1C_20200810T030551_N0209_R075_T50TMK_20200810T050321.SAFE')  # 图像所在文件夹
    He = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]])  # 设置卷积核
    Filter = Convo()
    proj, geotrans, data, new_data1, im_width, im_height = Filter.read_img('clip1.tif')  # 读数据
    new_data = Filter.convolotion(He, data, new_data1, im_width, im_height)  # 卷积运算
    Filter.WriteTif('lap2.tif', proj, geotrans, data, new_data)  # 写数据
