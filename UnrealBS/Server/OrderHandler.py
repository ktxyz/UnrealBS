from queue import Queue
from threading import Lock

from UnrealBS.Common.Orders import Order, OrderStatus


class OrderHandler:
    def __init__(self, update_callback):
        self.orders_lock = Lock()
        self.update_callback = update_callback

        self.orders_active = []
        self.orders_history = []
        self.orders_queue = Queue()

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

    def enqueue_order(self, recipe, order_data):
        try:
            self.orders_lock.acquire()
            new_order = Order(recipe, order_data)

            self.orders_active.append(new_order)
            self.orders_queue.put(new_order)
        finally:
            self.orders_lock.release()
            self.update_callback()

    def update_order(self, order_id, status_val):
        try:
            self.orders_lock.acquire()
            new_status = OrderStatus(status_val)

            print(f'Searching for order {order_id}')

            for order in self.orders_active:
                if order.id == order_id:
                    order.status = new_status
                    print(f'Found, now status is {order.status}')

                    if new_status.value > OrderStatus.IN_PROGRESS:
                        self.orders_active.remove(order)
                        self.orders_history.append(order)

                    break

            return True
        finally:
            self.orders_lock.release()
            self.update_callback()
