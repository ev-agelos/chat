import socket
import io
import sys
from collections import deque
from select import select


def receive_messages(sock):
    while 1:
        yield sock
        server_msg = sock.recv(1024)
        if not server_msg:
            break
        print(server_msg.decode('ascii'), end='')


def send_input(sock):
    while 1:
        yield sys.stdin
        data = input()
        sock.sendall(data.encode('ascii'))


def main(sock):
    tasks = deque()
    wait = {}
    tasks.append(send_input(sock))
    tasks.append(receive_messages(sock))

    while 1:
        while not tasks:
            can_read, _, _ = select(wait, [], [])
            for s in can_read:
                tasks.append(wait.pop(s))

        task = tasks.popleft()
        try:
            what = next(task)
        except StopIteration:
            break

        if isinstance(what, socket.socket):
            wait[what] = task
        elif isinstance(what, io.TextIOWrapper):
            wait[what] = task
        else:
            raise RuntimeError('ARG!')


if __name__ == '__main__':
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # avoid 'address already in use' problems
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        host, port = '127.0.0.1', 4444
        try:
            sock.connect((host, port))
            main(sock)
        except KeyboardInterrupt:
            sock.shutdown(socket.SHUT_WR)
        except ConnectionRefusedError:
            print("Could not connect to host.")
