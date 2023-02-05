import time
from threading import Thread

from UnrealBS.Config import Config
from UnrealBS.Worker.StepHandler import OrderCanceledException

class ProcessHandler:
    def __init__(self, order_handler):
        self.config = Config()
        self.order_handler = order_handler

    def run(self):
        while not self.order_handler.worker.kill_event.is_set():
            try:
                self.order_handler.order_lock.acquire()
                if self.order_handler.order is not None:
                    length = len(self.order_handler.order.recipe.steps)
                    self.order_handler.step_handler.handle(-1, length, self.order_handler.order.recipe.start_step)
                    for idx, step in enumerate(self.order_handler.order.recipe.steps):
                        self.order_handler.step_handler.handle(idx, length, step)
                    self.order_handler.success()
            except OrderCanceledException as e:
                self.config.worker_logger.warning('Order cancelled')
                self.order_handler.clean()
                self.order_handler.order = None
                return None
            except TimeoutError:
                self.config.worker_logger.error('Order timed-out')
                # FIXME this is not thread safe!!!!!!!!!
                self.order_handler.worker.timeout = True
                self.order_handler.fail()
            except Exception as e:
                self.config.worker_logger.error(e)
                self.order_handler.fail()
            finally:
                self.order_handler.order = None
                self.order_handler.order_lock.release()

            time.sleep(0.1)  # we don't need to tick every cpu cycle
        self.order_handler.clean()
