import socket
import os

CLIENT_DIR = ""

HOST = "127.0.0.1"
PORT = 9090


def send_list(sock):
    """Запрашивает список файлов на сервере"""
    sock.send("LIST".encode())

    response = sock.recv(1024).decode()
    parts = response.split("|")

    if parts[0] == "OK":
        print("Файлы на сервере:")
        print(parts[1])
    else:
        print(f"Ошибка: {parts[1]}")


def send_upload(sock, filename):
    """Отправляет файл на сервер"""
    filepath = os.path.join(CLIENT_DIR, filename)

    if not os.path.exists(filepath):
        print(f"Файл '{filename}' не найден в папке {CLIENT_DIR}")
        return

    filesize = os.path.getsize(filepath)

    if filesize == 0:
        print("Ошибка: файл пустой")
        return

    sock.send(f"UPLOAD|{filename}|{filesize}".encode())

    response = sock.recv(1024).decode()
    if response != "OK":
        print(f"Сервер отказал: {response}")
        return

    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(1024)
            if not chunk:
                break
            sock.send(chunk)

    response = sock.recv(1024).decode()
    if response == "OK":
        print(f"Файл '{filename}' успешно загружен на сервер")
    else:
        print(f"Ошибка при загрузке: {response}")


def send_download(sock, filename):
    """Скачивает файл с сервера"""
    sock.send(f"DOWNLOAD|{filename}".encode())

    response = sock.recv(1024).decode()
    parts = response.split("|")

    if parts[0] == "ERROR":
        print(f"Ошибка: {parts[1]}")
        return

    filesize = int(parts[1])

    filepath = os.path.join(CLIENT_DIR, filename)
    received = 0

    with open(filepath, "wb") as f:
        while received < filesize:
            chunk = sock.recv(1024)
            if not chunk:
                break
            f.write(chunk)
            received += len(chunk)

    print(f"Файл '{filename}' скачан в папку {CLIENT_DIR} ({received} байт)")


def main():
    """Основная функция клиента"""
    global CLIENT_DIR

    name = input("Введите ваше имя: ").strip()
    CLIENT_DIR = f"client_files_{name}"

    if not os.path.exists(CLIENT_DIR):
        os.makedirs(CLIENT_DIR)
        print(f"Создана папка: {CLIENT_DIR}")

    sock = socket.socket()

    try:
        sock.connect((HOST, PORT))
        print(f"Подключено к серверу {HOST}:{PORT}")
    except Exception as e:
        print(f"Не удалось подключиться к серверу: {e}")
        return

    print("Команды: LIST | UPLOAD <имя_файла> | DOWNLOAD <имя_файла> | EXIT")

    while True:
        user_input = input("\n> ").strip()

        if not user_input:
            continue

        parts = user_input.split()
        command = parts[0].upper()

        try:
            if command == "LIST":
                send_list(sock)

            elif command == "UPLOAD":
                if len(parts) < 2:
                    print("Использование: UPLOAD <имя_файла>")
                    continue
                send_upload(sock, parts[1])

            elif command == "DOWNLOAD":
                if len(parts) < 2:
                    print("Использование: DOWNLOAD <имя_файла>")
                    continue
                send_download(sock, parts[1])

            elif command == "EXIT":
                sock.send("EXIT".encode())
                sock.recv(1024) 
                print("Отключение от сервера")
                break

            else:
                print("Неизвестная команда. Доступны: LIST, UPLOAD, DOWNLOAD, EXIT")

        except Exception as e:
            print(f"Ошибка соединения: {e}")
            break

    sock.close()

if __name__ == "__main__":
    main()
