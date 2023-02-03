from threading import Thread

from UnrealBS.Server import Server
from UnrealBS.Worker import Worker


if __name__ == "__main__":
    server = Server()
    worker = Worker(2137)

    s_thread = Thread(target=server.run)
    w_thread = Thread(target=worker.run)


    s_thread.start()
    w_thread.start()

    q = ""
    while q != "q":
        q = input()
        if q == "a":
            server.enqueOrder('example-success', {'client': 'test'})
        elif q == "lo":
            orders = server.getOrders()
            for order in orders:
                print(f'Order[{order.id}] status = {order.status}')
        elif q == "lw":
            workers = server.getWorkers()
            for worker in workers:
                print(f'Worker[{worker.id}] @ {worker.port} status = {worker.status}')

    server.kill()
    worker.kill()