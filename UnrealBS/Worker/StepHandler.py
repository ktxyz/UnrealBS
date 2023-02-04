import os
import signal
import subprocess
import time
from threading import Event

class StepFailedException(Exception):
    pass

class OrderCanceledException(Exception):
    pass

class StepHandler:
    def __init__(self):
        self.canceled = False
        self.canceled_ev = Event()
        pass

    def handle(self, step):
        self.canceled = False
        try:
            cmds = step.cmd.split(' ')
            timeout = step.timeout
            if timeout == 0:
                timeout = 60 * 60 * 6 # 6 HOUR MAX WAIT TIME!

            print(f"RUNNING COMMAND: {cmds}")

            self.proc = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                         shell=False, universal_newlines=True)

            print(f'waiting {timeout}')

            time_delta = 1
            time_elapsed = 0
            while self.proc.poll() is None:
                if time_elapsed > timeout:
                    self.proc.kill()
                    self.proc.terminate()
                    raise TimeoutError

                if self.canceled_ev.is_set() is True:
                    print('Dead, raising')
                    self.proc.kill()
                    self.canceled_ev.clear()
                    raise OrderCanceledException
                else:
                    print(f'self.cancelled_ev = {self.canceled_ev.is_set()}')
                time_elapsed += time_delta
                time.sleep(time_delta)
            print('AFTER LOOP')

            if self.canceled_ev.is_set():
                    print('Dead, raising2')
                    self.proc.kill()
                    self.canceled_ev.clear()
                    raise OrderCanceledException

            self.proc.wait(timeout - time_elapsed)


            if self.canceled_ev.is_set():
                    print('Dead, raising3')
                    self.proc.kill()
                    self.canceled_ev.clear()
                    raise OrderCanceledException

            stdout, stderr = self.proc.stdout.read(), self.proc.stderr.read()
            exit_val = self.proc.returncode
            print('finished')

            if self.canceled:
                raise OrderCanceledException

            if exit_val != 0:
                print(f'Returned non zero value! {exit_val}')
                print(f'OUT: {stdout} ERR: {stderr}')
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


    def kill(self):
        print('Kill in stephandler')
        self.proc.kill()
        self.canceled_ev.set()
        print(f'Now canceled_ev set is {self.canceled_ev.is_set()}')
