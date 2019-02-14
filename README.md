# Data-Visualization-PJ

庄吓海老师数据可视化PJ，具体内容见pdf文件。主程序为GUI.py。操作系统为win7。python第三方库为vtk8.1.0。

我们主要运用了python中的vtk和pyqt5设计出一个交互界面。用户通过拖动控制点实现3D物体的形变，并且物体的形变数据可以保存为ffd文件。使用的算法是b样条函数和贝塞尔函数。

初始交互界面中默认背景是一个iphone6：
![Image text](https://github.com/James0231/Data-Visualization-PJ/blob/master/img-folder/1.png)

然后在上方菜单栏中选择add obj file可以导入obj文件，我们随便选择一张，例如：zxh-ape.obj，效果如下
在菜单栏选择导入ffd形变文件之后，会生成包围住物体的红色控制点，效果如下：
![Image text](https://github.com/James0231/Data-Visualization-PJ/blob/master/img-folder/2.png)
