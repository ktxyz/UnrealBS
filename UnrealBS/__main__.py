from threading import Thread

from UnrealBS.Server import Server
from UnrealBS.Worker import Worker

from UnrealBS.Config import Config

if __name__ == "__main__":
    config = Config()

    s_thread = None
    if config.args.run_server:
        server = Server()

        # TODO
        # this is kinda hacky, but needed for API server
        config.server = server

        s_thread = Thread(target=server.run)
        s_thread.start()

    w_thread = None
    if config.args.run_worker:
        worker = Worker()
        w_thread = Thread(target=worker.run)
        w_thread.start()

    if s_thread:
        s_thread.join()
    if w_thread:
        w_thread.join()
