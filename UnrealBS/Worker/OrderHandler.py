import json
import time
from threading import Lock, Thread

from UnrealBS.Common.Orders import Order
from UnrealBS.Common.Recipes import Recipe
from UnrealBS.Worker.StepHandler import StepHandler


class OrderHandler:
    def __init__(self, worker):
        self.order = None
        self.worker = worker

        self.step_handler = StepHandler()

        self.order_lock = Lock()
        self.process_thread = Thread(target=self.process)
        self.process_thread.daemon = True
        self.process_thread.start()

    def rpc_recv_order(self, order_data):
        try:
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
                    self.step_handler.handle(self.order.recipe.fail_step)
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
        while not self.worker.kill_event.is_set():
            try:
                self.order_lock.acquire()
                if self.order is not None:
                    print('HERE')
                    try:
                        self.step_handler.handle(self.order.recipe.start_step)
                    except Exception:
                        print('Fail')
                        self.fail()
                        raise Exception

                    for idx, step in enumerate(self.order.recipe.steps):
                        print(f'Runnign step {idx} or order: {self.order.id}')
                        try:
                            self.step_handler.handle(step)
                        except Exception:
                            self.fail()
                            raise Exception
                    self.success()
            except Exception as e:
                print(e)
            finally:
                self.order = None
                self.order_lock.release()

            time.sleep(0.1)  # we don't need to tick every cpu cycle
        self.clean()

    def clean(self):
        pass
