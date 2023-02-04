from threading import Lock
from dataclasses import dataclass

from UnrealBS.Worker import WorkerStatus


@dataclass
class WorkerData:
    id: str
    port: int
    status: WorkerStatus


class WorkerHandler:
    def __init__(self, update_callback):
        self.workers_lock = Lock()
        self.update_callback = update_callback

        self.registered_workers = {}

    def get_free_worker(self):
        try:
            self.workers_lock.acquire()
            for worker in self.registered_workers.values():
                if worker.status == WorkerStatus.FREE:
                    return worker
            return None
        except Exception:
            return None
        finally:
            self.workers_lock.release()

    def get_list(self, free=False):
        try:
            self.workers_lock.acquire()

            if free is False:
                return self.registered_workers.values()
            else:
                return [x for x in self.registered_workers.values() if x.status == WorkerStatus.FREE]
        finally:
            self.workers_lock.release()

    def rpc_register(self, worker_id, worker_port):
        try:
            self.workers_lock.acquire()
            worker_data = WorkerData(worker_id, worker_port, WorkerStatus.FREE)
            self.registered_workers[worker_data.id] = worker_data
            print(f'Registered worker {worker_data.id} at port {worker_data.port}')
            return True
        except Exception:
            return False
        finally:
            self.workers_lock.release()
            self.update_callback()

    def rpc_deregister(self, worker_id):
        try:
            self.workers_lock.acquire()
            self.registered_workers.pop(worker_id)
            print(f'Deregistered worker {worker_id}')
            return True
        except Exception:
            return False
        finally:
            self.workers_lock.release()

    def rpc_update(self, worker_id, status_val):
        try:
            print(f'UPDATE! - {worker_id} {status_val}')
            self.workers_lock.acquire()
            status = WorkerStatus(status_val)
            self.registered_workers[worker_id].status = status
            print(f'Worker {worker_id} changed status to {status}')
            return True
        except Exception:
            print('Exception')
            return False
        finally:
            self.workers_lock.release()
            self.update_callback()
