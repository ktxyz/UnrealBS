import json
import os
from dataclasses import dataclass
from queue import Queue

from threading import Thread, Lock, Event

import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer

from UnrealBS.Common import Recipe, Order, OrderStatus
from UnrealBS.Worker import WorkerStatus, WorkerData


class Server:
    # TODO
    # Finish basic functionality to the point of scripts correctly running

    # TODO
    # Split class into subclasses (pref one per thread like:
    def __init__(self):
        self.kill_event = Event()

        self.workers_lock = Lock()
        self.registered_workers = {}

        self.rpc_server = SimpleXMLRPCServer(('localhost', 2137))
        self.setup_RPCServer()

        self.recipes = []
        self.loadRecipes()

        self.orders = {}
        self.orders_queue = Queue()

    def loadRecipes(self):
        cwd = os.getcwd()
        directory = os.path.join(cwd, 'Examples/Linux')
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                file_path = os.path.join(directory, filename)
                with open(file_path, 'r') as f:
                    self.recipes.append(Recipe(json.load(f)))
                    print(f'Registered new {self.recipes[-1].target} recipe')

    def enqueOrder(self, target, json_data):
        for recipe in self.recipes:
            if recipe.target == target:
                order = Order(recipe, json_data)
                self.orders[order.id] = order
                self.orders_queue.put(order)
                # TODO
                # Make this event on another thread!
                self.try_startNextOrder()
                return True
        return False

    def getOrders(self):
        # TODO
        # Make it thread safe
        return self.orders.values()

    def rpc_register_worker(self, worker_id, worker_port):
        try:
            self.workers_lock.acquire()
            worker_data = WorkerData(worker_id, worker_port, WorkerStatus.FREE)
            self.registered_workers[worker_data.id] = worker_data
            print(f'Registered worker {worker_data.id} at port {worker_data.port}')
            self.try_startNextOrder()
            return True
        finally:
            self.workers_lock.release()

    def rpc_deregister_worker(self, worker_id):
        try:
            self.workers_lock.acquire()
            self.registered_workers.pop(worker_id)
            print(f'Deregistered worker {worker_id}')
            return True
        finally:
            self.workers_lock.release()

    def rpc_update_status_worker(self, worker_id, status_val):
        try:
            self.workers_lock.acquire()
            status = WorkerStatus(status_val)
            self.registered_workers[worker_id].status = status
            print(f'Worker {worker_id} changed status to {status}')
            return True
        except:
            return False
        finally:
            self.workers_lock.release()

    def getWorkers(self):
        # TODO
        # Make it thread safe
        return self.registered_workers.values()

    def setup_RPCServer(self):
        # TODO
        # Create naming conventions for RPC methods, calls, members etc.
        self.rpc_server.register_function(self.rpc_register_worker, 'registerWorker')
        self.rpc_server.register_function(self.rpc_deregister_worker, 'deregisterWorker')
        self.rpc_server.register_function(self.rpc_update_status_worker, 'updateWorkerStatus')

        self.rpc_thread = Thread(target=self.rpc_server.serve_forever)
        self.rpc_thread.daemon = True

    def try_startNextOrder(self):
        if self.orders_queue.empty():
            return

        for worker in self.registered_workers.values():
            if worker.status == WorkerStatus.FREE:
                with xmlrpc.client.ServerProxy(f'http://localhost:{worker.port}') as proxy:
                    try:
                        order = self.orders_queue.get(False)
                        # TODO
                        # Create order manager and worker manager for server
                        self.orders[order.id].status = OrderStatus.IN_PROGRESS
                        print(f'Sending order to {worker.id} @ {worker.port}')
                        proxy.receiveOrder(order.as_json())
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