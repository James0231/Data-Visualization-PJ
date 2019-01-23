import copy

import numpy as np

class FFDAlgorithm(object):
    def __init__(self, num_x, num_y, num_z, filename, object_points): #定义三坐标轴上控制点个数
        self.cp_num_x = num_x
        self.cp_num_y = num_y
        self.cp_num_z = num_z
        self.object_points_initial = object_points

    def cover_obj(self, initial=True): #对obj物体做一层网格覆盖
        points = np.array(self.object_points_initial) #找到三坐标轴上最大、最小值，来生成最小网格
        self.min_x, self.min_y, self.min_z = points.min(axis=0)
        self.max_x, self.max_y, self.max_z = points.max(axis=0)
        self.nx = (self.max_x - self.min_x) / (self.cp_num_x - 1)
        self.ny = (self.max_y - self.min_y) / (self.cp_num_y - 1)
        self.nz = (self.max_z - self.min_z) / (self.cp_num_z - 1)
        self.changed = {}
        if initial:
            self.control_points = [#初始化控制点位置
                [
                    [np.array([0.0, 0.0, 0.0]) for z in range(self.cp_num_z)]
                    for y in range(self.cp_num_y)
                ]
                for x in range(self.cp_num_x)
            ]
            self.cp_locations = [#依据网格大小生成控制点坐标
                [
                    [
                        np.array(
                            [
                                self.min_x + x * self.nx,
                                self.min_y + y * self.ny,
                                self.min_z + z * self.nz,
                            ]
                        )
                        for z in range(self.cp_num_z)
                    ]
                    for y in range(self.cp_num_y)
                ]
                for x in range(self.cp_num_x)
            ]
            self.init_cp_locations = copy.deepcopy(
                self.cp_locations #深拷贝一份控制点坐标
            )
            try:
                del self.object_points
            except:
                pass
            self.object_points = {}
            for x in range(self.cp_num_x):
                for y in range(self.cp_num_y):
                    for z in range(self.cp_num_z):
                        self.object_points[(x, y, z)] = set()
            for point_index in range(len(self.object_points_initial)):
                [x, y, z] = self.object_points_initial[point_index]
                i = int((x - self.min_x) / self.nx)
                j = int((y - self.min_y) / self.ny)
                k = int((z - self.min_z) / self.nz)
                self.object_points[(i, j, k)].add((point_index, x, y, z))

    def read_ffd(self, path):
        f = open(path, "r")
        self.new_control_points = copy.deepcopy(self.control_points)
        self.new_cp_locations = copy.deepcopy(
            self.init_cp_locations
        )
        begin = False
        while True:
            line = f.readline() #按行读取ffd文件
            if not begin:
                if line.startswith("#"):
                    if "#dimension#" in line: #提取维度
                        line = f.readline()
                        self.dimension = int(line.split("\n")[0])
                        continue
                    if "#offsets of the control points#" in line: #提取偏移量
                        begin = True
                        x = 0
                        y = 0
                        continue
                    elif "#control grid size#" in line: #提取控制点个数
                        size = []
                        for _ in range(self.dimension):
                            line = f.readline()
                            size.append(int(line.split("\n")[0]))
                        continue
                    else:
                        continue
                else:
                    continue
            else:
                if line == "\n":
                    x += 1
                    y = 0
                    if x == size[0]:
                        break
                    else:
                        continue
                else:
                    line = line.split("\t")[:-1]
                    for z in range(len(line)):
                        try:
                            self.new_control_points[x][y][z] = np.array(
                                [np.float(i) for i in line[z].split(" ")]
                            )
                        except IndexError:
                            raise
                    y += 1
        for x in range(len(self.new_control_points)):
            for y in range(len(self.new_control_points[x])):
                for z in range(len(self.new_control_points[x][y])):
                    self.new_cp_locations[x][y][z] += (
                        self.new_control_points[x][y][z]
                        * 3
                        * (self.nx + self.ny + self.nz)
                        / 3 #偏移量较小时按照网格单位长度*偏移量
                    )
        return

    def save_cp(self, filename): #保存ffd文件
        f = open(filename, "w")
        f.write("#dimension#\n")
        f.write("3\n")
        f.write("#one to one#\n")
        f.write("1\n")
        f.write("#control grid size#\n")
        f.write(str(self.cp_num_x) + "\n")
        f.write(str(self.cp_num_y) + "\n")
        f.write(str(self.cp_num_z) + "\n")
        f.write("#control grid spacing#\n")
        f.write(str(self.nx) + "\n")
        f.write(str(self.ny) + "\n")
        f.write(str(self.nz) + "\n")
        f.write("#offsets of the control points#\n")
        for x in range(len(self.control_points)):
            for y in range(len(self.control_points[x])):
                for z in range(len(self.control_points[x][y])):
                    f.write(
                        str(self.control_points[x][y][z][0])
                        + " "
                        + str(self.control_points[x][y][z][1])
                        + " "
                        + str(self.control_points[x][y][z][2])
                        + "\t"
                    )
                f.write("\n")
            f.write("\n")
        f.close()
        return

    def B(self, i, u): #B样条变换，下面class为bezier变换
        if i == 0:
            return (1 - u) ** 3 / 6
        elif i == 1:
            return (3 * u ** 3 - 6 * u ** 2 + 4) / 6
        elif i == 2:
            return (-3 * u ** 3 + 3 * u ** 2 + 3 * u + 1) / 6
        elif i == 3:
            return u ** 3 / 6

    def T_local(self, object_point):
        [x, y, z] = object_point
        i = int((x - self.min_x) / self.nx) - 1
        j = int((y - self.min_y) / self.ny) - 1
        k = int((z - self.min_z) / self.nz) - 1
        u = (x - self.min_x) / self.nx - int((x - self.min_x) / self.nx)
        v = (y - self.min_y) / self.ny - int((y - self.min_y) / self.ny)
        w = (z - self.min_z) / self.nz - int((z - self.min_z) / self.nz)
        result = np.array([0.0, 0.0, 0.0])
        for l in range(4):
            if 0 <= i + l < self.cp_num_x:
                for m in range(4):
                    if 0 <= j + m < self.cp_num_y:
                        for n in range(4):
                            if 0 <= k + n < self.cp_num_z:
                                result = (
                                    result
                                    + self.B(l, u)
                                    * self.B(m, v)
                                    * self.B(n, w)
                                    * self.control_points[i + l][j + m][k + n]
                                )
        return result

    def changed_reset(self):
        del self.changed
        self.changed = {}

    def changed_update(self, id, location):
        self.changed[id] = location

    def update_control_point(self):
        for (u, v, w), new_location in self.changed.items():
            self.control_points[u][v][w] = (
                new_location - self.cp_locations[u][v][w]
            )


