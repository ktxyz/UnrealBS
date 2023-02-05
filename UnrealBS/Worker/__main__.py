import sys
import signal

from threading import Thread

from UnrealBS.Worker import Worker

from UnrealBS.Config import Config


def sigterm_handler(signal, frame):
    config = Config()
    config.universal_kill_ev.set()
    config.universal_kill_ct += 1

    config.worker_logger.warning('Received SIGTERM, exiting...')
    config.worker.kill()
    if config.universal_kill_ct == 3:
        config.worker_logger.error('KILLED 2nd TIME, HARD EXIT')
        sys.exit(-1)


def Main():
    config = Config()

    try:
        worker = Worker()

        # TODO
        # this is also hacky, for signal
        config.worker = worker

        w_thread = Thread(target=worker.run)
        w_thread.daemon = True
        w_thread.start()

        # Trie to cleanup before sigterm
        signal.signal(signal.SIGINT, sigterm_handler)
        signal.signal(signal.SIGTERM, sigterm_handler)
        signal.signal(signal.SIGBREAK, sigterm_handler)

        while not config.universal_kill_ev.is_set():
            pass
    except InterruptedError:
        sigterm_handler(None, None)
    except KeyboardInterrupt:
        sigterm_handler(None, None)
    except Exception as e:
        config.worker_logger.error(f'EXCEPTION: {e}')
        sigterm_handler(None, None)

    if w_thread:
        w_thread.join()
    config.server_logger.info('[ Bye!!! ]')


if __name__ == "__main__":
    Main()
