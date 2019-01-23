import sys
import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox, QAction, QFileDialog
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk
from models import model
from models_bezier import model_bezier

class MainWindow(object): #设置主窗口显示
    def __init__(self):
        self.central_widget = None
        self.grid_layout = None
        self.vtk_widget = None

    def setup_ui(self, view): #设置主界面
        view.setObjectName("MainWindow")
        view.resize(1500, 1500) #设置界面初始大小
        self.central_widget = QtWidgets.QWidget(view)
        self.grid_layout = QtWidgets.QGridLayout(self.central_widget)
        self.vtk_widget = QVTKRenderWindowInteractor(self.central_widget) #嵌入vtk界面
        view.setCentralWidget(self.vtk_widget)
        view.statusBar().showMessage("successfully...") #显示加载成功字样
        view.setWindowTitle("Free-Form Deformation") #显示窗口标题


class SimpleView(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.ui = MainWindow()
        self.ui.setup_ui(self)
        self.create_actions() #创建菜单栏操作
        self.create_menus() #创建菜单栏
        self.filename = "iphone_6_model.obj" #封面导入苹果手机obj文件
        self.show_obj() #显示封面
        self.show_all() #显示界面

    def show_obj(self):
        self.reader = vtk.vtkOBJReader() #读取obj文件
        self.reader.SetFileName(self.filename) #读取文件名
        self.reader.Update()
        self.data = self.reader.GetOutput() #记录obj文件数据
        self.ren = vtk.vtkRenderer() #初始化显示界面
        self.ui.vtk_widget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.ui.vtk_widget.GetRenderWindow().GetInteractor()
        mapper = vtk.vtkPolyDataMapper() #生成polydata格式
        mapper.SetInputData(self.data)
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(mapper)
        self.ren.AddActor(self.actor) #添加actor

    def show_vtk(self, dots=5, grid_size=[5, 5, 5], method="nolight", ffd_type="B"):
        self.ren = vtk.vtkRenderer()
        self.ui.vtk_widget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.ui.vtk_widget.GetRenderWindow().GetInteractor()
        if method == "light": #添加聚光灯效果
            mylight = vtk.vtkLight()
            mylight.SetColor(0, 1, 0)
            mylight.SetPosition(2, 3, 1)
            self.ren.AddLight(mylight)
        self.dots = dots
        self.grid_size = grid_size
        self.dot_xyz = [None, None, None]
        if ffd_type == "B": #使用B样条变换
            self.model: model = model(
                ren=self.ren,
                iren=self.iren,
                filename=self.filename,
                cp_num_x=grid_size[0] - 1,
                cp_num_y=grid_size[1] - 1,
                cp_num_z=grid_size[2] - 1,
            )
        else: #使用贝塞尔变换
            self.model = model_bezier(
                ren=self.ren,
                iren=self.iren,
                filename=self.filename,
                cp_num_x=grid_size[0] - 1,
                cp_num_y=grid_size[1] - 1,
                cp_num_z=grid_size[2] - 1,
            )

    def show_all(self): #显示界面
        self.iren.Initialize()
        self.show()

    def create_actions(self): #创建菜单链接
        self.load_obj_Action = QAction("Add_OBJ_file", self, triggered=self.load_obj) #导入obj文件
        self.load_ffd_Action = QAction("Add_FFD_file", self, triggered=self.load_ffd) #导入ffd文件
        self.save_ffd_Action = QAction("Save_to_FFD", self, triggered=self.save_ffd) #保存ffd文件
        self.to_bezier_Action = QAction(
            "To_Bezier", self, triggered=self.load_ffd_bezier #创建对应操作
        )
        self.turn_on_light_Action = QAction(
            "Turn_on_light", self, triggered=self.load_ffd_light
        )
        
        self.reset_Action = QAction(
            QIcon("reset.jpg"), "Reset", triggered=self.initial #添加复原图标
        )
        
        
        
        self.exit_Action = QAction(
            QIcon("exit.jpg"), "Exit", triggered=QApplication.instance().quit #添加退出图标
        )
        
        
    def create_menus(self): #创建菜单栏
        menubar = self.menuBar()
        self.toolbar_reset = self.addToolBar("Initial")
        self.toolbar_reset.addAction(self.reset_Action)
        self.toolbar_exit = self.addToolBar("Exit")
        self.toolbar_exit.addAction(self.exit_Action)
        self.loadMenu_obj = menubar.addMenu("Change_obj_background")
        self.loadMenu_ffd = menubar.addMenu("Add_FFD_file")
        self.saveMenu = menubar.addMenu("To_FFD_file")
        self.to_bezier = menubar.addMenu("To_Bezier")
        self.turn_on_light = menubar.addMenu("Turn_on_light")
        self.loadMenu_obj.addAction(self.load_obj_Action)
        self.loadMenu_ffd.addAction(self.load_ffd_Action)
        self.saveMenu.addAction(self.save_ffd_Action)
        self.to_bezier.addAction(self.to_bezier_Action)
        self.turn_on_light.addAction(self.turn_on_light_Action)

    def load_obj(self): 
        filename, ok = QFileDialog.getOpenFileName(self, "Add_OBJ_file", "")
        if not filename.upper().endswith(".OBJ"): #判断后缀是否为obj
            reply = QMessageBox.information(
                self, "Info", "This file is not .OBJ", QMessageBox.Yes
            )
        else:
            if ok:#导入obj文件
                self.filename = filename
                self.show_obj()
                self.show_all()
                reply = QMessageBox.information(
                    self, "Info", "Successfully added obj file", QMessageBox.Yes
                )
                print("Done Load OBJ")

    def load_control_size(self, filename): #读取ffd文件对应控制点个数
        num = []
        start = False
        with open(filename, "r") as f:
            while True:
                line = f.readline()
                if "#control grid size#" in line:
                    start = True
                    continue
                if len(num) == 3:
                    break
                if start:
                    num.append(int(line))
        return num

    def load_ffd(self): #导入ffd文件并进行偏移
        filename, ok = QFileDialog.getOpenFileName(self, "Add_FFD_file", "")
        if not filename.upper().endswith(".FFD"):
            reply = QMessageBox.information(
                self, "Info", "This file is not .FFDAlgorithm", QMessageBox.Yes
            )
        else:
            if ok:
                grid_size = self.load_control_size(filename)
                self.show_vtk(grid_size=grid_size)
                self.model.ffd.read_ffd(filename) #读取ffd文件
                for x in range(len(self.model.ffd.control_points)): #对控制点偏移变化做记录
                    for y in range(len(self.model.ffd.control_points[x])):
                        for z in range(len(self.model.ffd.control_points[x][y])):
                            x_loc_new, y_loc_new, z_loc_new = self.model.ffd.new_control_points_location[
                                x
                            ][
                                y
                            ][
                                z
                            ]
                            x_loc_old, y_loc_old, z_loc_old = self.model.ffd.control_points_location[
                                x
                            ][
                                y
                            ][
                                z
                            ]
                            print(1)
                            if (
                                (x_loc_old != x_loc_new)
                                or (y_loc_old != y_loc_new)
                                or (z_loc_old != z_loc_new)
                            ):
                                print(2)
                                self.model.render_sphere(
                                    (x, y, z),
                                    self.model.ffd.new_control_points_location[x][y][z],
                                )

                reply = QMessageBox.information(#提示成功导入ffd
                    self, "Info", "Successfully added ffd_algo file", QMessageBox.Yes
                )
                print("Done Load FFDAlgorithm")
                self.show_all()
        return

    def load_ffd_light(self): #以聚光灯方式导入ffd
        """ 导入 ffd_algo 文件，用self.model.sphereQt函数依次设置点位移 """

        filename, ok = QFileDialog.getOpenFileName(self, "Add_FFD_file", "")
        if not filename.upper().endswith(".FFD"):
            reply = QMessageBox.information(
                self, "Info", "This file is not .FFDAlgorithm", QMessageBox.Yes
            )
        else:
            if ok:
                grid_size = self.load_control_size(filename)
                self.show_vtk(grid_size=grid_size, method="light")
                self.model.ffd.read_ffd(filename)
                for x in range(len(self.model.ffd.control_points)):
                    for y in range(len(self.model.ffd.control_points[x])):
                        for z in range(len(self.model.ffd.control_points[x][y])):
                            x_loc_new, y_loc_new, z_loc_new = self.model.ffd.new_control_points_location[
                                x
                            ][
                                y
                            ][
                                z
                            ]
                            x_loc_old, y_loc_old, z_loc_old = self.model.ffd.control_points_location[
                                x
                            ][
                                y
                            ][
                                z
                            ]
                            print(1)
                            if (
                                (x_loc_old != x_loc_new)
                                or (y_loc_old != y_loc_new)
                                or (z_loc_old != z_loc_new)
                            ):
                                print(2)
                                self.model.render_sphere(
                                    (x, y, z),
                                    self.model.ffd.new_control_points_location[x][y][z],
                                )

                reply = QMessageBox.information(
                    self, "Info", "Successfully added ffd_algo file", QMessageBox.Yes
                )
                print("Done Load FFDAlgorithm")
                self.show_all()
        return

    def load_ffd_bezier(self): #以贝塞尔变换方式导入ffd
        """ 导入 ffd_algo 文件，用self.model.sphereQt函数依次设置点位移 """

        filename, ok = QFileDialog.getOpenFileName(self, "Add_FFD_file", "")
        if not filename.upper().endswith(".FFD"):
            reply = QMessageBox.information(
                self, "Info", "This file is not .FFDAlgorithm", QMessageBox.Yes
            )
        else:
            if ok:
                grid_size = self.load_control_size(filename)
                self.show_vtk(grid_size=grid_size, ffd_type="bezier")
                self.model.ffd.read_ffd(filename)
                for x in range(len(self.model.ffd.control_points)):
                    for y in range(len(self.model.ffd.control_points[x])):
                        for z in range(len(self.model.ffd.control_points[x][y])):
                            x_loc_new, y_loc_new, z_loc_new = self.model.ffd.new_control_points_location[
                                x
                            ][
                                y
                            ][
                                z
                            ]
                            x_loc_old, y_loc_old, z_loc_old = self.model.ffd.control_points_location[
                                x
                            ][
                                y
                            ][
                                z
                            ]
                            print(1)
                            if (
                                (x_loc_old != x_loc_new)
                                or (y_loc_old != y_loc_new)
                                or (z_loc_old != z_loc_new)
                            ):
                                print(2)
                                self.model.render_sphere(
                                    (x, y, z),
                                    self.model.ffd.new_control_points_location[x][y][z],
                                )

                reply = QMessageBox.information(
                    self, "Info", "Successfully added ffd_algo file", QMessageBox.Yes
                )
                print("Done Load FFDAlgorithm")
                self.show_all()
        return

    def save_ffd(self): #导出ffd
        filename, ok = QFileDialog.getSaveFileName(self, "Save_to_FFD", "")
        if ok:
            self.model.ffd.save_cp(filename)
            reply = QMessageBox.information(
                self, "Info", "Successfully saved ffd_algo file", QMessageBox.Yes
            )
            print("Done Save FFDAlgorithm")
            return

    def initial(self): #复原
        self.show_obj()
        self.show_all()
        reply = QMessageBox.information( #弹出提示框
            self, "Info", "Successfully reset", QMessageBox.Yes
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimpleView()
    window.show()
    window.iren.Initialize()  #将vtk嵌入pyqt5界面显示
    sys.exit(app.exec_())
