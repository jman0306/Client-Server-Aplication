#!/usr/bin/env python3
# -- coding: utf-8 --
"""
Created on Mon Dec  2 14:05:20 2024

@author: valeriaandrade
"""

#----------------------SERVIDOR----------------------

import socket
import threading
import json

# Base de datos simulada (archivo JSON)
DATABASE_FILE = "server_database.json"

# Inicialización de la base de datos
def initialize_database():
    try:
        with open(DATABASE_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_database(database):
    with open(DATABASE_FILE, 'w') as file:
        json.dump(database, file, indent=4)

# Función para manejar cada cliente
def handle_client(conn, addr, database):
    print(f"Cliente conectado desde {addr}")
    conn.sendall("Bienvenido al servidor central.\n".encode('utf-8'))
    while True:
        try:
            data = conn.recv(1024).decode('utf-8').strip()
            if not data:
                break

            command = data.split()
            if command[0] == "INSC":
                # Registro de cliente
                client_name = command[1]
                ip = command[2]
                port = command[3]
                if client_name not in database:
                    database[client_name] = {"ip": ip, "port": port, "videos": []}
                    save_database(database)
                    conn.sendall("Cliente registrado exitosamente.\n".encode('utf-8'))
                else:
                    conn.sendall("El cliente ya está registrado.\n".encode('utf-8'))
            
            elif command[0] == "VIDEOS":
                # Registro de videos
                client_name = command[1]
                videos = command[2:]
                if client_name in database:
                    database[client_name]["videos"] = videos
                    save_database(database)
                    conn.sendall(b"Videos registrados exitosamente.\n")
                else:
                    conn.sendall("Cliente no registrado. Por favor, regístrese primero con INSC.\n".encode('utf-8'))
            
            elif command[0] == "INFO":
                # Consulta de videos
                video_list = {name: client["videos"] for name, client in database.items() if client["videos"]}
                if video_list:
                    conn.sendall(f"Videos disponibles: {json.dumps(video_list)}\n".encode())
                else:
                    conn.sendall("No hay videos disponibles.\n".encode('utf-8'))
            
            elif command[0] == "DESCARGAR":
                # Solicitar video
                archivo = command[1]
                encontrado  = False
                for client_name, client_info in database.items():
                    if archivo in client_info["videos"]:
                        response = f"{client_info['ip']},{client_info['port']},{archivo},./videos"
                        conn.sendall(response.encode('utf-8'))
                        encontrado = True
                        break
                if not encontrado:
                    conn.send("Archivo no encontrado.".encode('utf-8'))
            
            else:
                conn.sendall("Comando no reconocido.\n".encode('utf-8'))
                
        except Exception as e:
            conn.sendall(f"Error: {str(e)}\n".encode())
            break
    conn.close()
    print(f"Cliente desconectado {addr}")

# Configuración del servidor
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 8000))
    server.listen(5)
    print("Servidor central en espera de conexiones...")
    database = initialize_database()

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr, database))
        thread.start()

if __name__ == "__main__":
    start_server()