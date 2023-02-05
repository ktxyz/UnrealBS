import time
from threading import Thread

from UnrealBS.Config import Config
from UnrealBS.Worker.StepHandler import OrderCanceledException

class ProcessHandler:
    def __init__(self, order_handler):
        self.config = Config()
        self.order_handler = order_handler

    def run(self):
        while self.order_handler.worker.kill_event.is_set() is False:
            try:
                self.config.worker_logger.debug('Order_lock [Acquire]')
                self.order_handler.order_lock.acquire(timeout=self.config.universal_timeout)
                if self.order_handler.order is not None:
                    self.order_handler.worker.on_startOrder()

                    length = len(self.order_handler.order.recipe.steps)
                    self.order_handler.step_handler.handle(-1, length, self.order_handler.order.recipe.start_step)
                    for idx, step in enumerate(self.order_handler.order.recipe.steps):
                        self.order_handler.step_handler.handle(idx, length, step)
                    self.order_handler.success()
                else:
                    self.config.worker_logger.debug('Order is none')
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
                self.config.worker_logger.error(f'Error [{e}]')
                self.order_handler.fail()
            finally:
                if self.order_handler.order_lock.locked():
                    self.order_handler.order = None
                    self.config.worker_logger.debug('Order_lock [Release]')
                    self.order_handler.order_lock.release()

            time.sleep(2)  # we don't need to tick every cpu cycle
        self.order_handler.clean()
