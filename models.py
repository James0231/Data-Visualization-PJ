# coding=utf-8

import numpy as np
import vtk

from algorithm import FFDAlgorithm


class model(object):
    def __init__(
        self,
        ren=None,
        iren=None,
        filename="dragon.obj",
        method="B",
        cp_num_x=4, #初始控制点个数设定为5
        cp_num_y=4,
        cp_num_z=4,
    ):
        self.radius = 0.01 #定义控制点的半径
        self.ren = ren  # 渲染器初始化
        self.iren = iren
        self.filename = filename
        self.cp_num_x = cp_num_x
        self.cp_num_y = cp_num_y
        self.cp_num_z = cp_num_z

        self.ren.SetBackground(0, 0, 0)  # 设置背景颜色为黑色

        interactor_style = vtk.vtkInteractorStyleTrackballCamera()  # 用移动摄像头的交互方式
        self.iren.SetInteractorStyle(
            interactor_style
        )  # 这种交互方式可以使用户点击鼠标左键并拖动时从另外角度观察物体。

        self.load_obj()  # 构造函数，该函数用来读取OBJ文件
        self.draw()  # 构造函数，该函数用来显示obj物体

        # 根据obj物体大小改变控制点半径
        self.radius = (self.ffd_algo.max_x - self.ffd_algo.min_x) * self.radius

        self.draw_control_points()  # 增加控制点
        self.draw_lines()  # 在控制点之间连线
        self.set_control_points_listener()  # 这个监听函数用来检查控制点是否移动。

    def neighbor(self, i, j, k):  # 之后要移动控制点，需要将控制点重新与他邻居的这些点连接起来。

        n = []
        if i > 0:
            n.append((i - 1, j, k))
        if i < self.cp_num_x:
            n.append((i + 1, j, k))
        if j > 0:
            n.append((i, j - 1, k))
        if j < self.cp_num_y:
            n.append((i, j + 1, k))
        if k > 0:
            n.append((i, j, k - 1))
        if k < self.cp_num_z:
            n.append((i, j, k + 1))
        return n

    def load_obj(self):
        self.reader = vtk.vtkOBJReader()  # 用vtk自带的OBJReader来读取
        self.reader.SetFileName(self.filename)  # 设置读取的文件名。
        self.reader.Update()  
        self.data = self.reader.GetOutput()  # 将数据储存在data中

    def draw(self):

        self.points = self.data.GetPoints()
        vertices = [
            self.points.GetPoint(i) for i in range(self.points.GetNumberOfPoints())
        ]
        self.ffd_algo = FFDAlgorithm( #调用ffd算法
            num_x=self.cp_num_x + 1,
            num_y=self.cp_num_y + 1,
            num_z=self.cp_num_z + 1,
            object_points=vertices,
            filename=self.filename,
        )
        self.ffd_algo.cover_obj() #生成包裹obj物体的网格
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(self.data)

        self.actor = vtk.vtkActor()
        self.actor.SetMapper(mapper)
        self.ren.AddActor(self.actor)

    def draw_control_points(self):

        # 初始化列表 保存每一个控制球体 列表为i*j*k维 因为有i*j*k个球体
        self.spherelist = [
            [
                [0 for zcol in range(self.cp_num_z + 1)]
                for col in range(self.cp_num_y + 1)
            ]
            for row in range(self.cp_num_x + 1)
        ]

        for i, j, k in (
            (a, b, c)
            for a in range(self.cp_num_x + 1)
            for b in range(self.cp_num_y + 1)
            for c in range(self.cp_num_z + 1)
        ):
            sphereWidget = vtk.vtkSphereWidget()  # 定义一个球状体widget

            sphereWidget.SetInteractor(self.iren)  # 在渲染窗口交互器实例iren实现3D球状体widget

            x, y, z = self.ffd_algo.cp_locations[i][j][k]  # 从索引值对应到真实空间中的xyz坐标
            sphereWidget.SetCenter(x, y, z)  # 设置球心在真实空间中的xyz坐标值。
            sphereWidget.SetRadius(self.radius)  # 设置球状体的半径大小
            sphereWidget.GetSphereProperty().SetColor(
                1, 0, 0
            )  # 设置球面的颜色为红色 通过GetProperty()方法来获取属性并进行设置
            sphereWidget.SetRepresentationToWireframe()  # 将球体的表面形式设置为网格形式。
            sphereWidget.On()  # 显示球状体
            self.spherelist[i][j][k] = sphereWidget  # 将球状体添加到球状体的列表中

    def draw_lines(self):
        # 初始化列表 这些列表用于保存边与边的关系 列表为i*j*k*6维 因为有i*j*k个球体 一个球最多有6个邻居
        self.sourcelist = [
            [
                [
                    [vtk.vtkLineSource() for nei in range(6)]
                    for zcol in range(self.cp_num_z + 1)
                ]
                for col in range(self.cp_num_y + 1)
            ]
            for row in range(self.cp_num_x + 1)
        ]
        # vtk.vtklinesource用来生成点之间的线。
        self.mapperlist = [
            [
                [
                    [vtk.vtkPolyDataMapper() for nei in range(6)]
                    for zcol in range(self.cp_num_z + 1)
                ]
                for col in range(self.cp_num_y + 1)
            ]
            for row in range(self.cp_num_x + 1)
        ]
        self.actorlist = [
            [
                [
                    [vtk.vtkActor() for nei in range(6)]
                    for zcol in range(self.cp_num_z + 1)
                ]
                for col in range(self.cp_num_y + 1)
            ]
            for row in range(self.cp_num_x + 1)
        ]

        # 初始化列表 实时保存和更新球的坐标 列表为i*j*k维 因为有i*j*k个球体
        self.spherelocation = [
            [
                [0 for zcol in range(self.cp_num_z + 1)]
                for col in range(self.cp_num_y + 1)
            ]
            for row in range(self.cp_num_x + 1)
        ]

        for i, j, k in (
            (a, b, c)
            for a in range(self.cp_num_x + 1)
            for b in range(self.cp_num_y + 1)
            for c in range(self.cp_num_z + 1)
        ):
            # 对于一个球体i 获取球心的位置
            x1, y1, z1 = self.spherelist[i][j][k].GetCenter()
            # 在初始化时 记录球体的位置
            self.spherelocation[i][j][k] = [x1, y1, z1]
            n = self.neighbor(i, j, k)

            count = 0  # count用来遍历邻居

            for (neighbor_i, neighbor_j, neighbor_k) in n:  # n包含了它6个邻居的三个维度的索引。
                # 对于这个球体i的邻居j 获取球心的位置
                x2, y2, z2 = self.spherelist[neighbor_i][neighbor_j][
                    neighbor_k
                ].GetCenter()  # 邻居点的球心位置。
                # 设置一条线的起点和终点
                self.sourcelist[i][j][k][count].SetPoint1(x1, y1, z1)  # 设置线的起点。
                self.sourcelist[i][j][k][count].SetPoint2(x2, y2, z2)  # 设置线的终点。
                self.sourcelist[i][j][k][count].SetResolution(21)  # 设置线的分辨率

                # 输出通过方法SetInputConnection()设置为vtkPolyDataMapper对象的输入
                self.mapperlist[i][j][k][count].SetInputConnection(
                    self.sourcelist[i][j][k][count].GetOutputPort()
                )
                # 设置定义几何信息的mapper到这个actor里
                # 在里 mapper的类型是vtkPolyDataMapper 也就是用类似点、线、多边形(Polygons)等几何图元进行渲染的
                self.actorlist[i][j][k][count].SetMapper(
                    self.mapperlist[i][j][k][count]
                )
                self.actorlist[i][j][k][
                    count
                ].GetMapper().ScalarVisibilityOff()  # 无视标量数据

                self.actorlist[i][j][k][count].GetProperty().SetDiffuseColor(
                    1, 0, 0
                )  # 设置actor的颜色
                # 使用renderer的方法AddActor()把要渲染的actor加入到renderer中去。
                self.ren.AddActor(self.actorlist[i][j][k][count])  # 将actor加入渲染器
                count += 1

    def set_control_points_listener(self):
        for i, j, k in (
            (a, b, c)
            for a in range(self.cp_num_x + 1)
            for b in range(self.cp_num_y + 1)
            for c in range(self.cp_num_z + 1)
        ):
            self.spherelist[i][j][k].AddObserver("InteractionEvent", self.cp_callback)
        # 对于每一个控制点，监听它是否发生变化。

    def render_sphere(self, xyz_index, xyz):
        i, j, k = xyz_index
        self.spherelist[i][j][k].SetCenter(xyz)
        self.cp_callback()

    def cp_callback(self, obj, event):  # 如果控制点发生了变化，这个函数才会被调用。
        for i, j, k in (
            (a, b, c)
            for a in range(self.cp_num_x + 1)
            for b in range(self.cp_num_y + 1)
            for c in range(self.cp_num_z + 1)
        ):
            # 对于一个球体i 获取它之前的位置
            x0, y0, z0 = self.spherelocation[i][j][k]
            # 对于一个球体i 获取它现在球心的位置
            x1, y1, z1 = self.spherelist[i][j][k].GetCenter()

            if x1 != x0 or y1 != y0 or z1 != z0:  # 对发生改变的球体进行计算 如果球体的位置发生改变 即该控制点被拖动
                # 将更新后的坐标点传给ffd算法保存下来
                self.ffd_algo.changed_update((i, j, k), np.array([x1, y1, z1]))
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
                    # 输出通过方法SetInputConnection()设置为vtkPolyDataMapper对象的输入
                    self.mapperlist[i][j][k][count].SetInputConnection(
                        self.sourcelist[i][j][k][count].GetOutputPort()
                    )
                    # 去掉之前的 邻居结点之前和该位置发生移动的控制点 生成的旧线
                    nei_of_nei = self.neighbor(inei, jnei, knei).index((i, j, k))
                    self.ren.RemoveActor(self.actorlist[inei][jnei][knei][nei_of_nei])
                    # 设置定义几何信息的mapper到这个actor里
                    # 在里 mapper的类型是vtkPolyDataMapper 也就是用类似点、线、多边形(Polygons)等几何图元进行渲染的
                    self.actorlist[i][j][k][count].SetMapper(
                        self.mapperlist[i][j][k][count]
                    )
                    self.actorlist[i][j][k][count].GetMapper().ScalarVisibilityOff()
                    # 设置Actor的颜色 该方法用RGB值来设置一个Actor的红、绿、蓝分量的颜色 每个分量的取值范围从0到1
                    self.actorlist[i][j][k][count].GetProperty().SetColor(1, 0, 0)
                    # 使用renderer的方法AddActor()把要渲染的actor加入到renderer中去。
                    self.ren.AddActor(self.actorlist[i][j][k][count])
                    count += 1

        # 更新控制点
        self.ffd_algo.update_control_point()
        self.points = self.data.GetPoints()

        # 对需要改变的点进行计算 并将计算后更改后的数据存入data的points数据中
        for u, v, w in self.ffd_algo.changed.keys():
            for a, b, c in (
                (a, b, c)
                for a in range(-2, 2)
                for b in range(-2, 2)
                for c in range(-2, 2)
            ):
                if (
                    0 <= u + a < self.ffd_algo.cp_num_x
                    and 0 <= v + b < self.ffd_algo.cp_num_y
                    and 0 <= w + c < self.ffd_algo.cp_num_z
                ):
                    for (id_index, x, y, z) in self.ffd_algo.object_points[
                        (u + a, v + b, w + c)
                    ]:
                        tmp = self.ffd_algo.T_local([x, y, z])
                        self.points.SetPoint(
                            id_index, tuple([x + tmp[0], y + tmp[1], z + tmp[2]])
                        )
        # 构造mapper
        self.ffd_algo.changed_reset()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(self.data)

        # 改变原obj物体
        self.ren.RemoveActor(self.actor)
        # 显示新obj物体
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(mapper)
        self.ren.AddActor(self.actor)
