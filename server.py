import socket
import threading
import os

SERVER_DIR = "server_files"

HOST = "127.0.0.1"
PORT = 9090

lock = threading.Lock()


def handle_list(client_socket):
    """Обрабатывает команду LIST — отправляет список файлов"""
    files = os.listdir(SERVER_DIR)
    if files:
        response = "OK|" + ",".join(files)
    else:
        response = "OK|Папка пуста"
    client_socket.send(response.encode())


def handle_upload(client_socket, filename, filesize):
    """Обрабатывает команду UPLOAD — принимает файл от клиента"""
    if filesize == 0:
        client_socket.send("ERROR|Файл пустой".encode())
        return

    client_socket.send("OK".encode())

    filepath = os.path.join(SERVER_DIR, filename)

    received = 0

    with lock:
        with open(filepath, "wb") as f:
            while received < filesize:
                chunk = client_socket.recv(1024)
                if not chunk:
                    break
                f.write(chunk)
                received += len(chunk)

    client_socket.send("OK".encode())
    print(f"Файл '{filename}' получен ({received} байт)")


def handle_download(client_socket, filename):
    """Обрабатывает команду DOWNLOAD — отправляет файл клиенту"""
    filepath = os.path.join(SERVER_DIR, filename)

    if not os.path.exists(filepath):
        client_socket.send("ERROR|Файл не найден".encode())
        return

    filesize = os.path.getsize(filepath)

    client_socket.send(f"OK|{filesize}".encode())

    import time
    time.sleep(0.1)

    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(1024)
            if not chunk:
                break
            client_socket.send(chunk)

    print(f"Файл '{filename}' отправлен ({filesize} байт)")


def handle_client(client_socket, address):
    """Основная функция обработки клиента — работает в отдельном потоке"""
    print(f"Клиент подключился: {address}")

    while True:
        try:
            data = client_socket.recv(1024).decode()

            if not data:
                break
            parts = data.split("|")
            command = parts[0]

            if command == "LIST":
                handle_list(client_socket)

            elif command == "UPLOAD":
                filename = parts[1]
                filesize = int(parts[2])
                handle_upload(client_socket, filename, filesize)

            elif command == "DOWNLOAD":
                filename = parts[1]
                handle_download(client_socket, filename)

            elif command == "EXIT":
                client_socket.send("OK".encode())
                break

            else:
                client_socket.send("ERROR|Неизвестная команда".encode())

        except Exception as e:
            print(f"Ошибка при работе с клиентом {address}: {e}")
            break

    client_socket.close()
    print(f"Клиент отключился: {address}")


def start_server():
    """Запускает сервер"""
    if not os.path.exists(SERVER_DIR):
        os.makedirs(SERVER_DIR)

    server_socket = socket.socket()

    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((HOST, PORT))

    server_socket.listen(5)

    server_socket.settimeout(1.0)

    print(f"Сервер запущен на {HOST}:{PORT}")
    print(f"Файлы хранятся в папке: {SERVER_DIR}")
    print("Для остановки нажмите Ctrl+C")

    try:
        while True:
            try:
                client_socket, address = server_socket.accept()
            except socket.timeout:
                continue

            thread = threading.Thread(target=handle_client, args=(client_socket, address))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("\nСервер остановлен")
        server_socket.close()

if __name__ == "__main__":
    start_server()
