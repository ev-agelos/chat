import socket
from select import select
from collections import deque


def release_client(client, address):
    chat_msg = f'{address[0]}:{address[1]} disconnected.'
    print(chat_msg)
    CHAT.send(chat_msg)
    client.shutdown(socket.SHUT_RDWR)


def shutdown_server():
    while CLIENTS:
        address, client = CLIENTS.popitem()
        client.sendall('\nServer shut down.'.encode('ascii'))
        client.shutdown(socket.SHUT_RDWR)


def message_clients():
    while 1:
        msg = yield
        msg = '\n' + msg
        for client in CLIENTS.values():
            client.sendall(msg.encode('ascii'))


def client_handler(client, address):
    msg = f'{address[0]}:{address[1]} connected.'
    CHAT.send(msg)
    CLIENTS[address] = client
    while 1:
        yield 'recv', client
        data = client.recv(1024)
        if not data:
            CLIENTS.pop(address)
            release_client(client, address)
            break
        msg = f"{address[0]}:{address[1]} : " + data.decode('ascii')
        CHAT.send(msg)


def server():
    while 1:
        yield 'recv', sock
        client, address = sock.accept()
        print(f'{address[0]}:{address[1]} connected.')
        tasks.append(client_handler(client, address))


def main():
    while any([tasks, recv_wait, send_wait]):
        while not tasks:
            can_recv, can_send, _ = select(recv_wait, send_wait, [])
            for s in can_recv:
                tasks.append(recv_wait.pop(s))
            for s in can_send:
                tasks.append(send_wait.pop(s))

        task = tasks.popleft()
        try:
            why, what = next(task)
        except StopIteration:
            continue

        if why == 'recv':
            recv_wait[what] = task
        elif why == 'send':
            send_wait[what] = task
        elif why == 'msg':
            pass
        else:
            raise RuntimeError('ARG!')


if __name__ == '__main__':
    HOST, PORT = '127.0.0.1', 4444
    CLIENTS = {}
    tasks = deque()

    recv_wait = {}
    send_wait = {}

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # avoid 'address already in use' problems
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(5)
    print("Listening on {}:{}".format(HOST, PORT))
    CHAT = message_clients()
    CHAT.send(None)
    tasks.append(server())
    try:
        main()
    except KeyboardInterrupt:
        shutdown_server()
