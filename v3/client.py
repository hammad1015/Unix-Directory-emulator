import socket as sc

PORT = 1095
IP   = sc.gethostname()
# IP   = input('Please enter server IP: ')
ADDR = IP, PORT

soc = sc.socket()
soc.connect(ADDR)

while True:
    username = input('Please enter your username: ').encode()
    if username: break
    
soc.send(username)

PS1 = '¥ '
while True:

    while True:
        inp = input(PS1).encode()
        if inp: break
    
    soc.send(inp)

    out = soc.recv(100).decode()
    if not out: break

    print(out)


print('''
server terminated connection unexpectidly
''')