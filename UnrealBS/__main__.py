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
        print('Hello')
        q = input()
        print(f'Q: {q}')
        if q == "a":
            target = input('which recipe: ')
            server.order_handler.enqueue_order(server.recipe_handler.get_recipe(target), {'client': 'test'})
        elif q == "lo":
            orders = server.order_handler.get_list()
            for order in orders:
                print(f'Order[{order.id}] status = {order.status.name}')
        elif q == "lw":
            workers = server.worker_handler.get_list(free=False)
            for worker in workers:
                print(f'Worker[{worker.id}] @ {worker.port} status = {worker.status.name}')
        elif q == "k":
            # order_id = input('which order?: ')
            # server.order_handler.kill_order(order_id)

            server.order_handler.kill_order(server.order_handler.get_list()[0].id)

    server.kill()
    worker.kill()