import time
from http.server import HTTPServer
from threading import Thread, Event, Lock

import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer

from UnrealBS.Common.Orders import OrderStatus
from UnrealBS.Config import Config

from UnrealBS.Server.OrderHandler import OrderHandler
from UnrealBS.Server.RecipeHandler import RecipeHandler
from UnrealBS.Server.WorkerHandler import WorkerHandler
from UnrealBS.Server.APIHandler import APIHandler
from UnrealBS.Worker import WorkerStatus


class Server:
    def __init__(self):
        self.config = Config()
        self.kill_event = Event()

        self.order_handler = OrderHandler(self, self.try_startNextOrder)
        self.worker_handler = WorkerHandler(self, self.try_startNextOrder)
        self.recipe_handler = RecipeHandler(self)

        self.rpc_server = SimpleXMLRPCServer((self.config.args.server_host, self.config.args.server_port))
        self.rpc_thread = Thread(target=self.rpc_server.serve_forever)
        self.rpc_thread.daemon = True
        self.setup_RPCServer()

        self.httpd = HTTPServer((self.config.args.server_host, self.config.args.server_port - 1),
                                APIHandler)
        self.httpd_thread = Thread(target=self.httpd.serve_forever)
        self.httpd_thread.daemon = True

        self.queue_lock = Lock()
        self.queue_update_interval = 5  # Check every 5 minutes
        self.queue_thread = Thread(target=self.process_queue)
        self.queue_thread.daemon = True

    def setup_RPCServer(self):
        self.rpc_server.register_function(self.worker_handler.rpc_register, 'registerWorker')
        self.rpc_server.register_function(self.worker_handler.rpc_deregister, 'deregisterWorker')
        self.rpc_server.register_function(self.worker_handler.rpc_update, 'updateWorkerStatus')

        self.rpc_server.register_function(self.order_handler.update_order, 'updateOrderStatus')

    def try_startNextOrder(self):
        self.config.server_logger.debug('Checking to assign next order')

        worker = self.worker_handler.get_free_worker()
        if worker is None:
            self.config.server_logger.debug('No worker is free')
            return

        order = self.order_handler.get_queued_order()
        if order is None:
            self.config.server_logger.debug('No order is in queue')
            return
        try:
            with xmlrpc.client.ServerProxy(f'http://{self.config.args.worker_host}:{worker.port}') as proxy:
                self.config.server_logger.info(f'Sending order[{order.id}] to {worker.id} @ {worker.port}')
                proxy.receiveOrder(order.as_json(to_str=True))
                if self.worker_handler.assign_order(order.id, worker.id) is False:
                    raise Exception('Worker DIDNT TAKE TASK')
                else:
                    self.config.server_logger.debug('WORKER TOOK TASK')
                    # TODO
                    # Find better to handle this race condition
                    self.worker_handler.rpc_update(worker.id, WorkerStatus.BUSY.value)
                    self.order_handler.update_order(order.id, OrderStatus.IN_PROGRESS.value, order.current_step)
        except Exception as e:
            self.config.server_logger.error(f'Error [{e}] - requeuing order [{order.id}]')
            self.order_handler._enqueue_order(order)

    def process_queue(self):
        while True:
            time.sleep(self.queue_update_interval)
            self.order_handler.refresh_orders()
            self.try_startNextOrder()

    def kill(self):
        self.config.server_logger.warning('Server is killed!')
        self.kill_event.set()
        self.clean_up()

    def clean_up(self):
        pass

    def run(self):
        self.config.server_logger.info(f'Starting queue thread [interval: {self.queue_update_interval}]')
        self.queue_thread.start()
        self.config.server_logger.info(
            f'Starting RPC server @ {self.config.args.server_host}:{self.config.args.server_port}')
        self.rpc_thread.start()
        self.config.server_logger.info(
            f'Starting API(JSON) server @ {self.config.args.server_host}:{self.config.args.server_port - 1}')
        self.httpd_thread.start()
        self.kill_event.wait()
        self.config.server_logger.debug('After kill event')
