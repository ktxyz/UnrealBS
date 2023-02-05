import os
import signal
import subprocess
import time
from threading import Event

from UnrealBS.Config import Config


class StepFailedException(Exception):
    pass


class OrderCanceledException(Exception):
    pass


class StepHandler:
    def __init__(self, order_handler):
        self.config = Config()

        self.canceled = False
        self.canceled_ev = Event()

        self.order_handler = order_handler

    def handle(self, idx, count, step):
        self.order_handler.order.current_step = idx
        self.order_handler.worker.on_startStep()
        self.config.worker_logger.info(f'Running step {idx}/{count} [{step.name}]')

        try:
            cmds = step.cmd.split(' ')
            timeout = step.timeout
            if timeout == 0:
                timeout = 60 * 60 * 6  # 6 HOUR MAX WAIT TIME!

            self.proc = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                         shell=False, universal_newlines=True)

            time_delta = 0.01
            time_elapsed = 0
            while self.proc.poll() is None:
                nextline = self.proc.stdout.readline().strip()
                if nextline != "":
                    self.config.worker_logger.info(f'[OUTPUT]: {nextline}')

                if time_elapsed > timeout:
                    self.proc.kill()
                    self.proc.terminate()
                    raise TimeoutError

                if self.canceled_ev.is_set() is True:
                    self.proc.kill()
                    self.canceled_ev.clear()
                    raise OrderCanceledException

                time_elapsed += time_delta
                time.sleep(time_delta)

            if self.canceled_ev.is_set():
                self.proc.kill()
                self.canceled_ev.clear()
                raise OrderCanceledException

            self.proc.wait(timeout - time_elapsed)

            if self.canceled_ev.is_set():
                self.on_cancel()

            stdout, stderr = self.proc.stdout.read().strip(), self.proc.stderr.read().strip()
            if stdout != "":
                self.config.worker_logger.info(f'[OUTPUT]: {stdout}')
            if stderr != "":
                self.config.worker_logger.error(f'[OUTPUT-ERR]: {stderr}')
            exit_val = self.proc.returncode
            self.config.worker_logger.info(f'Step finished [{step.name}]')

            if exit_val != 0:
                self.config.worker_logger.info('Detected failure[return value != 0]')
                raise StepFailedException

        except OrderCanceledException:
            self.proc.kill()
            raise OrderCanceledException

        except TimeoutError as e:
            self.proc.kill()
            raise TimeoutError

        except Exception as e:
            print(e)
            raise StepFailedException
    def on_cancel(self):
        self.proc.kill()
        self.canceled_ev.clear()
        raise OrderCanceledException
    def kill(self):
        self.config.worker_logger.debug('Kill called!')

        self.proc.kill()
        self.canceled_ev.set()
