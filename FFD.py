import numpy as np
import copy
import gc

class obj_reader(object):
    def __init__(self, filename):
        """Loads a Wavefront OBJ file. """
        self.vertices = []
        self.faces = []
        self.tmp = []
        for line in open(filename, "r"):
            if line.startswith('#'): continue
            values = line.split()
            if not values: continue
            if values[0] == 'v':
                v = [float(x) for x in values[1:4]]
                t = [float(x) for x in values[4:]]
                self.vertices.append(v)
                self.tmp.append(t)
            elif values[0] == 'f':
                face = []
                self.faces.append(line)


class FFD(object):

    def __init__(self, num_x, num_y, num_z, object_file,object_points):
        self.cp_num_x = num_x
        self.cp_num_y = num_y
        self.cp_num_z = num_z
        self.obj_file = obj_reader(object_file)
        self.object_points_initial=object_points

    def initial_ffd(self, initial=True):
        tmp = copy.deepcopy(self.object_points_initial)
        tmp.sort(key=lambda x: x[0])
        self.min_x = tmp[0][0]
        self.max_x = tmp[-1][0]
        tmp.sort(key=lambda x: x[1])
        self.min_y = tmp[0][1]
        self.max_y = tmp[-1][1]
        tmp.sort(key=lambda x: x[2])
        self.min_z = tmp[0][2]
        self.max_z = tmp[-1][2]
        del tmp
        self.nx = (self.max_x - self.min_x) / (self.cp_num_x - 1)
        self.ny = (self.max_y - self.min_y) / (self.cp_num_y - 1)
        self.nz = (self.max_z - self.min_z) / (self.cp_num_z - 1)
        self.changed = {}
        if initial:
            self.control_points = [
                [[np.array([0., 0., 0.])
                  for z in range(self.cp_num_z)]
                 for y in range(self.cp_num_y)]
                for x in range(self.cp_num_x)]
            self.control_points_location =  [
                [[np.array([self.min_x + x * self.nx, self.min_y + y * self.ny, self.min_z + z * self.nz])
                  for z in range(self.cp_num_z)]
                 for y in range(self.cp_num_y)]
                for x in range(self.cp_num_x)]
            self.control_points_location_initial = copy.deepcopy(self.control_points_location)            
            try:
                del self.object_points
                # gc.collect()
            except:
                pass
            self.object_points = {}
            for x in range(self.cp_num_x):
                for y in range(self.cp_num_y):
                    for z in range(self.cp_num_z):
                        self.object_points[(x, y, z)] = set()
            #self.object_points= []
            for point_index in range(len(self.object_points_initial)):
                [x, y, z] = self.object_points_initial[point_index]
                i = int((x - self.min_x) / self.nx)
                j = int((y - self.min_y) / self.ny)
                k = int((z - self.min_z) / self.nz)
                self.object_points[(i, j, k)].add((point_index, x, y, z))
                #self.object_points.append(np.array([x,y,z]))

    def load_cp(self, path):
        f = open(path, 'r')
        self.new_control_points = copy.deepcopy(self.control_points)
        self.new_control_points_location = copy.deepcopy(self.control_points_location_initial)
        begin = False
        while True:
            line = f.readline()
            if not begin:
                if line.startswith('#'):
                    if '#dimension#' in line:
                        line = f.readline()
                        self.dimension = int(line.split('\n')[0])
                        continue
                    if '#offsets of the control points#' in line:
                        begin = True
                        x = 0
                        y = 0
                        continue
                    elif '#control grid size#' in line:
                        size = []
                        for _ in range(self.dimension):
                            line = f.readline()
                            size.append(int(line.split('\n')[0]))
                        if self.dimension == 3:
                            # self.control_points = [[[None for z in range(size[2])]
                            #                         for y in range(size[1])]
                            #                        for x in range(size[0])]
                            continue
                        continue
                    else:
                        continue
                else:
                    continue
            else:
                if line == '\n':
                    x += 1
                    y = 0
                    if x == size[0]:
                        break
                    else:
                        continue
                else:
                    line = line.split('\t')[:-1]
                    for z in range(len(line)):
                        try:
                            self.new_control_points[x][y][z] = np.array([np.float(i) for i in line[z].split(' ')])
                        except IndexError:
                            raise
                        # self.control_points[x][y][z] = np.array([np.float(i) for i in line[z].split(' ')]）
                    y += 1
        for x in range(len(self.new_control_points)):
            for y in range(len(self.new_control_points[x])):
                for z in range(len(self.new_control_points[x][y])):
                    # self.new_control_points_location[x][y][z] += self.new_control_points[x][y][z]
                    self.new_control_points_location[x][y][z] += self.new_control_points[x][y][z] * 3 * (self.nx+self.ny+self.nz)/3
        return

    def save_obj(self,filename,new_vertices):
        f = open(filename,'w')
        if self.obj_file.tmp[0]!=[]:
            for i in range(len(new_vertices)):
                f.write('v '+str(new_vertices[i][0])+' '+str(new_vertices[i][1])+' '+str(new_vertices[i][2])+'\n')
        else:
            for i in range(len(new_vertices)):
                f.write('v ' + str(new_vertices[i][0]) + ' ' + str(new_vertices[i][1]) + ' ' + str(
                    new_vertices[i][2]) +' '+str(self.obj_file.tmp[i][0]) + ' ' + str(self.obj_file.tmp[i][1]) + ' ' + str(
                    self.obj_file.tmp[i][2])+ '\n')
        for i in range(len(self.obj_file.faces)):
            f.write(self.obj_file.faces[i])
        f.close()
        print('Successfully save the face!')
        return

    def save_cp(self, filename):
        f = open(filename, 'w')
        f.write('#dimension#\n')
        f.write('3\n')
        f.write('#one to one#\n')
        f.write('1\n')
        f.write('#control grid size#\n')
        f.write(str(self.cp_num_x) + '\n')
        f.write(str(self.cp_num_y) + '\n')
        f.write(str(self.cp_num_z) + '\n')
        f.write('#control grid spacing#\n')
        f.write(str(self.nx) + '\n')
        f.write(str(self.ny) + '\n')
        f.write(str(self.nz) + '\n')
        f.write('#offsets of the control points#\n')
        for x in range(len(self.control_points)):
            for y in range(len(self.control_points[x])):
                for z in range(len(self.control_points[x][y])):
                    f.write(
                        str(self.control_points[x][y][z][0]) + ' ' + str(self.control_points[x][y][z][1]) + ' ' + str(
                            self.control_points[x][y][z][2]) + '\t')
                f.write('\n')
            f.write('\n')
        f.close()
        return

    def B(self, i, u):
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
        result = np.array([0., 0., 0.])
        for l in range(4):
            if 0 <= i + l < self.cp_num_x:
                for m in range(4):
                    if 0 <= j + m < self.cp_num_y:
                        for n in range(4):
                            if 0 <= k + n < self.cp_num_z:
                                result = result + self.B(l, u) * self.B(m, v) * self.B(n, w) * self.control_points[i + l][j + m][k + n]
        return result

    def changed_reset(self):
        del self.changed
        self.changed = {}

    def changed_update(self, id, location):
        self.changed[id] = location

    # Change one control point, we will get the [u,v,w] of the control point.
    # def update_control_point(self, changed_control_point, change):
    #     [u, v, w] = changed_control_point
    #     self.control_points[u][v][w] += change
    #     self.control_points_location[u][v][w] += change
    #     for i in range(len(self.object_points)):
    #         self.object_points[i]=self.T_local(changed_control_point,self.object_points[i])
    #     return self.object_points

    def update_control_point(self):
        # tmp = copy.deepcopy(self.object_points)
        # result = []
        for (u, v, w), new_location in self.changed.items():
            self.control_points[u][v][w] = new_location - self.control_points_location[u][v][w]
        # for i in range(len(self.object_points)):
        #     change_point=self.T_local([u,v,w],tmp[i])
        #     if change_point[0]==0 and change_point[1]==0 and change_point[2]==0:
        #         continue
        #     else:
        #         result.append([i,self.object_points[i]+change_point])
        # return result

