import multiprocessing as mp
import time
import random

class Node(mp.Process):
    def __init__(self, node_id, inboxes, state_store):
        super().__init__()
        self.node_id = node_id
        self.inboxes = inboxes
        self.inbox = inboxes[node_id]
        self.active = True  # controla falhas
        self.data = []
        self.state_store = state_store  # memória compartilhada para estado final

    def broadcast(self, msg):
        """Replica mensagem para o outro nó"""
        for i, q in enumerate(self.inboxes):
            if i != self.node_id:
                q.put(("update", msg))

    def recover(self):
        """Recupera estado do outro nó"""
        for i, q in enumerate(self.inboxes):
            if i != self.node_id:
                q.put(("sync_request", self.node_id))

    def run(self):
        while True:
            # Se nó estiver ativo, processa mensagens
            if self.active:
                while not self.inbox.empty():
                    tipo, conteudo = self.inbox.get()
                    if tipo == "insert":
                        self.data.append(conteudo)
                        self.broadcast(conteudo)
                        print(f"[Node {self.node_id}] Inseriu {conteudo} e replicou")
                    elif tipo == "update":
                        self.data.append(conteudo)
                        print(f"[Node {self.node_id}] Recebeu replicação: {conteudo}")
                    elif tipo == "sync_request":
                        # outro nó pediu estado
                        destino = conteudo
                        self.inboxes[destino].put(("sync_response", list(self.data)))
                    elif tipo == "sync_response":
                        # recebeu estado atualizado
                        self.data = conteudo
                        print(f"[Node {self.node_id}] Recuperou estado: {self.data}")
            else:
                # Nó "desligado" (não processa nada)
                time.sleep(1)

            # atualiza estado global para monitorar
            self.state_store[self.node_id] = list(self.data)
            time.sleep(0.5)

def client(inboxes):
    """Cliente que insere dados periodicamente"""
    for i in range(5):
        msg = f"item-{i}"
        inboxes[0].put(("insert", msg))  # envia sempre ao Node 0
        print(f"[Cliente] Inseriu {msg} via Node 0")
        time.sleep(1.5)

def main():
    N = 2
    inboxes = [mp.Queue() for _ in range(N)]
    manager = mp.Manager()
    state_store = manager.dict()

    nodes = [Node(i, inboxes, state_store) for i in range(N)]
    for n in nodes:
        n.start()

    # inicia cliente
    c = mp.Process(target=client, args=(inboxes,))
    c.start()

    # Simula falha do Node 1
    time.sleep(3)
    print("\n*** Falha: Node 1 caiu ***\n")
    nodes[1].active = False

    # Cliente continua inserindo
    time.sleep(4)

    # Node 1 volta e recupera estado
    print("\n*** Node 1 voltou, iniciando recuperação ***\n")
    nodes[1].active = True
    nodes[1].recover()

    # Aguarda cliente terminar
    c.join()
    time.sleep(3)

    print("\n=== Estado Final dos Nós ===")
    for i in range(N):
        print(f"Node {i}: {state_store[i]}")

    for n in nodes:
        n.terminate()

if __name__ == "__main__":
    main()
