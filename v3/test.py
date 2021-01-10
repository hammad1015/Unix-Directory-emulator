import os
import pickle
import threading

# import sys
# import time

# for i in range(10, 0, -1):
#     sys.stdout.write(f'\r{ "="*i }>')
#     sys.stdout.flush()
#     time.sleep(0.5)


class MetaData():

    maxSize = 2**10

    # initialising directory structure
    if not os.path.exists('sample.data'):
        data = [
            [],
            {'.': None,}
        ]
        data[1]['~'] = data[1]
        SSD = open('sample.data', 'wb+')
        SSD.write(pickle.dumps(data))
        SSD.close()


    # loading directory structure
    SSD  = open('sample.data', 'rb+')
    data = pickle.loads(SSD.read(maxSize))
        
    # setting root directory, storage holes and thread lock
    holes = data[0]
    root  = data[1]
    metas = {'~', '.'}
    lock  = threading.Lock()


    @classmethod
    def save(cls):

        cls.SSD.seek(0)
        cls.SSD.write(b' ' * cls.maxSize)
        cls.SSD.seek(0)
        cls.SSD.write(pickle.dumps(cls.data))
        cls.SSD.seek(cls.maxSize)
    


class View():

    def __init__(self):
        self.pwd =  MetaData.root


   # low level functions

    def list_(curr):
        return [ name for name in curr if name not in metas ]

    def path_(curr):
        
        if curr['.'] is None: return '~'

        for name in curr['.']:
            if curr['.'][name] is curr:
                return View.path_(curr['.']) + f'/{name}'

    def dir_(curr, path):

        for name in path.split('/'): curr = curr[name]
        assert type(curr) is dict, f'{path}: no such directory exists'

        return curr

    def create_(curr, name, isdir):

        if name in MetaData.metas: return

        curr[name] = {
            '~': View.dir_(curr, '~'), 
            '.': curr,
            
        } if isdir else [] 

    def dealloc_(name, curr):

        if type(curr) is list:
            MetaData.holes.extend(curr)
            return

        for name in View.list_(curr): View.dealloc_(name, curr[name])

    def tree_(curr, depth= 1):
        r = ''
        if type(curr) is list: return f': {curr}' 

        for name in View.list_(curr):
            r += f'\n{ "   "*depth }{ name }'    
            r += View.tree_(curr[name], depth+1)

        return r


    def quit():
        save(); client.close(); exit()

    def help():
        return '''
            command |argument           |usage

            rm      [file/folder path]  removes file or directory

            touch   [file path]         creates file

            mkdir   [directory name]    creates directory

            mv      [source directory]  move file
                    [target directory]   

            rd      [file path]         read file

            wrt     [file path]         write to file
                    [input data]         

            cd      [path]              change working directory

            pwd                         displays the present working directory

            ls                          list files and folders in current directory

            quit                        exit the file system
            '''

    def chdir(self, path):

        curr = View.dir_(self.pwd, path)
        pwd = curr

        return ''

    def create1(self, name):
        View.create_(self.pwd, name, False)
        return ''

    def create2(self, name):
        View.create_(self.pwd, name, True)
        return ''

    def move(self, name, path):                   # assert statement
        
        curr = View.dir_(self.pwd, path)
        assert name in self.pwd, f'{name}: no such directory'
        curr[name] = self.pwd[name]
        del self.pwd[name]

        return ''

    def delete(self, name):                       # assert statement

        assert name in self.pwd, f'{name}: no such directory'
        View.dealloc_(name, self.pwd[name])
        del self.pwd[name]

        return ''

    def tree(self):
        return '~' + View.tree_(View.dir_(self.pwd, '~'))

    def path(self):
        return View.path_(self.pwd)

    def lis(self):
        return '   '.join(View.list_(self.pwd))

    def read(path, start= 0, size= -1):

        start = int(start)
        size  = int(size)
        
        f = View.File(path)
        f.seek(start)
        r = f'\n> {f.read(size)} \n'
        f.close()

        return r

    def write(path, data, at= 0):

        at = int(at)

        f = View.File(path)
        f.seek(at)
        f.write(data)
        f.close()

        return ''

    def append(path, data, at= -1): 

        at = int(at)

        f = View.File(path)
        f.seek(at)
        f.write(data, overwrite= False)
        f.close()

        return ''

    class File():

        def __init__(self, path):


            tmp = path.rsplit('/', 1)

            self.name  = tmp[-1]
            self.dir   = pwd if len(tmp) == 1 else dir_(pwd, tmp[0])
            self.ptr   = 0
            self.data  = b''        
            self.ptrs  = self.dir[self.name]

            assert type(self.ptrs) is list, f'{self.name}, is not a file'

            tmp = self.ptrs.copy()[::-1]
            while tmp:
                i = tmp.pop()
                s = tmp.pop()

                SSD.seek(i)
                self.data += SSD.read(s)


        def size(self):
            return len(self.data)

        def seek(self, pos):

            if not ~pos: pos = self.size()
            assert 0 <= pos <= self.size(), f'File pointer out of range. File size is {self.size()}'
            self.ptr = pos

        def tell(self):
            return self.ptr

        def read(self, size= -1):

            i = self.ptr
            j = self.ptr + size

            if not ~size: j = self.size()

            self.seek(j)
            return self.data[i: j].decode()

        def write(self, data, overwrite= True):

            end  = min(self.size(), self.ptr + len(data)) #if overwrite else self.ptr

            data = data.encode()
            self.data = self.data[:self.ptr]    \
                    + data                      \
                    + self.data[end:]

        def append(self, data):

            data = data.encode()
            self.data = self.data[:self.ptr]    \
                    + data                      \
                    + self.data[self.ptr:]
            
        def close(self):

            ptrs = self.ptrs
            data = self.data
            temp = []

            j = 0

            while data:

                i = SSD.seek(0, 2)
                m = len(data)

                if voids:
                    i = voids.pop(0)
                    m = voids.pop(0)

                elif ptrs:
                    i = ptrs.pop(0)
                    m = ptrs.pop(0)

                d = data[:m]
                data = data[m:]

                j = SSD.seek(i)
                n = SSD.write(d)
                temp.extend([j, n])

                if n < m: voids.extend([i, m-n])

            self.dir[self.name] = temp
            del self



    switch = {
        ''      : lambda: '',
        'quit'  : quit,
        'pwd'   : path,
        'cd'    : chdir,
        'ls'    : lis,
        'touch' : create1,
        'mkdir' : create2,
        'rm'    : delete,
        'mv'    : move,
        'rd'    : read,
        'wrt'   : write,
        'apd'   : append,
        'tree'  : tree,
        'help'  : help,
    }

    pass








class MyClass():

    classVar = 'it works'

    @staticmethod
    def myFunction():
        print(classVar)

    myFunction.__func__()
    
    