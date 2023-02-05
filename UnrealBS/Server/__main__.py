import sys
import signal

from threading import Thread

from UnrealBS.Server import Server

from UnrealBS.Config import Config


def sigterm_handler(signal, frame):
    config = Config()
    config.universal_kill_ev.set()
    config.universal_kill_ct += 1

    config.server_logger.warning('Received SIGTERM, exiting...')
    config.server.kill()
    if config.universal_kill_ct == 3:
        config.server_logger.error('KILLED 2nd TIME, HARD EXIT')
        sys.exit(-1)


def Main():
    config = Config()

    try:
        server = Server()

        # TODO
        # this is kinda hacky, but needed for API server
        config.server = server

        s_thread = Thread(target=server.run)
        s_thread.daemon = True
        s_thread.start()


        # Trie to cleanup before sigterm
        signal.signal(signal.SIGTERM, sigterm_handler)
        signal.signal(signal.SIGINT, sigterm_handler)
        signal.signal(signal.SIGBREAK, sigterm_handler)

        while not config.universal_kill_ev.is_set():
            pass
    except InterruptedError:
        sigterm_handler(None, None)
    except KeyboardInterrupt:
        sigterm_handler(None, None)
    except Exception as e:
        config.server_logger.error(f'EXCEPTION: {e}')
        sigterm_handler(None, None)

    if s_thread:
        s_thread.join()
    config.server_logger.info('[ Bye!!! ]')


if __name__ == "__main__":
    Main()
