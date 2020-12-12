# 计算NDVI，多波段的数据，nir为近红外波段在数据的位置，Red同理！

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
    # new_data = np.array(im_data)  # 将数据写成数组，对应栅格矩阵
    print(im_data.dtype.name)
    print(im_data.shape)
    # print(im_data)
    del dataset
    return proj, geotrans, im_data,im_data.shape


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
    name,path = openfile()
    os.chdir(path)
    nir = int(input("Nir:"))
    red = int(input("Red:"))
    proj, geotrans, im_data,shape = opentif(name)
    NDVI_data = (im_data[nir - 1]-im_data[red - 1])/(im_data[nir - 1]+im_data[red - 1])
    WriteTif("ndvi.tif", proj, geotrans, im_data, NDVI_data)
