import sys
import signal

from threading import Thread

from UnrealBS.Server import Server
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
            config.worker_logger.error('KILLED 3rd TIME, HARD EXIT')
    if config.args.run_server:
        config.server_logger.warning('Received SIGTERM, exiting...')
        config.server.kill()
        if KILL_TRIES == 3:
            config.server_logger.error('KILLED 3rd TIME, HARD EXIT')

    if KILL_TRIES == 3:
        sys.exit(-1)


def Main():
    config = Config()

    s_thread = None
    if config.args.run_server:
        server = Server()

        # TODO
        # this is kinda hacky, but needed for API server
        config.server = server

        s_thread = Thread(target=server.run)
        s_thread.start()

    # Trie to cleanup before sigterm
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigterm_handler)

    w_thread = None
    if config.args.run_worker:
        worker = Worker()

        # TODO
        # this is also hacky, for signal
        config.worker = worker

        w_thread = Thread(target=worker.run)
        w_thread.start()

    if s_thread:
        s_thread.join()
    if w_thread:
        w_thread.join()


if __name__ == "__main__":
    Main()
