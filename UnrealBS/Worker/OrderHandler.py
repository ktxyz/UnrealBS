import json
import time
from threading import Lock, Thread, Event

from UnrealBS.Common.Orders import Order
from UnrealBS.Common.Recipes import Recipe
from UnrealBS.Worker.ProcessHandler import ProcessHandler
from UnrealBS.Worker.StepHandler import StepHandler


class OrderHandler:
    def __init__(self, worker):
        self.order = None
        self.worker = worker


        self.step_handler = StepHandler()

        self.order_lock = Lock()
        self.process_handler = ProcessHandler(self)

    def rpc_kill_order(self):
        self.step_handler.kill()
        print('Kill Sent')

        return True

    def rpc_recv_order(self, order_data):
        try:
            self.worker.timeout = False
            order_data = json.loads(order_data)
            self.order = Order(Recipe(order_data['recipe']), order_data['order'])
            print(f'Worker[{self.worker.id}] got new order {self.order.id}')

            return True
        finally:
            self.worker.on_startOrder()

    def fail(self):
        if not self.worker.kill_event.is_set():
            if self.order is not None:
                try:
                    self.step_handler.handle(self.order.recipe.failure_step)
                except Exception as e:
                    print(e)
                self.worker.on_failOrder()

    def success(self):
        if not self.worker.kill_event.is_set():
            if self.order is not None:
                try:
                    self.step_handler.handle(self.order.recipe.success_step)
                except Exception as e:
                    print(e)
                self.worker.on_cookOrder()

    def process(self):
        while self.worker.kill_event.is_set() is False:
            print('Revived')
            self.process_handler.run()
            print('Killed')
        print('Killed for good')

    def clean(self):
        self.worker.on_killOrder()
