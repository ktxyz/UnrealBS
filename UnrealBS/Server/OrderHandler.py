from queue import Queue
from threading import Lock

from UnrealBS.Common.Orders import Order, OrderStatus
from UnrealBS.Config import Config


class OrderHandler:
    def __init__(self, server, update_callback):
        self.config = Config()

        self.server = server
        self.orders_lock = Lock()
        self.update_callback = update_callback

        self.orders_active = []
        self.orders_history = []
        self.orders_queue = Queue()

        self.orders_scheduled = []
        self.orders_repeating = []

    def has_pending_orders(self):
        return self.orders_queue.empty() is False

    def get_queued_order(self):
        try:
            return self.orders_queue.get(False)
        except Exception:
            return None

    def get_list(self, active=False):
        try:
            self.orders_lock.acquire()
            if active:
                return self.orders_active
            else:
                all_list = self.orders_active.copy()
                all_list.extend(self.orders_history)
                return all_list
        finally:
            self.orders_lock.release()

    def refresh_orders(self):
        try:
            self.orders_lock.acquire()

            for order in self.orders_repeating:
                if order.recipe.is_time():
                    new_order = Order(order.recipe, {
                        'client': 'SERVER-REPEAT'
                    })
                    self._enqueue_order(new_order)
                    order.recipe.reset_time()
        finally:
            self.orders_lock.release()
    def repeat_order(self, recipe):
        try:
            self.orders_lock.acquire()
            order = Order(recipe, {
                'client': 'SERVER-REPEAT'
            })
            self.orders_repeating.append(order)
        finally:
            self.orders_lock.release()

    def _enqueue_order(self, new_order):
        self.orders_active.append(new_order)
        self.orders_queue.put(new_order)

    def enqueue_order(self, recipe, order_data):
        if recipe is None:
            self.config.server_logger.debug('Tried to order None recipe!')
            return
        try:
            self.orders_lock.acquire()
            new_order = Order(recipe, order_data)

            self.orders_active.append(new_order)
            self.orders_queue.put(new_order)
        finally:
            self.orders_lock.release()
            self.update_callback()

    def kill_order(self, order_id):
        orders = self.get_list(True)
        for order in orders:
            if order.id == order_id:
                if order.status == OrderStatus.IN_PROGRESS:
                    self.server.worker_handler.kill_order(order_id)
                self.update_order(order_id, OrderStatus.CANCELLED, order.current_step)

    def update_order(self, order_id, status_val, new_step):
        try:
            self.orders_lock.acquire()
            new_status = OrderStatus(status_val)

            for order in self.orders_active:
                if order.id == order_id:
                    if order.status != new_status:
                        order.status = new_status
                        self.config.server_logger.info(f'Order[{order_id}] changed status to {new_status.name}')

                        if new_status.value > OrderStatus.IN_PROGRESS:
                            self.orders_active.remove(order)
                            self.orders_history.append(order)
                    if order.current_step != new_step:
                        order.current_step = new_step
                        self.config.server_logger.info(f'Order[{order_id}] started step[{new_step}]')
                    break
            return True
        finally:
            self.orders_lock.release()
            self.update_callback()
