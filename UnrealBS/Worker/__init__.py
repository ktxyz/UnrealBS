import json
import uuid
from enum import IntEnum
from threading import Thread, Event

import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer

from UnrealBS.Common.Recipes import Recipe
from UnrealBS.Common.Orders import Order, OrderStatus
from UnrealBS.Worker.OrderHandler import OrderHandler


class WorkerStatus(IntEnum):
    FREE = 0,
    BUSY = 1


class Worker:
    def __init__(self, server_port):
        self.kill_event = Event()
        self.current_order = None

        self.timeout = False

        self.id = f'worker-{str(uuid.uuid4().hex)[:5]}'
        self.server_port = server_port

        self.order_handler = OrderHandler(self)
        self.order_handler_thread = Thread(target=self.order_handler.process)
        self.order_handler_thread.daemon = True

        self.rpc_server = SimpleXMLRPCServer(('localhost', 2138))
        self.rpc_server_thread = Thread(target=self.rpc_server.serve_forever)
        self.rpc_server_thread.daemon = True
        self.setup_RPCServer()


    def setup_RPCServer(self):
        self.rpc_server.register_function(self.order_handler.rpc_recv_order, 'receiveOrder')
        self.rpc_server.register_function(self.order_handler.rpc_kill_order, 'killOrder')

    def run(self):
        self.rpc_server_thread.start()
        self.order_handler_thread.start()

        with xmlrpc.client.ServerProxy(f'http://localhost:{self.server_port}') as proxy:
            proxy.registerWorker(self.id, 2138)

        self.kill_event.wait()
        self.rpc_server_thread.join()

    def on_killOrder(self):
        print('Im free')
        with xmlrpc.client.ServerProxy('http://localhost:2137') as proxy:
            proxy.updateWorkerStatus(self.id, WorkerStatus.FREE.value)

    def on_startOrder(self):
        with xmlrpc.client.ServerProxy('http://localhost:2137') as proxy:
            proxy.updateWorkerStatus(self.id, WorkerStatus.BUSY.value)
            proxy.updateOrderStatus(self.order_handler.order.id, OrderStatus.IN_PROGRESS.value)

    def on_failOrder(self):
        with xmlrpc.client.ServerProxy('http://localhost:2137') as proxy:
            proxy.updateWorkerStatus(self.id, WorkerStatus.FREE.value)
            if self.timeout:
                proxy.updateOrderStatus(self.order_handler.order.id, OrderStatus.TIMEOUT.value)
            else:
                proxy.updateOrderStatus(self.order_handler.order.id, OrderStatus.FAILED.value)

    def on_cookOrder(self):
        with xmlrpc.client.ServerProxy('http://localhost:2137') as proxy:
            proxy.updateWorkerStatus(self.id, WorkerStatus.FREE.value)
            proxy.updateOrderStatus(self.order_handler.order.id, OrderStatus.COOKED.value)


    def clean_up(self):
        with xmlrpc.client.ServerProxy('http://localhost:2137') as proxy:
            proxy.deregisterWorker(self.id)

    def kill(self):
        self.clean_up()
        self.kill_event.set()