class FFD_Bezier(object):
    def __init__(self, num_x, num_y, num_z, filename, object_points): #定义三坐标轴上控制点个数
        self.cp_num_x = num_x
        self.cp_num_y = num_y
        self.cp_num_z = num_z
        self.object_points_initial = object_points

    def cover_obj(self, initial=True): #对obj物体做一层网格覆盖
        points = np.array(self.object_points_initial) #找到三坐标轴上最大、最小值，来生成最小网格
        self.min_x, self.min_y, self.min_z = points.min(axis=0)
        self.max_x, self.max_y, self.max_z = points.max(axis=0)
        self.nx = (self.max_x - self.min_x) / (self.cp_num_x - 1)
        self.ny = (self.max_y - self.min_y) / (self.cp_num_y - 1)
        self.nz = (self.max_z - self.min_z) / (self.cp_num_z - 1)
        self.changed = {}
        if initial:
            self.control_points = [#初始化控制点位置
                [
                    [np.array([0.0, 0.0, 0.0]) for z in range(self.cp_num_z)]
                    for y in range(self.cp_num_y)
                ]
                for x in range(self.cp_num_x)
            ]
            self.cp_locations = [#依据网格大小生成控制点坐标
                [
                    [
                        np.array(
                            [
                                self.min_x + x * self.nx,
                                self.min_y + y * self.ny,
                                self.min_z + z * self.nz,
                            ]
                        )
                        for z in range(self.cp_num_z)
                    ]
                    for y in range(self.cp_num_y)
                ]
                for x in range(self.cp_num_x)
            ]
            self.init_cp_locations = copy.deepcopy(
                self.cp_locations #深拷贝一份控制点坐标
            )
            try:
                del self.object_points
            except:
                pass
            self.object_points = {}
            for x in range(self.cp_num_x):
                for y in range(self.cp_num_y):
                    for z in range(self.cp_num_z):
                        self.object_points[(x, y, z)] = set()
            for point_index in range(len(self.object_points_initial)):
                [x, y, z] = self.object_points_initial[point_index]
                i = int((x - self.min_x) / self.nx)
                j = int((y - self.min_y) / self.ny)
                k = int((z - self.min_z) / self.nz)
                self.object_points[(i, j, k)].add((point_index, x, y, z))

    def read_ffd(self, path):
        f = open(path, "r")
        self.new_control_points = copy.deepcopy(self.control_points)
        self.new_cp_locations = copy.deepcopy(
            self.init_cp_locations
        )
        begin = False
        while True:
            line = f.readline() #按行读取ffd文件
            if not begin:
                if line.startswith("#"):
                    if "#dimension#" in line: #提取维度
                        line = f.readline()
                        self.dimension = int(line.split("\n")[0])
                        continue
                    if "#offsets of the control points#" in line: #提取偏移量
                        begin = True
                        x = 0
                        y = 0
                        continue
                    elif "#control grid size#" in line: #提取控制点个数
                        size = []
                        for _ in range(self.dimension):
                            line = f.readline()
                            size.append(int(line.split("\n")[0]))
                        continue
                    else:
                        continue
                else:
                    continue
            else:
                if line == "\n":
                    x += 1
                    y = 0
                    if x == size[0]:
                        break
                    else:
                        continue
                else:
                    line = line.split("\t")[:-1]
                    for z in range(len(line)):
                        try:
                            self.new_control_points[x][y][z] = np.array(
                                [np.float(i) for i in line[z].split(" ")]
                            )
                        except IndexError:
                            raise
                    y += 1
        for x in range(len(self.new_control_points)):
            for y in range(len(self.new_control_points[x])):
                for z in range(len(self.new_control_points[x][y])):
                    self.new_cp_locations[x][y][z] += (
                        self.new_control_points[x][y][z]
                        * 3
                        * (self.nx + self.ny + self.nz)
                        / 3 #偏移量较小时按照网格单位长度*偏移量
                    )
        return

    def save_cp(self, filename): #保存ffd文件
        f = open(filename, "w")
        f.write("#dimension#\n")
        f.write("3\n")
        f.write("#one to one#\n")
        f.write("1\n")
        f.write("#control grid size#\n")
        f.write(str(self.cp_num_x) + "\n")
        f.write(str(self.cp_num_y) + "\n")
        f.write(str(self.cp_num_z) + "\n")
        f.write("#control grid spacing#\n")
        f.write(str(self.nx) + "\n")
        f.write(str(self.ny) + "\n")
        f.write(str(self.nz) + "\n")
        f.write("#offsets of the control points#\n")
        for x in range(len(self.control_points)):
            for y in range(len(self.control_points[x])):
                for z in range(len(self.control_points[x][y])):
                    f.write(
                        str(self.control_points[x][y][z][0])
                        + " "
                        + str(self.control_points[x][y][z][1])
                        + " "
                        + str(self.control_points[x][y][z][2])
                        + "\t"
                    )
                f.write("\n")
            f.write("\n")
        f.close()
        return
    
    def Bezier(self, i, u):
        if i == 0:
            return (1 - u) ** 3
        elif i == 1:
            return 3 * u ** 3 - 6 * u ** 2 + 3 * u
        elif i == 2:
            return -3 * u ** 3 + 3 * u ** 2
        elif i == 3:
            return u ** 3

    def T_local(self, object_point):
        [x, y, z] = object_point
        i = int((x - self.min_x) / self.nx) - 1
        j = int((y - self.min_y) / self.ny) - 1
        k = int((z - self.min_z) / self.nz) - 1
        u = (x - self.min_x) / self.nx - int((x - self.min_x) / self.nx)
        v = (y - self.min_y) / self.ny - int((y - self.min_y) / self.ny)
        w = (z - self.min_z) / self.nz - int((z - self.min_z) / self.nz)
        result = np.array([0.0, 0.0, 0.0])
        for l in range(4):
            if 0 <= i + l < self.cp_num_x:
                for m in range(4):
                    if 0 <= j + m < self.cp_num_y:
                        for n in range(4):
                            if 0 <= k + n < self.cp_num_z:
                                result = (
                                    result
                                    + self.Bezier(l, u)
                                    * self.Bezier(m, v)
                                    * self.Bezier(n, w)
                                    * self.control_points[i + l][j + m][k + n]
                                )
        return result

    def changed_reset(self):
        del self.changed
        self.changed = {}

    def changed_update(self, id, location):
        self.changed[id] = location

    def update_control_point(self):
        for (u, v, w), new_location in self.changed.items():
            self.control_points[u][v][w] = (
                new_location - self.cp_locations[u][v][w]
            )
