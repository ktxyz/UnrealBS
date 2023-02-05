import sys
import signal

from threading import Thread

from UnrealBS.Worker import Worker

from UnrealBS.Config import Config

KILL_TRIES = 0

def sigterm_handler(signal, frame):
    config = Config()
    global KILL_TRIES

    KILL_TRIES += 1

    if config.args.run_worker:
        config.worker_logger.warning('Received SIGTERM, exiting...')
        config.worker.kill()
        if KILL_TRIES == 3:
            config.server_logger.error('KILLED 3rd TIME, HARD EXIT')

    if KILL_TRIES == 3:
        sys.exit(-1)


def Main():
    config = Config()
    config.args.run_worker = True

    worker = Worker()

    # TODO
    # this is also hacky, for signal
    config.worker = worker

    w_thread = Thread(target=worker.run)
    w_thread.start()

    # Trie to cleanup before sigterm
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigterm_handler)

    if w_thread:
        w_thread.join()

    config.server_logger.info('[ Bye!!! ]')


if __name__ == "__main__":
    Main()
