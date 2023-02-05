import socketserver
from http.server import HTTPServer
from threading import Thread, Event

import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer

from UnrealBS.Config import Config

from UnrealBS.Server.OrderHandler import OrderHandler
from UnrealBS.Server.RecipeHandler import RecipeHandler
from UnrealBS.Server.WorkerHandler import WorkerHandler
from UnrealBS.Server.APIHandler import APIHandler


class Server:
    def __init__(self):
        self.config = Config()
        self.kill_event = Event()

        self.recipe_handler = RecipeHandler()
        self.order_handler = OrderHandler(self, self.try_startNextOrder)
        self.worker_handler = WorkerHandler(self.try_startNextOrder)

        self.rpc_server = SimpleXMLRPCServer((self.config.args.server_host, self.config.args.server_port))

        self.setup_RPCServer()

        self.httpd = HTTPServer((self.config.args.server_host, self.config.args.server_port - 1),
                                APIHandler)
        self.httpd_thread = Thread(target=self.httpd.serve_forever)

    def setup_RPCServer(self):
        self.rpc_server.register_function(self.worker_handler.rpc_register, 'registerWorker')
        self.rpc_server.register_function(self.worker_handler.rpc_deregister, 'deregisterWorker')
        self.rpc_server.register_function(self.worker_handler.rpc_update, 'updateWorkerStatus')

        self.rpc_server.register_function(self.order_handler.update_order, 'updateOrderStatus')

        self.rpc_thread = Thread(target=self.rpc_server.serve_forever)
        self.rpc_thread.daemon = True

    def try_startNextOrder(self):
        # FIXME
        # its not atomic and i think
        # it can fail in some esoteric moment
        # but not for now
        self.config.server_logger.debug('Checking to assign next order')

        worker = self.worker_handler.get_free_worker()
        if worker is None:
            self.config.server_logger.debug('No worker is free')
            return

        order = self.order_handler.get_queued_order()
        if order is None:
            self.config.server_logger.debug('No order is in queue')
            return

        with xmlrpc.client.ServerProxy(f'http://localhost:{worker.port}') as proxy:
            try:
                self.config.server_logger.info(f'Sending order[{order.id}] to {worker.id} @ {worker.port}')
                proxy.receiveOrder(order.as_json(to_str=True))
                self.worker_handler.assign_order(order.id, worker.id)
            finally:
                pass
    def kill(self):
        self.config.server_logger.warning('Server is killed!')
        self.kill_event.set()
        self.clean_up()

    def clean_up(self):
        pass

    def run(self):
        self.config.server_logger.info(f'Starting RPC server @ {self.config.args.server_host}:{self.config.args.server_port}')
        self.rpc_thread.start()
        self.config.server_logger.info(f'Starting API(JSON) server @ {self.config.args.server_host}:{self.config.args.server_port - 1}')
        self.httpd_thread.start()
        self.kill_event.wait()