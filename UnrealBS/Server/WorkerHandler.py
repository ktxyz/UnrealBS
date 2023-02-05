from threading import Lock
from dataclasses import dataclass

import xmlrpc.client

from UnrealBS.Config import Config
from UnrealBS.Worker import WorkerStatus


@dataclass
class WorkerData:
    id: str
    port: int
    status: WorkerStatus


class WorkerHandler:
    def __init__(self, update_callback):
        self.config = Config()

        self.workers_lock = Lock()
        self.update_callback = update_callback

        self.registered_workers = {}

        self.order_map = {}

    def kill_order(self, order_id):
        try:
            self.workers_lock.acquire()
            if order_id in self.order_map.keys():
                worker_id = self.order_map.pop(order_id)
                worker = self.registered_workers[worker_id]
                # TODO
                # for now workers have to all be on ethe same host!
                # not good, but for now can be!
                with xmlrpc.client.ServerProxy(f'http://{self.config.args.worker_host}:{worker.port}') as proxy:
                    proxy.killOrder()
        finally:
            self.workers_lock.release()
    def assign_order(self, order_id, worker_id):
        try:
            self.workers_lock.acquire()
            if worker_id in self.registered_workers.keys():
                self.config.server_logger.debug(f'Assigning order[{order_id}] to worker[{worker_id}]')
                self.order_map[order_id] = worker_id
        finally:
            self.workers_lock.release()

    def get_free_worker(self):
        try:
            self.workers_lock.acquire()
            for worker in self.registered_workers.values():
                if worker.status == WorkerStatus.FREE:
                    return worker
            return None
        except Exception as e:
            self.config.server_logger.error(f'Error [{e}]')
            return None
        finally:
            self.workers_lock.release()

    def get_list(self, free=False):
        try:
            self.workers_lock.acquire()
            if free is False:
                return list(self.registered_workers.values())
            else:
                return [x for x in self.registered_workers.values() if x.status == WorkerStatus.FREE]
        finally:
            self.workers_lock.release()

    def rpc_register(self, worker_id, worker_port):
        try:
            self.workers_lock.acquire()
            worker_data = WorkerData(worker_id, worker_port, WorkerStatus.FREE)
            self.registered_workers[worker_data.id] = worker_data
            self.config.server_logger.info(f'Registered worker {worker_data.id} at port {worker_data.port}')
            return True
        except Exception as e:
            self.config.server_logger.error(f'Error [{e}]')
            return False
        finally:
            self.workers_lock.release()
            self.update_callback()

    def rpc_deregister(self, worker_id):
        try:
            self.workers_lock.acquire()
            self.registered_workers.pop(worker_id)
            self.config.server_logger.info(f'Deregistered worker {worker_id}')
            return True
        except Exception as e:
            self.config.server_logger.error(f'Error [{e}]')
            return False
        finally:
            self.workers_lock.release()

    def rpc_update(self, worker_id, status_val):
        try:
            self.workers_lock.acquire()
            status = WorkerStatus(status_val)

            if worker_id in self.registered_workers.keys():
                self.registered_workers[worker_id].status = status
                self.config.server_logger.info(f'Worker {worker_id} changed status to {status.name}')
            return True
        except Exception as e:
            self.config.server_logger.error(f'Error [{e}]')
            return False
        finally:
            self.workers_lock.release()
            self.update_callback()