class FFD_Bezier(object):

    def __init__(self, num_x, num_y, num_z, object_file,object_points):
        self.cp_num_x = num_x         #x方向控制点个数
        self.cp_num_y = num_y         #y方向控制点个数
        self.cp_num_z = num_z         #z方向控制点个数
        self.obj_file = obj_reader(object_file)       #读取obj文件
        self.object_points_initial=object_points

    def initial_ffd(self, initial=True):
        tmp = copy.deepcopy(self.object_points_initial)
        tmp.sort(key=lambda x: x[0])
        self.min_x = tmp[0][0]
        self.max_x = tmp[-1][0]
        tmp.sort(key=lambda x: x[1])
        self.min_y = tmp[0][1]
        self.max_y = tmp[-1][1]
        tmp.sort(key=lambda x: x[2])
        self.min_z = tmp[0][2]
        self.max_z = tmp[-1][2]
        del tmp
        self.nx = (self.max_x - self.min_x) / (self.cp_num_x - 1)
        self.ny = (self.max_y - self.min_y) / (self.cp_num_y - 1)
        self.nz = (self.max_z - self.min_z) / (self.cp_num_z - 1)
        self.changed = {}
        if initial:
            self.control_points = [
                [[np.array([0., 0., 0.])
                  for z in range(self.cp_num_z)]
                 for y in range(self.cp_num_y)]
                for x in range(self.cp_num_x)]
            self.control_points_location = [
                [[np.array([self.min_x + x * self.nx, self.min_y + y * self.ny, self.min_z + z * self.nz])
                  for z in range(self.cp_num_z)]
                 for y in range(self.cp_num_y)]
                for x in range(self.cp_num_x)]
            self.control_points_location_initial = copy.deepcopy(self.control_points_location)            
            try:
                del self.object_points
                # gc.collect()
            except:
                pass
            self.object_points = {}
            for x in range(self.cp_num_x):
                for y in range(self.cp_num_y):
                    for z in range(self.cp_num_z):
                        self.object_points[(x, y, z)] = set()
            #self.object_points= []
            for point_index in range(len(self.object_points_initial)):
                [x, y, z] = self.object_points_initial[point_index]
                i = int((x - self.min_x) / self.nx)
                j = int((y - self.min_y) / self.ny)
                k = int((z - self.min_z) / self.nz)
                self.object_points[(i, j, k)].add((point_index, x, y, z))
                #self.object_points.append(np.array([x,y,z]))

    def load_cp(self, path):
        f = open(path, 'r')
        self.new_control_points = copy.deepcopy(self.control_points)
        self.new_control_points_location = copy.deepcopy(self.control_points_location_initial)
        begin = False
        while True:
            line = f.readline()
            if not begin:
                if line.startswith('#'):
                    if '#dimension#' in line:
                        line = f.readline()
                        self.dimension = int(line.split('\n')[0])
                        continue
                    if '#offsets of the control points#' in line:
                        begin = True
                        x = 0
                        y = 0
                        continue
                    elif '#control grid size#' in line:
                        size = []
                        for _ in range(self.dimension):
                            line = f.readline()
                            size.append(int(line.split('\n')[0]))
                        if self.dimension == 3:
                            # self.control_points = [[[None for z in range(size[2])]
                            #                         for y in range(size[1])]
                            #                        for x in range(size[0])]
                            continue
                        continue
                    else:
                        continue
                else:
                    continue
            else:
                if line == '\n':
                    x += 1
                    y = 0
                    if x == size[0]:
                        break
                    else:
                        continue
                else:
                    line = line.split('\t')[:-1]
                    for z in range(len(line)):
                        self.new_control_points[x][y][z] = np.array([np.float(i) for i in line[z].split(' ')])
                        # self.control_points[x][y][z] = np.array([np.float(i) for i in line[z].split(' ')]）
                    y += 1
        for x in range(len(self.new_control_points)):
            for y in range(len(self.new_control_points[x])):
                for z in range(len(self.new_control_points[x][y])):
                    self.new_control_points_location[x][y][z] += self.new_control_points[x][y][z]
        return

    def save_obj(self,filename,new_vertices):
        f = open(filename,'w')
        if self.obj_file.tmp[0]!=[]:
            for i in range(len(new_vertices)):
                f.write('v '+str(new_vertices[i][0])+' '+str(new_vertices[i][1])+' '+str(new_vertices[i][2])+'\n')
        else:
            for i in range(len(new_vertices)):
                f.write('v ' + str(new_vertices[i][0]) + ' ' + str(new_vertices[i][1]) + ' ' + str(
                    new_vertices[i][2]) +' '+str(self.obj_file.tmp[i][0]) + ' ' + str(self.obj_file.tmp[i][1]) + ' ' + str(
                    self.obj_file.tmp[i][2])+ '\n')
        for i in range(len(self.obj_file.faces)):
            f.write(self.obj_file.faces[i])
        f.close()
        print('Successfully save the face!')
        return

    def save_cp(self, filename):
        f = open(filename, 'w')
        f.write('#dimension#\n')
        f.write('3\n')
        f.write('#one to one#\n')
        f.write('1\n')
        f.write('#control grid size#\n')
        f.write(str(self.cp_num_x) + '\n')
        f.write(str(self.cp_num_y) + '\n')
        f.write(str(self.cp_num_z) + '\n')
        f.write('#control grid spacing#\n')
        f.write(str(self.nx) + '\n')
        f.write(str(self.ny) + '\n')
        f.write(str(self.nz) + '\n')
        f.write('#offsets of the control points#\n')
        for x in range(len(self.control_points)):
            for y in range(len(self.control_points[x])):
                for z in range(len(self.control_points[x][y])):
                    f.write(
                        str(self.control_points[x][y][z][0]) + ' ' + str(self.control_points[x][y][z][1]) + ' ' + str(
                            self.control_points[x][y][z][2]) + '\t')
                f.write('\n')
            f.write('\n')
        f.close()
        return

    
    def B(self, i, u):
        if i == 0:
            return (1 - u) ** 3 / 6
        elif i == 1:
            return (3 * u ** 3 - 6 * u ** 2 + 4) / 6
        elif i == 2:
            return (-3 * u ** 3 + 3 * u ** 2 + 3 * u + 1) / 6
        elif i == 3:
            return u ** 3 / 6
        
    
    def Bezier(self, i, u):  
        if i == 0:
            return (1 - u) ** 3
        elif i == 1:
            return (3 * u ** 3 - 6 * u ** 2 + 3*u)
        elif i == 2:
            return (-3 * u ** 3 + 3 * u ** 2)
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
        result = np.array([0., 0., 0.])
        for l in range(4):
            if 0 <= i + l < self.cp_num_x:
                for m in range(4):
                    if 0 <= j + m < self.cp_num_y:
                        for n in range(4):
                            if 0 <= k + n < self.cp_num_z:
                                result = result + self.B(l, u) * self.B(m, v) * self.B(n, w) * self.control_points[i + l][j + m][k + n]
        return result

    def changed_reset(self):
        del self.changed
        self.changed = {}

    def changed_update(self, id, location):
        self.changed[id] = location

    # Change one control point, we will get the [u,v,w] of the control point.
    # def update_control_point(self, changed_control_point, change):
    #     [u, v, w] = changed_control_point
    #     self.control_points[u][v][w] += change
    #     self.control_points_location[u][v][w] += change
    #     for i in range(len(self.object_points)):
    #         self.object_points[i]=self.T_local(changed_control_point,self.object_points[i])
    #     return self.object_points

    def update_control_point(self):
        # tmp = copy.deepcopy(self.object_points)
        # result = []
        for (u, v, w), new_location in self.changed.items():
            self.control_points[u][v][w] = new_location - self.control_points_location[u][v][w]
        # for i in range(len(self.object_points)):
        #     change_point=self.T_local([u,v,w],tmp[i])
        #     if change_point[0]==0 and change_point[1]==0 and change_point[2]==0:
        #         continue
        #     else:
        #         result.append([i,self.object_points[i]+change_point])
        # return result






