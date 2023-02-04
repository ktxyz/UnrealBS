import time
from threading import Thread

from UnrealBS.Worker.StepHandler import OrderCanceledException

class ProcessHandler:
    def __init__(self, order_handler):
        self.order_handler = order_handler

    def run(self):
        while not self.order_handler.worker.kill_event.is_set():
            try:
                self.order_handler.order_lock.acquire()
                if self.order_handler.order is not None:
                    print('HERE')
                    self.order_handler.step_handler.handle(self.order_handler.order.recipe.start_step)

                    for idx, step in enumerate(self.order_handler.order.recipe.steps):
                        print(f'Running step {idx} or order: {self.order_handler.order.id}')
                        self.order_handler.step_handler.handle(step)
                    self.order_handler.success()
            except OrderCanceledException as e:
                print('Cancelled, nothing should run after!')
                self.order_handler.clean()
                self.order_handler.order = None
                return None
            except TimeoutError:
                print('Timeout')
                # FIXME this is not thread safe!!!!!!!!!
                self.order_handler.worker.timeout = True
                self.order_handler.fail()
            except Exception as e:
                print(f'e - {e}')
                print('Fail2131')
                self.order_handler.fail()
            finally:
                self.order_handler.order = None
                self.order_handler.order_lock.release()

            time.sleep(0.1)  # we don't need to tick every cpu cycle
        self.order_handler.clean()
