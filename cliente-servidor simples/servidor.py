# --- Servidor ---
import socket
import threading

def handle_client(conn, addr):
    print(f"[Servidor] Conexão estabelecida com {addr}")
    while True:
        data = conn.recv(1024).decode()
        if not data:
            break
        try:
            # Calcula a expressão recebida
            result = eval(data)
            conn.send(f"Resultado: {result}".encode())
        except Exception as e:
            conn.send(f"Erro: {e}".encode())
    conn.close()

def servidor():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("localhost", 5000))
    s.listen()
    print("[Servidor] Aguardando conexões...")

    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

# --- Cliente ---
def cliente():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("localhost", 5000))
    print("[Cliente] Conectado ao servidor")

    while True:
        expr = input("Digite uma expressão (ex: 2+3*4) ou 'sair': ")
        if expr.lower() == "sair":
            break
        s.send(expr.encode())
        resposta = s.recv(1024).decode()
        print("[Servidor respondeu]", resposta)

    s.close()

if __name__ == "__main__":
    print("Escolha:")
    print("1 - Servidor")
    print("2 - Cliente")
    escolha = input("Digite: ")
    if escolha == "1":
        servidor()
    else:
        cliente()
