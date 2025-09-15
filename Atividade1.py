import multiprocessing as mp
import time
import random

# Função que representa um nó do sistema distribuído
def node(node_id, inboxes):
    other_inboxes = [q for i, q in enumerate(inboxes) if i != node_id]
    my_inbox = inboxes[node_id]

    active_nodes = {i: False for i in range(len(inboxes))}

    while True:
        # 1. Envia mensagem "estou vivo" para os outros
        msg = f"Node {node_id} está ativo"
        for q in other_inboxes:
            q.put((node_id, msg))

        # 2. Processa mensagens recebidas
        while not my_inbox.empty():
            sender, message = my_inbox.get()
            active_nodes[sender] = True
            print(f"[Node {node_id}] recebeu de Node {sender}: {message}")

        # 3. Exibe visão unificada
        print(f"[Node {node_id}] Visão global: {active_nodes}")

        # Espera um pouco antes do próximo ciclo
        time.sleep(random.uniform(1, 2))


if __name__ == "__main__":
    NUM_NODES = 3
    queues = [mp.Queue() for _ in range(NUM_NODES)]
    processes = []

    # Cria 3 nós em paralelo
    for i in range(NUM_NODES):
        p = mp.Process(target=node, args=(i, queues))
        p.start()
        processes.append(p)

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        print("\nEncerrando sistema distribuído...")
        for p in processes:
            p.terminate()
