import os
import pickle
import threading



# initialization code
def init():
    global maxMetaDataSize, metaData, SSD, voids, pwd, metas, lock

    maxMetaDataSize = 2**10

    # loading directory structure
    if os.path.exists('sample.data'):
        SSD      = open('sample.data', 'rb+')
        metaData = pickle.loads(SSD.read(maxMetaDataSize))
    else:
        SSD      = open('sample.data', 'wb+')
        metaData = {
            0: [],
            1: {
                '.': None,
            }
        }
        metaData[1]['~'] = metaData[1]
        save()
        
    # setting root and present working directory
    voids = metaData[0]
    pwd   = metaData[1]
    metas = ('~', '.')
    lock  = threading.Lock()

# code for serialization and saving
def save():
    SSD.seek(0)
    SSD.write(b' ' * maxMetaDataSize)
    SSD.seek(0)
    SSD.write(pickle.dumps(metaData))
    SSD.seek(maxMetaDataSize)




# low level functions

def list_(curr):
    return [ name for name in curr if name not in metas ]

def path_(curr):
    
    if curr['.'] is None: return '~'

    for name in curr['.']:
        if curr['.'][name] is curr:
            return path_(curr['.']) + f'/{name}'

def dir_(curr, path):

    for name in path.split('/'): curr = curr[name]
    assert type(curr) is dict, f'{path}: no such directory exists'

    return curr

def create_(curr, name, isdir):

    if name in metas: return

    curr[name] = {
        '~': dir_(curr, '~'), 
        '.': curr,
        
    } if isdir else [] 

def dealloc_(name, curr):

    if type(curr) is list:
        voids.extend(curr)
        return

    for name in list_(curr): dealloc_(name, curr[name])

def tree_(curr, depth= 0):
    r = '~'
    if type(curr) is list:  print(': ', curr, end= ''); return
        # return f': {curr}' 

    for name in list_(curr):
        # r = f'\n{ "   "*depth }{ name }'    
        # r += tree_(curr[name], depth+1)
        print('\n', '    '*depth, name, end= '')
        tree_(curr[name], depth+1)

    return r



# system functions

def quit():
    save(); print(); exit()

def help():
    print('''
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
        ''')

def chdir(path):
    global pwd

    curr = dir_(pwd, path)
    pwd = curr

def create1(name):
    create_(pwd, name, False)

def create2(name):
    create_(pwd, name, True)

def move(name, path):                   # assert statement
    
    curr = dir_(pwd, path)
    assert name in pwd, f'{name}: no such directory'
    curr[name] = pwd[name]
    del pwd[name]

def delete(name):                       # assert statement

    assert name in pwd, f'{name}: no such directory'
    dealloc_(name, pwd[name])
    del pwd[name]

def tree():
    print('~', end= '')
    tree_(dir_(pwd, '~'))
    print()

    # return tree_(dir_(pwd, '~'))

def path():
    print(path_(pwd))
    # return path_(pwd)

def lis():
    print(*list_(pwd), sep= '   ')
    # return 

def read(path, start= 0, size= -1):

    start = int(start)
    size  = int(size)
    
    f = File(path)
    f.seek(start)
    print('\n>', f.read(size), end= '\n\n')
    f.close()

def write(path, data, at= 0):

    at = int(at)

    f = File(path)
    f.seek(at)
    f.write(data)
    f.close()

def append(path, data, at= -1): 

    at = int(at)

    f = File(path)
    f.seek(at)
    f.write(data, overwrite= False)
    f.close()


# file class 

class File():

    def __init__(self, path):

        tmp = path.rsplit('/', 1)

        self.name  = tmp[-1]
        self.dir   = pwd if len(tmp) == 1 else dir_(pwd, tmp[0])
        self.ptr   = 0
        self.data  = b''        
        self.ptrs  = self.dir[self.name]


        assert type(self.ptrs) is list, f'{self.name}, is not a file'                   # assertion statement

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
        assert 0 <= pos <= self.size(), f'File pointer out of range. File size is {self.size()}'    # assertion statement
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
                  + data                    \
                  + self.data[end:]

    def append(self, data):

        data = data.encode()
        self.data = self.data[:self.ptr] \
                  + data                 \
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


# debugging functions 

def dump():

    SSD.seek(maxMetaDataSize)
    print(SSD.read())
    print(metaData[0])


# thread function
def foo(id):

    with open(f'input_thread_{id}.txt', 'r') as f:
        commands = f.readlines()

    for command in commands:

        stmt = command.replace('\n', '').split(' ')
        case = stmt[0]
        args = stmt[1:]

        try:
            assert case in switch, f'{case}: command not found'

            with lock: r = switch[case](*args); save(); print(r)
        
        except (KeyboardInterrupt, EOFError): quit()
        except AssertionError as e          : print(e)
        #except Exception as e               : print(type(e), e, sep= '\n')

    #with open(f'output_thread_{id}.txt', 'w') as f:
    #    pass


# CLI 

#PS1 = '£ '
PS1 = '¥ '
#PS1 = '• '

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
    'dump'  : dump,
}

if __name__ == '__main__':

    init()
    
    while True:
            
        save()
        stmt = input(PS1).split(' ')
        case = stmt[0]
        args = stmt[1:]

        try:
            assert case in switch, f'{case}: command not found'
            switch[case](*args)
        
        except (KeyboardInterrupt, EOFError): quit()
        except AssertionError as e          : print(e)
        #except Exception as e               : print(type(e), e, sep= '\n')

