import os
import pickle


# initialization code
def init():
    global maxMetaDataSize, metaData, SSD, holes, pwd, metas

    maxMetaDataSize = 2**10

    # loading directory structure
    if os.path.exists('sample.data'):
        SSD      = open('sample.data', 'rb+')
        metaData = pickle.loads(SSD.read(maxMetaDataSize))
    else:
        SSD      = open('sample.data', 'wb+')
        metaData = {
            'h':[],
            '~':{
                '.': None,
            }
        }
        metaData['~']['~'] = metaData['~']
        save()
        
    # setting root and present working directory
    holes = metaData['h']
    pwd   = metaData['~']
    metas = ('~', '.')


def save():
    SSD.seek(0)
    SSD.write(b' ' * maxMetaDataSize)
    SSD.seek(0)
    SSD.write(pickle.dumps(metaData))
    SSD.seek(maxMetaDataSize)





def list_(curr):
    return [ name for name in curr if name not in metas ]


def path_(curr):
    
    if curr['.'] is None: return '~'

    for name in curr['.']:
        if curr['.'][name] is curr:
            return path_(curr['.']) + f'/{name}'


def dir_(path):

    path = path.split('/')
    curr = pwd
    for name in path: curr = curr[name]

    return curr


def create_(name, isdir):

    if name in metas: return

    cpath = path_(pwd)
    pwd[name] = {
        '~': dir_('~'), 
        '.': dir_(cpath),
        
    } if isdir else [] 


def dealloc_(name, curr):

    if type(curr) is list:
        holes.extend(curr)
        return

    for name in list_(curr): dealloc_(name, curr[name])


def tree_(curr, depth= 0):
   
    if type(curr) is list: return

    for name in list_(curr):
        print('    '*depth, name)
        tree_(curr[name], depth+1)








def chdir(path):
    global pwd
    pwd = dir_(path)

def create1(name):
    create_(name, False)

def create2(name):
    create_(name, True)

def delete(name):
    dealloc_(name, pwd[name])
    del pwd[name]

def tree():
    print('~')
    tree_(dir_('~'))

def path():
    print(path_(pwd))

def lis():
    print(*list_(pwd), sep= '\t')


# system functions

def _abs(path):
    return path if path.startswith('~') else f'{PATH}/{path}' if path else PATH

def _dir(path):

    curr  = metaData
    path  = _abs(path)
    trace = path.split('/')

    for dname in trace:
        assert dname in curr       , f'{path}: No such file or directory'
        assert _isdir(curr[dname]), f'{path}: Not a directory'
        
        curr = curr[dname]

    return curr

def _mkdir(path):

    curr  = metaData
    path  = _abs(path)
    trace = path.split('/')

    for dname in trace:
        if not dname in curr:
            curr[dname] = {}

        curr = curr[dname]

    return curr

def _isdir(obj):
    return type(obj) == dict

def _delete(obj):

    if not _isdir(obj):
        holes.extend(obj)
        return

    for el in obj: 
        _delete(el)

def _split(path):
    path = _abs(path)
    i = path.rfind('/')

    return path[:i], path[i+1:]

def mkdir(*paths):

    for path in paths:
        _mkdir(path)

def create(*paths):                             ##### potential error
    paths = [ _split(path) for path in paths ]

    for path, fname in paths:
        d = _mkdir(path)
        assert not (fname in d) or _isdir(d[fname]), f'file {path}/{fname} already exists'
        d[fname] = []

def delete(*pfnames):
    pfnames = [ _split(pfname) for pfname in pfnames ]
    '''
    objs = [
        _dir(path)[fname]
        for path, fname in pfnames
    ]
    for obj in objs: _delete(obj)
    '''
    for path, fname in pfnames:
        _delete(_dir(path)[fname])
        del      _dir(path)[fname]

def chdir(path):
    global PATH
    
    _dir(path)
    PATH = _abs(path)

def move(fname, path):
    
    _dir(path)[fname] = _dir(PATH)[fname]
    del _dir(PATH)[fname]

def mem_map():
    print(*_dir(PATH), sep= '\t')

def print_dir():
    print(PATH)

