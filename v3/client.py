import socket as sc

PORT = 9999
IP   = sc.gethostname()
ADDR = IP, PORT

soc = sc.socket()
soc.connect(ADDR)

PS1 = '¥ '
out = True
while out:

    inp = input(PS1).encode()
    soc.send(inp)

    out = soc.recv(100).decode()
    print(out)
