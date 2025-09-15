import multiprocessing as mp
import time
import random

class LamportProcess(mp.Process):
    def __init__(self, proc_id, inboxes, log):
        super().__init__()
        self.proc_id = proc_id
        self.inboxes = inboxes
        self.inbox = inboxes[proc_id]
        self.clock = 0
        self.log = log

    def send(self, dest):
        """Envia mensagem com timestamp para outro processo"""
        self.clock += 1
        msg = (self.proc_id, self.clock, f"Msg de P{self.proc_id} -> P{dest}")
        self.inboxes[dest].put(msg)
        self.log.put((self.clock, f"P{self.proc_id} enviou para P{dest}"))

    def local_event(self):
        """Evento local"""
        self.clock += 1
        self.log.put((self.clock, f"P{self.proc_id} executou evento local"))

    def receive(self):
        """Processa mensagens recebidas"""
        while not self.inbox.empty():
            sender, ts, text = self.inbox.get()
            self.clock = max(self.clock, ts) + 1
            self.log.put((self.clock, f"P{self.proc_id} recebeu de P{sender}: {text}"))

    def run(self):
        for _ in range(5):  # cada processo executa 5 passos
            action = random.choice(["local", "send", "recv"])
            if action == "local":
                self.local_event()
            elif action == "send":
                dest = random.choice([i for i in range(len(self.inboxes)) if i != self.proc_id])
                self.send(dest)
            elif action == "recv":
                self.receive()
            time.sleep(random.uniform(0.5, 1.5))
        # processa mensagens restantes
        self.receive()

def main():
    N = 3  # número de processos
    inboxes = [mp.Queue() for _ in range(N)]
    log = mp.Queue()

    processes = [LamportProcess(i, inboxes, log) for i in range(N)]
    for p in processes:
        p.start()
    for p in processes:
        p.join()

    # Coleta e ordena eventos por timestamp lógico
    events = []
    while not log.empty():
        events.append(log.get())
    events.sort(key=lambda x: x[0])

    print("\n=== Ordem Lógica dos Eventos ===")
    for ts, ev in events:
        print(f"[{ts}] {ev}")

if __name__ == "__main__":
    main()
