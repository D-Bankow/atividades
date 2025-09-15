import socket
import threading

# --- Servidor ---
def servidor():
    host = "127.0.0.1"
    port = 7000

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen()
    print(f"[Servidor] Aguardando conexões em {host}:{port}...")

    def handle_client(conn, addr):
        print(f"[Servidor] Conectado a {addr}")
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break
            try:
                resultado = eval(data)  # processa expressão
                conn.send(f"Resultado: {resultado}".encode())
            except Exception as e:
                conn.send(f"Erro: {e}".encode())
        conn.close()

    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

# --- Cliente ---
def cliente():
    host = "127.0.0.1"
    port = 7000

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    print(f"[Cliente] Conectado ao servidor {host}:{port}")

    while True:
        expr = input("Digite expressão (ex: 2+3*4) ou 'sair': ")
        if expr.lower() == "sair":
            break
        s.send(expr.encode())
        resposta = s.recv(1024).decode()
        print("[Servidor respondeu]", resposta)

    s.close()

# --- Main ---
if __name__ == "__main__":
    print("Escolha:")
    print("1 - Servidor")
    print("2 - Cliente")
    escolha = input("Digite: ")
    if escolha == "1":
        servidor()
    else:
        cliente()