def read(path, frm= 0, size= -1):
    f = File(path)
    #f.seek(frm)
    print()
    print(f.read(size).decode())
    print()
    f.close()

def write(path, text, at= 0):
    f = File(path)
    f.seek(at)
    f.write(text)
    f.close()

def append(path, text, at= -1): 
    pass

def quit():
    save(); print(); exit()

def dump():
    '''
    SSD.seek(0)
    print(SSD.read())
    print(metaData)
    '''
    print(
        json.dumps(metaData, indent= '| ')\
            .replace('{', '').replace('}', '')\
                .replace('[', '').replace(']', '')
        )

def help():
    print(
        '''
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
    )

class File():

    def __init__(self, path):
        path, fname = _split(path)

        self.chunks = _dir(path)[fname]
        self.ptr    = 0

    def size(self):
        return sum(self.chunks[1::2])

    def seek(self, pos):
        s = self.size()
        if ~pos: pos = s
        assert 0 <= pos <= s, f'File pointer out of range. File size is {s}'
        self.ptr = pos

    def tell(self):
        return self.ptr

    def read(self, size= -1):
        start  = self.ptr
        chunks = self.chunks.copy()
        end    = self.size() if ~size else start + size
        #self.seek(end)
        data = b''

        while chunks:
            s = chunks.pop()
            i = chunks.pop()
            SSD.seek(i)
            data += SSD.read(s)

        return data

    def write(self, data):

        data = data.encode()
        indx = len(data)

        while data:
            if holes:
                i, s = holes.pop(), holes.pop()
                if s > len(data):
                    holes.append(i+len(data))
                    holes.append(s-len(data))

                towrite = data[:s]
                data    = data[s:]
        
            else:
                i = SSD.seek(0, 2)
                s = len(data)

                towrite = data
                data = b''

            i = SSD.seek(i)
            s = SSD.write(towrite)
            self.chunks.append(i)
            self.chunks.append(s)

    def append(self, data, at= -1):

        data = data.encode()

        i = SSD.seek(0, 2)
        s = SSD.write(data)
        self.chunks.append(i)
        self.chunks.append(s)


    def close(self):
        del self




def read(self, size= -1):
        i      = self.ptr
        j      = self.size() if ~size else i + size

        assert j < self.size(), f''

        chunks = self.chunks.copy()[::-1]
        #self.seek(end)
        data = b''

        chunks.pop()
        while chunks:
            
            s = chunks.pop()

            if s < i:
                i -= s
                j -= s
                chunks.pop()
                continue

            if j < s:
                s = j
            
            SSD.seek(i)
            data += SSD.read(s)
            
            i = chunks.pop()

        return data

    def write(self, data):

        data = data.encode()
        indx = len(data)

        while data:
            if holes:
                i, s = holes.pop(), holes.pop()
                if s > len(data):
                    holes.append(i+len(data))
                    holes.append(s-len(data))

                towrite = data[:s]
                data    = data[s:]
        
            else:
                i = SSD.seek(0, 2)
                s = len(data)

                towrite = data
                data = b''

            i = SSD.seek(i)
            s = SSD.write(towrite)
            self.chunks.append(i)
            self.chunks.append(s)




# CLI 

#PS1 = '£ '
PS1 = '¥ '
#PS1 = '• '

'''switch = {
    ''      : lambda: [0],
    'quit'  : quit,
    'pwd'   : print_dir,
    'ls'    : mem_map,
    'touch' : create,
    'rm'    : delete,
    'mkdir' : mkdir,
    'cd'    : chdir,
    'mv'    : move,
    'rd'    : read,
    'wrt'   : write,
    'dump'  : dump,
    'help'  : help,
    'dump'  : dump,
}
'''
switch = {
    ''      : lambda: 0,
    'quit'  : quit,
    'pwd'   : path,
    'cd'    : chdir_,
    'ls'    : lis,
    'touch' : create1,
    'mkdir' : create2,
    'rm'    : delete,
    'mv'    : move,
    'rd'    : read,
    'wrt'   : write,
    'tree'  : tree,
    'help'  : help,
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








