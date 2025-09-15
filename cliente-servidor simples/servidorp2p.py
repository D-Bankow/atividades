import socket
import threading

PORTA = 6000

def ouvir(peer_socket):
    while True:
        data, addr = peer_socket.recvfrom(1024)
        print(f"[Recebido de {addr}] {data.decode()}")

def peer():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("localhost", PORTA))

    threading.Thread(target=ouvir, args=(s,), daemon=True).start()

    print("[P2P] Peer iniciado na porta", PORTA)
    while True:
        msg = input("Digite mensagem (ou 'sair'): ")
        if msg.lower() == "sair":
            break
        destino = input("Enviar para porta: ")
        s.sendto(msg.encode(), ("localhost", int(destino)))

if __name__ == "__main__":
    peer()
