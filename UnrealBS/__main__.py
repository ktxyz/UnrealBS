import sys
import signal

from threading import Thread

from UnrealBS.Server import Server
from UnrealBS.Worker import Worker

from UnrealBS.Config import Config


def sigterm_handler(signum, frame):
    config = Config()
    config.universal_kill_ev.set()
    config.universal_kill_ct += 1

    if config.args.run_worker:
        config.worker_logger.warning('Received SIGTERM, exiting...')
        config.worker.kill()
        if config.universal_kill_ct == 3:
            config.worker_logger.error('KILLED 2nd TIME, HARD EXIT')
            sys.exit(-1)
    if config.args.run_server:
        config.server_logger.warning('Received SIGTERM, exiting...')
        config.server.kill()
        if config.universal_kill_ct == 3:
            config.server_logger.error('KILLED 2nd TIME, HARD EXIT')
            sys.exit(-1)


def Main():
    config = Config()

    try:
        s_thread = None
        if config.args.run_server:
            server = Server()

            # TODO
            # this is kinda hacky, but needed for API server
            config.server = server

            s_thread = Thread(target=server.run)
            s_thread.daemon = True
            s_thread.start()

        # Trie to cleanup before sigterm
        signal.signal(signal.SIGINT, sigterm_handler)
        signal.signal(signal.SIGTERM, sigterm_handler)
        signal.signal(signal.SIGBREAK, sigterm_handler)

        w_thread = None
        if config.args.run_worker:
            worker = Worker()

            # TODO
            # this is also hacky, for signal
            config.worker = worker

            w_thread = Thread(target=worker.run)
            w_thread.daemon = True
            w_thread.start()

        # Stupid fucking windows fix
        # I hate this fucking os
        while not config.universal_kill_ev.is_set():
            pass

    except InterruptedError:
        sigterm_handler(None, None)
    except KeyboardInterrupt:
        sigterm_handler(None, None)
    except Exception as e:
        print(f'EXCEPTION: {e}')
        sigterm_handler(None, None)

    if w_thread:
        w_thread.join()
    if s_thread:
        s_thread.join()


if __name__ == "__main__":
    Main()
