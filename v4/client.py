import socket as sc

pkt_size = 2**10

PORT = 1095
# IP   = sc.gethostname()
IP   = input('Please enter server IP: ')
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

    out = soc.recv(pkt_size).decode()
    if not out: break

    if out != ' ': print(out)


print('''
server terminated the connection
''')