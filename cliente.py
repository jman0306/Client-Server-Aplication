#----------------------CLIENTE----------------------

import socket
import threading
import os

# Función para manejar solicitudes de descarga de otros clientes
def serve_downloads(port, video_dir):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', port))
    server.listen(5)
    print(f"Servidor de descarga activo en el puerto {port}.")

    while True:
        conn, addr = server.accept()
        print(f"Solicitud de descarga recibida desde {addr}")
        try:
            data = conn.recv(1024).decode('utf-8').strip()
            if data.startswith("GET_VIDEO"):
                video_name = data.split()[1]
                video_path = os.path.join(video_dir, video_name)
                if os.path.exists(video_path):
                    conn.sendall(b"OK")
                    file_size = os.path.getsize(video_path)
                    conn.sendall(f"{file_size}\n".encode())  # Enviar tamaño del archivo seguido de un delimitador
                    with open(video_path, 'rb') as file:
                        while chunk := file.read(4096):  # Leer en bloques grandes
                            conn.sendall(chunk)  # Enviar datos binarios al cliente
                    print(f"Video '{video_name}' enviado a {addr}.")
                else:
                    conn.sendall(b"ERROR: Video no encontrado.\n")
            else:
                conn.sendall(b"ERROR:  no reconocido.\n")
        except PermissionError as e:
            print(f"Video no se encuentra en el dispositivo")
        except Exception as e:
            print(f"Error al manejar la solicitud de {addr}: {e}")
        finally:
            conn.close()

# Función para interactuar con el servidor central
def interact_with_server(server_ip, server_port, client_ip, client_port, video_dir):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, server_port))
    print("Conectado al servidor central.")

    def listen_server():
        while True:
            try:
                response = client.recv(1024).decode('utf-8')
                if not response:
                    break
                print(response)
            except:
                break

    # Hilo para escuchar mensajes del servidor
    threading.Thread(target=listen_server, daemon=True).start()

    print("Escribe comandos (INSC, VIDEOS, INFO, DESCARGAR):")
    while True:
        command = input()
        if command.lower() == "exit":
            break
        if command.startswith("DESCARGAR"):
            _, video_name = command.split()
            handle_download_request(server_ip, server_port, video_name, video_dir)
        else:
            client.sendall(command.encode('utf-8'))
    client.close()
   

# Función para manejar la descarga desde otro cliente
def handle_download_request(server_ip, server_port, video_name, video_dir):
    try:
        # Conectar al servidor informativo para obtener IP, puerto y demás detalles
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((server_ip, server_port))
        client.sendall(f"DESCARGAR {video_name}".encode('utf-8'))
        print("------",client.recv(1024).decode('utf-8').strip(), "------")
        response = client.recv(1024).decode('utf-8').strip()
        print(response)
        client.close()
       

        if "ERROR" not in response:
            # Descomponer la respuesta en partes
            target_ip, target_port, video_name, video_dir = response.split(",")
            print(f"Video encontrado en {target_ip}:{target_port}. Iniciando descarga...")
            download_video(target_ip, int(target_port), video_name, video_dir)
        else:
            print(response)
    except Exception as e:
        print(f"Error al manejar la solicitud: {e}")

# Función para descargar un video desde otro cliente
def download_video(target_ip, target_port, video_name, video_dir):
    try:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((target_ip, target_port))
        conn.sendall(f"GET_VIDEO {video_name}".encode('utf-8'))
        response = conn.recv(1024).decode('utf-8').strip()
        if response == "OK":
            print(f"Descargando '{video_name}' de {target_ip}:{target_port}...")
            # Leer hasta encontrar el delimitador '\n'
            file_size = b""
            while not file_size.endswith(b"\n"):
                file_size += conn.recv(1)
            
            file_size = int(file_size.decode().strip())  # Convertir a entero después de decodificar
            print(f"Tamaño del archivo que se va a recibir: {file_size} bytes")
            
            received_size = 0
            bar_length = 50  # Tamaño de la barra
            
            video_path = os.path.join(video_dir, video_name)
            
            with open(video_path, 'wb') as file:
                while received_size < file_size:  # Seguir leyendo hasta alcanzar el tamaño total
                    chunk = conn.recv(4096)  # Leer en bloques
                    file.write(chunk)
                    received_size += len(chunk)
                    # Calcular progreso
                    progress = received_size / file_size
                    block = int(bar_length * progress)
                    bar = f"[{'#' * block}{'.' * (bar_length - block)}]"  # Crear barra
                    print(f"\rProgreso: {bar} {progress * 100:.2f}%", end="")  # Actualizar en la misma línea
                    
            print(f"Video '{video_name}' descargado exitosamente.")
        else:
            print(f"Error del servidor de descarga: {response}")
    except PermissionError as e:
        print(f"Video no encontrado en cliente")
    except Exception as e:
        print(f"Error al descargar el video: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    SERVER_IP = "192.168.160.8"  # Cambia esto a la IP de tu servidor central
    SERVER_PORT = 8000           # Puerto del servidor central
    CLIENT_IP = "192.168.160.37"  # Cambia esto a la IP de este cliente
    CLIENT_PORT = 7000           # Puerto de escucha para descargas
    VIDEO_DIR = "E:/Películas"       # Carpeta donde se almacenan los videos
    # Crear la carpeta de videos si no existe
    if not os.path.exists(VIDEO_DIR):
        os.makedirs(VIDEO_DIR)

    # Inicia el servidor de descarga en un hilo
    threading.Thread(target=serve_downloads, args=(CLIENT_PORT, VIDEO_DIR), daemon=True).start()

    # Interactúa con el servidor central
    interact_with_server(SERVER_IP, SERVER_PORT, CLIENT_IP, CLIENT_PORT, VIDEO_DIR)