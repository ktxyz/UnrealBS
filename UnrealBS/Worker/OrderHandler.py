import json
from threading import Lock

from UnrealBS.Common.Orders import Order
from UnrealBS.Common.Recipes import Recipe
from UnrealBS.Config import Config
from UnrealBS.Worker.ProcessHandler import ProcessHandler
from UnrealBS.Worker.StepHandler import StepHandler


class OrderHandler:
    def __init__(self, worker):
        self.config = Config()

        self.order = None
        self.worker = worker

        self.step_handler = StepHandler(self)

        self.order_lock = Lock()
        self.process_handler = ProcessHandler(self)

    def rpc_kill_order(self):
        self.config.worker_logger.debug('Kill order sent')
        self.step_handler.kill()
        return True

    def rpc_recv_order(self, order_data):
        try:
            self.worker.timeout = False
            order_data = json.loads(order_data)
            self.order = Order(Recipe(order_data['recipe']), order_data['order'])
            self.config.worker_logger.info(f'Got new order {self.order.id}')
            self.worker.on_startOrder()
            return True
        except Exception as e:
            self.config.worker_logger.error(f'[ERROR]: {e}')
            return False

    def fail(self):
        self.config.worker_logger.info('Order failed!')
        if not self.worker.kill_event.is_set():
            if self.order is not None:
                try:
                    self.step_handler.handle('Last', 'All', self.order.recipe.failure_step)
                except Exception as e:
                    self.config.worker_logger.error(e)
                self.worker.on_failOrder()

    def success(self):
        self.config.worker_logger.info('Order cooked!')
        if not self.worker.kill_event.is_set():
            if self.order is not None:
                try:
                    self.step_handler.handle('Last', 'All', self.order.recipe.success_step)
                except Exception as e:
                    self.config.worker_logger.error(e)
                self.worker.on_cookOrder()

    def process(self):
        while self.worker.kill_event.is_set() is False:
            self.config.worker_logger.debug('Process handler launched')
            self.process_handler.run()
            self.config.worker_logger.debug('Process handler killed')
        self.config.worker_logger.debug('Process handler killed 4 ever')

    def clean(self):
        self.worker.on_killOrder()
