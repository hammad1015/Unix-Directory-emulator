import os
import pickle
import threading
import socket as sc



# initialization code



maxMetaDataSize = 2**10

# code for serialization and saving
def save():

    SSD.seek(0)
    SSD.write(b' ' * maxMetaDataSize)
    SSD.seek(0)
    SSD.write(pickle.dumps(metaData))
    SSD.seek(maxMetaDataSize)

# initializing directory structure
if not os.path.exists('sample.data'):
    SSD      = open('sample.data', 'wb+')
    metaData = [
        [],
        {'.': None,}
    ]
    metaData[1]['~'] = metaData[1]
    save()
    
# loading directory structure
SSD      = open('sample.data', 'rb+')
metaData = pickle.loads(SSD.read(maxMetaDataSize))

# setting root and present working directory
voids = metaData[0]
pwd   = metaData[1]
metas = {'~', '.'}
lock  = threading.Lock()






# low level functions

def list_(curr):
    return [ name for name in curr if name not in metas ]

def path_(curr):
    
    if curr['.'] is None: return '~'

    for name in curr['.']:
        if curr['.'][name] is curr:
            return path_(curr['.']) + f'/{name}'

def dir_(curr, path):

    for name in path.split('/'): 
        assert name in curr, f'{name}: : no such directory exists'
        curr = curr[name]
        
    assert type(curr) is dict, f'{path}: no such directory exists'

    return curr

def create_(curr, name, isdir):

    assert not name in metas, f'{name}: improper filename'

    curr[name] = {
        '~': dir_(curr, '~'), 
        '.': curr,
        
    } if isdir else [] 

def dealloc_(name, curr):

    if type(curr) is list:
        voids.extend(curr)
        return

    for name in list_(curr): dealloc_(name, curr[name])

def tree_(curr, depth= 1):
    
    r = ''
    if type(curr) is list: 
        return f': {curr}' 

    for name in list_(curr):
        r += f"\n{ '    '*depth }{ name }"
        r += tree_(curr[name], depth+1)

    return r


# thread function
def handle_client(client):

    pwd   = metaData[1]


    # system functions

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

    def chdir(path):
        nonlocal pwd

        curr = dir_(pwd, path)
        pwd = curr

        return ''

    def create1(name):
        create_(pwd, name, isdir= False)
        return ''

    def create2(name):
        create_(pwd, name, isdir= True)
        return ''

    def move(name, path):                   # assert statement
        
        curr = dir_(pwd, path)
        assert name in pwd, f'{name}: no such directory'
        curr[name] = pwd[name]
        del pwd[name]

        return ''

    def delete(name):                       # assert statement

        assert name in pwd, f'{name}: no such directory'
        dealloc_(name, pwd[name])
        del pwd[name]

        return ''

    def tree():
        return '~' + tree_(dir_(pwd, '~'))

    def path():
        return path_(pwd)

    def lis():
        return '   '.join(list_(pwd))

    def read(path, start= 0, size= -1):

        start = int(start)
        size  = int(size)
        
        f = File(path)
        f.seek(start)
        r = f'\n> {f.read(size)} \n'
        f.close()

        return r

    def write(path, data, at= 0):

        at = int(at)

        f = File(path)
        f.seek(at)
        f.write(data)
        f.close()

        return ''

    def append(path, data, at= -1): 

        at = int(at)

        f = File(path)
        f.seek(at)
        f.write(data, overwrite= False)
        f.close()

        return ''


    # file class 

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



    username = client.recv(100).decode()

    while True:

        command = client.recv(pkt_size).decode()
        if not command: break

        stmt    = command.replace('\n', '').split(' ')
        case    = stmt[0]
        args    = stmt[1:]



        with lock: 
            try: 
                r = switch[case](*args)
            except AssertionError as e  : r = f'{ e }'
            except KeyError             : r = 'command not found'
            except TypeError            : r = 'improper parameters'
            except Exception            : r = 'unknown error'

        r = ' ' if not r else r
        
        client.send(r.encode())

    with lock: save()

    del threads[client]




threads = {}

pkt_size = 2**10

PORT = 1095
IP   = sc.gethostname(); print(f'server IP address: {IP}')
ADDR = IP, PORT

main = sc.socket()
main.bind(ADDR)
main.listen()

while True:
    try:
        client, _ = main.accept()

        threads[client] = threading.Thread(target= handle_client, args= (client,))
        threads[client].start()


    except Exception as e:
        main.close()
        save()
        exit()