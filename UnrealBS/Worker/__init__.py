import json
import uuid
from enum import IntEnum
from threading import Thread, Event

import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer

from UnrealBS.Common.Recipes import Recipe
from UnrealBS.Common.Orders import Order, OrderStatus
from UnrealBS.Config import Config
from UnrealBS.Worker.OrderHandler import OrderHandler


class WorkerStatus(IntEnum):
    FREE = 0,
    BUSY = 1


class Worker:
    def __init__(self):
        self.config = Config()

        self.kill_event = Event()
        self.current_order = None

        self.timeout = False

        self.id = f'worker-{str(uuid.uuid4().hex)[:5]}'

        self.server_url = f'http://{self.config.args.server_host}:{self.config.args.server_port}'

        self.order_handler = OrderHandler(self)
        self.order_handler_thread = Thread(target=self.order_handler.process)
        self.order_handler_thread.daemon = True

        self.rpc_server = SimpleXMLRPCServer((self.config.args.worker_host, self.config.args.worker_port))
        self.rpc_server_thread = Thread(target=self.rpc_server.serve_forever)
        self.rpc_server_thread.daemon = True
        self.setup_RPCServer()


    def setup_RPCServer(self):
        self.rpc_server.register_function(self.order_handler.rpc_recv_order, 'receiveOrder')
        self.rpc_server.register_function(self.order_handler.rpc_kill_order, 'killOrder')

    def run(self):
        self.config.worker_logger.info(f'Starting RPC server @ {self.config.args.worker_host}:{self.config.args.worker_port}')

        self.rpc_server_thread.start()
        self.order_handler_thread.start()

        try:
            with xmlrpc.client.ServerProxy(self.server_url) as proxy:
                proxy.registerWorker(self.id, self.config.args.worker_port)
        except ConnectionRefusedError as e:
            self.config.worker_logger.error(f'Can\'t conect to server @ {self.server_url}')
            return
        self.kill_event.wait()
        self.order_handler_thread.join()

    def on_killOrder(self):
        self.config.worker_logger.info('Order was cancelled')
        with xmlrpc.client.ServerProxy(self.server_url) as proxy:
            proxy.updateWorkerStatus(self.id, WorkerStatus.FREE.value)

    def on_startOrder(self):
        self.config.worker_logger.info('Order was started')
        try:
            with xmlrpc.client.ServerProxy(self.server_url) as proxy:
                self.config.worker_logger.debug('Updating WorkerStatus')
                proxy.updateWorkerStatus(self.id, WorkerStatus.BUSY.value)
                self.config.worker_logger.debug('OrderStatus updated')
                proxy.updateOrderStatus(self.order_handler.order.id, OrderStatus.IN_PROGRESS.value,
                                        self.order_handler.order.current_step)
        except Exception as e:
            self.config.worker_logger.error(f'Error [{e}]')


    def on_startStep(self):
        with xmlrpc.client.ServerProxy(self.server_url) as proxy:
            proxy.updateOrderStatus(self.order_handler.order.id, OrderStatus.IN_PROGRESS.value,
                                    self.order_handler.order.current_step)
    def on_failOrder(self):
        with xmlrpc.client.ServerProxy(self.server_url) as proxy:
            proxy.updateWorkerStatus(self.id, WorkerStatus.FREE.value)
            if self.timeout:
                proxy.updateOrderStatus(self.order_handler.order.id, OrderStatus.TIMEOUT.value,
                                        self.order_handler.order.current_step)
            else:
                proxy.updateOrderStatus(self.order_handler.order.id, OrderStatus.FAILED.value,
                                        self.order_handler.order.current_step)

    def on_cookOrder(self):
        self.config.worker_logger.info('Order has been cooked')
        with xmlrpc.client.ServerProxy(self.server_url) as proxy:
            self.config.worker_logger.debug('Updating order status')
            proxy.updateOrderStatus(self.order_handler.order.id, OrderStatus.COOKED.value,
                                    self.order_handler.order.current_step)
            self.config.worker_logger.debug('Updating worker status')
            proxy.updateWorkerStatus(self.id, WorkerStatus.FREE.value)

    def clean_up(self):
        self.order_handler.rpc_kill_order()
        with xmlrpc.client.ServerProxy(self.server_url) as proxy:
            proxy.deregisterWorker(self.id)

    def kill(self):
        self.clean_up()
        self.kill_event.set()
