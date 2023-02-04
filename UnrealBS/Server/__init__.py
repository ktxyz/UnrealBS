import json
import os
from dataclasses import dataclass
from queue import Queue

from threading import Thread, Lock, Event

import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer

from UnrealBS.Server.OrderHandler import OrderHandler
from UnrealBS.Server.RecipeHandler import RecipeHandler
from UnrealBS.Server.WorkerHandler import WorkerHandler



class Server:
    # TODO
    # Finish basic functionality to the point of scripts correctly running

    def __init__(self):
        self.kill_event = Event()

        self.recipe_handler = RecipeHandler()
        self.order_handler = OrderHandler(self.try_startNextOrder)
        self.worker_handler = WorkerHandler(self.try_startNextOrder)

        self.rpc_server = SimpleXMLRPCServer(('localhost', 2137))
        self.setup_RPCServer()

    def setup_RPCServer(self):
        # TODO
        # Create naming conventions for RPC methods, calls, members etc.
        self.rpc_server.register_function(self.worker_handler.rpc_register, 'registerWorker')
        self.rpc_server.register_function(self.worker_handler.rpc_deregister, 'deregisterWorker')
        self.rpc_server.register_function(self.worker_handler.rpc_update, 'updateWorkerStatus')

        self.rpc_server.register_function(self.order_handler.update_order, 'updateOrderStatus')

        self.rpc_thread = Thread(target=self.rpc_server.serve_forever)
        self.rpc_thread.daemon = True

    def try_startNextOrder(self):
        # TODO
        # its not atomic and i think
        # it can fail in some esoteric moment
        # but not for now
        worker = self.worker_handler.get_free_worker()
        if worker is None:
            return

        order = self.order_handler.get_queued_order()
        if order is None:
            return

        with xmlrpc.client.ServerProxy(f'http://localhost:{worker.port}') as proxy:
            try:
                print(f'Sending order to {worker.id} @ {worker.port}')
                proxy.receiveOrder(order.as_json(to_str=True))
            finally:
                pass
    def kill(self):
        self.kill_event.set()
        self.clean_up()

    def clean_up(self):
        pass

    def run(self):
        self.rpc_thread.start()
        self.kill_event.wait()