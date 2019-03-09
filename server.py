import socket
from select import select
from collections import deque


class Server:

    clients = {}

    def listen_on(self, sock):
        """Listen for new client connections."""
        while 1:
            yield 'recv', sock
            client, address = sock.accept()
            msg = f'{address[0]}:{address[1]} connected.'
            print(msg)
            TASKS.append(self.send(msg))
            TASKS.append(self.bind_client(client, address))

    def bind_client(self, sock, address):
        """Bind client and broadcast its messages."""
        self.clients[sock] = address
        while 1:
            yield 'recv', sock
            data = sock.recv(1024)
            if not data:
                self.unbind_client(sock)
                break
            msg = f'{address[0]}:{address[1]}: ' + data.decode('ascii')
            TASKS.append(self.send(msg))

    def send(self, msg):
        """Send message to all clients."""
        for sock in self.clients.copy():
            yield 'send', sock
            sock.sendall(f'\n{msg}'.encode('ascii'))

    def unbind_client(self, sock):
        """Disconnect socket."""
        address = self.clients.pop(sock)
        msg = f'{address[0]}:{address[1]} disconnected.'
        print(msg)
        TASKS.append(self.send(msg))
        sock.shutdown(socket.SHUT_RDWR)

    def shutdown(self):
        """Shutdown server."""
        self.send('Server shut down.')
        for sock in self.clients:
            sock.shutdown(socket.SHUT_RDWR)


def main():
    recv_wait, send_wait = {}, {}
    while any([TASKS, recv_wait, send_wait]):
        while not TASKS:
            can_recv, can_send, _ = select(recv_wait, send_wait, [])
            for s in can_recv:
                TASKS.append(recv_wait.pop(s))
            for s in can_send:
                TASKS.append(send_wait.pop(s))

        task = TASKS.popleft()
        try:
            why, what = next(task)
        except StopIteration:
            continue

        if why == 'recv':
            recv_wait[what] = task
        elif why == 'send':
            send_wait[what] = task
        else:
            raise RuntimeError('ARG!')


if __name__ == '__main__':
    TASKS = deque()
    HOST, PORT = '127.0.0.1', 4444
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # avoid 'address already in use' problems
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((HOST, PORT))
        sock.listen(5)
        print(f"Listening on {HOST}:{PORT}")
        server = Server()
        TASKS.append(server.listen_on(sock))
        try:
            main()
        except KeyboardInterrupt:
            server.shutdown()
