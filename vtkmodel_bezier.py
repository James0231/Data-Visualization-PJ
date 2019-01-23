# coding=utf-8
#https://www.kitware.com/products/books/VTKUsersGuide.pdf  vtk的帮助文档。

import vtk
from FFD import obj_reader, FFD_Bezier
import numpy as np
from time import time
from ObjProcessing import resize_poly_data, color_on_points, read_color_from_ffd



class VtkModel_bezier(object):
    def __init__(self, ren=None, iren=None, filename="zxh-ape.obj", RESIZE = 1, COLOR = True, RADISU = 0.01, xl = 4, yl = 4, zl = 4):
        # 参数初始化，参数COLOR表示是否需要上色
        #x1,y1,z1=4表示各个维度有五个控制点
        #RADISU表示控制球的半径大小。
        
        self.ren = ren  #初始化渲染器
        self.iren = iren  
        self.filename = filename
        self.RESIZE = RESIZE
        self.RADISU = RADISU
        self.COLOR = COLOR
        self.xl = xl
        self.yl = yl
        self.zl = zl

        self.ren.SetBackground(0, 0, 0)         # 设置背景颜色为黑色,


        InteractorStyle = vtk.vtkInteractorStyleTrackballCamera()  #用移动摄像头的交互方式
        self.iren.SetInteractorStyle(InteractorStyle)  #这种交互方式可以使用户点击鼠标左键并拖动时从另外角度观察物体。

        self.loadOBJ()   #构造函数，该函数用来读取OBJ文件
        self.drawFace()  #构造函数，该函数用来画脸

        # 根据load进来的物体大小 自适应设置球体的半径大小
        self.RADISU = (self.ffd.max_x - self.ffd.min_x) * self.RADISU  #ffd为FFD类对象。在本文件的110行进行了初始化。

        self.drawControlPoints()   #增加控制点
        self.drawLines()           #在控制点之间连线
        self.addControlPointsObserver()  #这个监听函数用来检查控制点是否移动。

    def ijk2xyz(self, i, j, k):
        """
        i, j, k为控制点在x轴 y轴 z轴方向分别的索引值
        x, y, z为控制点在坐标系中的坐标
        该坐标由ffd算法根据读入进来的物体的大小自动生成 保证控制点为能恰好包裹住物体的长方体
        """
        x, y, z = self.ffd.control_points_location[i][j][k]  #对于每一个控制点，将其索引值变为x，y，z坐标。
        return x, y, z

    def neighbor(self, i, j, k):  #之后要移动控制点，需要将控制点重新与他邻居的这些点连接起来。
        """
        找到第i,j,k号球对应的所有邻居球体的索引值 即:上下左右前后六个点 通过索引值返回即可 记得判断越界
        """
        n = []
        if i > 0:
            n.append((i-1, j, k))
        if i < self.xl:
            n.append((i+1, j, k))
        if j > 0:
            n.append((i, j-1, k))
        if j < self.yl:
            n.append((i, j+1, k))
        if k > 0:
            n.append((i, j, k-1))
        if k < self.zl:
            n.append((i, j, k+1))
        return n



    def loadOBJ(self):
        """
        初始化，加载模型.obj格式文件
        """
        self.reader = vtk.vtkOBJReader()  #用vtk自带的OBJReader来读取
        self.reader.SetFileName(self.filename) #设置读取的文件名。
        self.reader.Update() #不知道为啥要这样。。
        self.data = self.reader.GetOutput()  #将数据储存在data中

    def color(self):
        """
        上色：模型上色，仅对于带有RGB信息的.obj文件有效
        """
        if self.COLORED:  #如果已经上色了，则不做任何事
            return
        else:
            self.data.GetPointData().SetScalars(self.data_color.GetPointData().GetScalars())
            self.COLORED = True
        mapper = vtk.vtkPolyDataMapper() #创建一个可以对PolyData映射的对象
        mapper.SetInputData(self.data)   #将Polydata存储到映射器当中。

        try:
            self.ren.RemoveActor(self.actor)    #去除原先的数据
            self.actor = vtk.vtkActor()         #新建一个vtkActor对象
            self.actor.SetMapper(mapper)        #必须通过映射器才能将数据映射到vtkActor对象中
            self.ren.AddActor(self.actor)       #将这个对象加入到渲染器中。
        except:
            pass

    
    def resize(self, RESIZE):  #老师没要求减采样和调整图片尺寸。。。。。。。。。。。。。。
        """
        调整尺寸，对PolyData进行减采样，仅对于Triangle类型有效
        """
        self.data = resize_poly_data(self.data, RESIZE)
        self.data_color = resize_poly_data(self.data_color, RESIZE)

        self.points = self.data.GetPoints()
        vertices = [self.points.GetPoint(i) for i in range(self.points.GetNumberOfPoints())]
        self.ffd = FFD_Bezier(num_x=self.xl + 1, num_y=self.yl + 1, num_z=self.zl + 1, object_points=vertices,object_file=self.filename)
        self.ffd.initial_ffd()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(self.data)

        self.ren.RemoveActor(self.actor)
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(mapper)
        self.ren.AddActor(self.actor)

    def drawFace(self, COLOR=False, RESIZE=1.0):
        """
        初始化 画出人脸 可以选择是否需要着色以及是否需要压缩图像
        """

        # 深拷贝一份着色PolyData，解决GUI中上色和RESIZE的逻辑冲突 
        self.data_color = vtk.vtkPolyData()
        self.data_color.DeepCopy(self.data)
        self.data_color = color_on_points(self.data_color, read_color_from_ffd(self.filename))
        self.COLORED = False  #默认未上色

        
        if COLOR :  # 如果需要着色的话
            self.color()
        
        if RESIZE != 1:  # 如果需要压缩图像的话
            self.data = resize_poly_data(self.data, RESIZE)
            self.data_color = resize_poly_data(self.data_color, RESIZE)
            
        self.points = self.data.GetPoints()
        vertices = [self.points.GetPoint(i) for i in range(self.points.GetNumberOfPoints())]
        self.ffd = FFD_Bezier(num_x=self.xl + 1, num_y=self.yl + 1, num_z=self.zl + 1, object_points=vertices,object_file=self.filename)
        self.ffd.initial_ffd()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(self.data)

        self.actor = vtk.vtkActor()
        self.actor.SetMapper(mapper)
        self.ren.AddActor(self.actor)


    def drawControlPoints(self):
        """
        生成控制点球体
        """
        
        # 初始化列表 保存每一个控制球体 列表为i*j*k维 因为有i*j*k个球体
        self.spherelist = [[[0 for zcol in range(self.zl+1)] for col in range(self.yl+1)] for row in range(self.xl+1)]
        
        for i, j, k in ((a, b, c) for a in range(self.xl+1) for b in range(self.yl+1) for c in range(self.zl+1)):
            
            sphereWidget = vtk.vtkSphereWidget()  # 定义一个球状体widget
            
            sphereWidget.SetInteractor(self.iren) # 在渲染窗口交互器实例iren实现3D球状体widget

            x, y, z = self.ijk2xyz(i, j, k)        # 从索引值对应到真实空间中的xyz坐标
            sphereWidget.SetCenter(x, y, z)        # 设置球心在真实空间中的xyz坐标值。
            sphereWidget.SetRadius(self.RADISU)   # 设置球状体的半径大小
            sphereWidget.GetSphereProperty().SetColor(1, 0, 0)     # 设置球面的颜色为红色 通过GetProperty()方法来获取属性并进行设置
            sphereWidget.SetRepresentationToWireframe()          #将球体的表面形式设置为网格形式。   
            sphereWidget.On()  #显示球状体            
            self.spherelist[i][j][k]= sphereWidget  #将球状体添加到球状体的列表中

    def drawLines(self):
        
        """
        初始化画线 生成用于保存线的sourcelist, mapperlist, actorlist
        获取每个控制点球体的位置并保存在spherelocation中
        将每个控制点与其邻居结点连接起来
        """
        # 初始化列表 这些列表用于保存边与边的关系 列表为i*j*k*6维 因为有i*j*k个球体 一个球最多有6个邻居
        self.sourcelist = [[[[vtk.vtkLineSource() for nei in range(6)] for zcol in range(self.zl+1)] for col in range(self.yl+1)] for row in range(self.xl+1)]
        #vtk.vtklinesource用来生成点之间的线。
        self.mapperlist = [[[[vtk.vtkPolyDataMapper() for nei in range(6)] for zcol in range(self.zl+1)] for col in range(self.yl+1)] for row in range(self.xl+1)]
        self.actorlist = [[[[vtk.vtkActor() for nei in range(6)] for zcol in range(self.zl+1)] for col in range(self.yl+1)] for row in range(self.xl+1)]
        
        # 初始化列表 实时保存和更新球的坐标 列表为i*j*k维 因为有i*j*k个球体
        self.spherelocation = [[[0 for zcol in range(self.zl+1)] for col in range(self.yl+1)] for row in range(self.xl+1)]
        
        for i, j, k in ((a, b, c) for a in range(self.xl+1) for b in range(self.yl+1) for c in range(self.zl+1)):
            # 对于一个球体i 获取球心的位置
            x1, y1, z1 = self.spherelist[i][j][k].GetCenter()
            # 在初始化时 记录球体的位置
            self.spherelocation[i][j][k] = [x1, y1, z1]
            n = self.neighbor(i, j, k)
            
            count = 0 #count用来遍历邻居
            
            for (inei, jnei, knei) in n:  #n包含了它6个邻居的三个维度的索引。
                # 对于这个球体i的邻居j 获取球心的位置
                x2, y2, z2 = self.spherelist[inei][jnei][knei].GetCenter()  #邻居点的球心位置。
                # 设置一条线的起点和终点
                self.sourcelist[i][j][k][count].SetPoint1(x1, y1, z1)  #设置线的起点。
                self.sourcelist[i][j][k][count].SetPoint2(x2, y2, z2)  #设置线的终点。
                self.sourcelist[i][j][k][count].SetResolution(21)  #设置线的分辨率
                
                # Filter的连接可以通过方法SetInputConnection()和GetOutputPort()
                #我们需要在source和mapper之间添加filter。
                # 输出通过方法SetInputConnection()设置为vtkPolyDataMapper对象的输入
                self.mapperlist[i][j][k][count].SetInputConnection(self.sourcelist[i][j][k][count].GetOutputPort())
                # 设置定义几何信息的mapper到这个actor里
                # 在里 mapper的类型是vtkPolyDataMapper 也就是用类似点、线、多边形(Polygons)等几何图元进行渲染的
                self.actorlist[i][j][k][count].SetMapper(self.mapperlist[i][j][k][count])
                self.actorlist[i][j][k][count].GetMapper().ScalarVisibilityOff()  #无视标量数据
                

                self.actorlist[i][j][k][count].GetProperty().SetDiffuseColor(1, 0, 0)  #设置actor的颜色
                # 使用renderer的方法AddActor()把要渲染的actor加入到renderer中去。
                self.ren.AddActor(self.actorlist[i][j][k][count])  #将actor加入渲染器
                count += 1

    def addControlPointsObserver(self):
        """
        对于每一个球体控制点 添加Observer监听vtkRenderWindowInteractor里的事件
        用户方法通过定义一个回调函数sphereCallback并将其作为参数传入AddObserver来定义
        该函数将GUI交互器与用户自定义的渲染交互窗口交互器的方法关联起来
        """
        for i, j, k in ((a, b, c) for a in range(self.xl+1) for b in range(self.yl+1) for c in range(self.zl+1)):
            self.spherelist[i][j][k].AddObserver("InteractionEvent", self.sphereCallback)
        #对于每一个控制点，监听它是否发生变化。

    def sphereCallback(self, obj, event):
        """
        对于控制点的回调交互函数
        主要功能为: 
        	检查控制点是否被拽动
        	对于被拽动的控制点: 去掉旧的邻居结点连线并增加新的连线
        					 去掉旧的人脸并调用ffd算法生成新的人脸
        """
        self._sphereCallback()

    def sphereQt(self, xyz_index, xyz):
        i, j, k = xyz_index
        self.spherelist[i][j][k].SetCenter(xyz)
        self._sphereCallback()

    def _sphereCallback(self):  #如果控制点发生了变化，这个函数才会被调用。
        for i, j, k in ((a, b, c) for a in range(self.xl+1) for b in range(self.yl+1) for c in range(self.zl+1)):
            # 对于一个球体i 获取它之前的位置
            x0, y0, z0 = self.spherelocation[i][j][k]
            # 对于一个球体i 获取它现在球心的位置
            x1, y1, z1 = self.spherelist[i][j][k].GetCenter() 

            
            if x1!=x0 or y1!=y0 or z1!=z0:  # 只对发生改变的球体进行计算 如果球体的位置发生改变 即该控制点被拖动
                print('Before location', x0, y0, z0)
                print("New location", x1, y1, z1)
                # 将更新后的坐标点传给ffd算法保存下来
                print(i ,j, k)
                self.ffd.changed_update((i, j, k), np.array([x1, y1, z1]))
                # 更新spherelocation里面保存的每一个球体的位置
                self.spherelocation[i][j][k] = [x1, y1, z1]

                # 对于球体位置改变的控制点 计算它的邻居结点 重新连线
                n = self.neighbor(i, j, k)
                count = 0
                for (inei, jnei, knei) in n:
                    # 对于这个移动过的球体i的邻居j 获取球心的位置
                    x2, y2, z2 = self.spherelist[inei][jnei][knei].GetCenter()
                    # 设置控制点移动后的新位置与邻居结点连线的起点和终点
                    self.sourcelist[i][j][k][count].SetPoint1(x1, y1, z1)
                    self.sourcelist[i][j][k][count].SetPoint2(x2, y2, z2)
                    # Filter的连接可以通过方法SetInputConnection()和GetOutputPort()
                    # 输出通过方法SetInputConnection()设置为vtkPolyDataMapper对象的输入
                    self.mapperlist[i][j][k][count].SetInputConnection(self.sourcelist[i][j][k][count].GetOutputPort())
                    # 去掉之前的 邻居结点之前和该位置发生移动的控制点 生成的旧线
                    nei_of_nei = self.neighbor(inei, jnei, knei).index((i, j, k))
                    self.ren.RemoveActor(self.actorlist[inei][jnei][knei][nei_of_nei])
                    # 设置定义几何信息的mapper到这个actor里
                    # 在里 mapper的类型是vtkPolyDataMapper 也就是用类似点、线、多边形(Polygons)等几何图元进行渲染的
                    self.actorlist[i][j][k][count].SetMapper(self.mapperlist[i][j][k][count])
                    # vtkActor.GetProperty()->SetColor() not working for me
                    # ref: http://vtk.1045678.n5.nabble.com/vtkActor-GetProperty-gt-SetColor-not-working-for-me-td5722373.html
                    self.actorlist[i][j][k][count].GetMapper().ScalarVisibilityOff()
                    # 设置Actor的颜色 该方法用RGB值来设置一个Actor的红、绿、蓝分量的颜色 每个分量的取值范围从0到1
                    self.actorlist[i][j][k][count].GetProperty().SetColor(1, 0, 0)
                    # 使用renderer的方法AddActor()把要渲染的actor加入到renderer中去。
                    self.ren.AddActor(self.actorlist[i][j][k][count])
                    count += 1
 
           
        print('Begin FFD...')
        print('Calculating...')
        # 更新控制点
        self.ffd.update_control_point()
        self.points = self.data.GetPoints()

        # 只对需要改变的点进行计算 并将计算后更改后的数据存入data的points数据中
        t1 = time()  #计算变形前时间
        for u, v, w in self.ffd.changed.keys():
            for a, b, c in ((a, b, c) for a in range(-2,2) for b in range(-2,2) for c in range(-2,2)):
                if 0<=u+a<self.ffd.cp_num_x and 0<=v+b<self.ffd.cp_num_y and 0<=w+c<self.ffd.cp_num_z:
                    for (id_index,x,y,z) in self.ffd.object_points[(u+a,v+b,w+c)]:
                        tmp = self.ffd.T_local([x,y,z])
                        self.points.SetPoint(id_index,tuple([x+tmp[0],y+tmp[1],z+tmp[2]]))
        print(time()-t1)  #打印总的计算时间。

        # 构造mapper
        self.ffd.changed_reset()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(self.data)

        # 去掉原始的人脸
        self.ren.RemoveActor(self.actor)
        # 添加更改后的新的人脸
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(mapper)
        self.ren.AddActor(self.actor)
        print('Done FFD')        

if __name__ == "__main__":

    ren = vtk.vtkRenderer()  #初始化渲染器
    iren = vtk.vtkRenderWindowInteractor()  #初始化对鼠标的渲染器
    renWin = vtk.vtkRenderWindow()  #初始化渲染窗口
    mylight=vtk.vtkLight()
    mylight.SetColor(0,1,0)
    mylight.SetPosition(2,3,1)
    ren.AddLight(mylight)
    
    renWin.AddRenderer(ren)  #将渲染器加入渲染窗口
    iren.SetRenderWindow(renWin)

    VtkModel(ren=ren, iren=iren)

    iren.Initialize()
    renWin.Render()
    iren.Start()
