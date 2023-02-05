import json
import http.server

from UnrealBS.Config import Config
from UnrealBS.Server.RecipeHandler import RecipeNotFound

# TODO
# this is fucking dirty
config = Config()
class APIHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _send_response(self, status_code, data=None):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if data:
            self.wfile.write(json.dumps(data).encode())

    def authorize(self):
        if "Authorization" not in self.headers:
            self._send_response(401, {"error": "Authorization header missing"})
            raise Exception

        auth_header = self.headers["Authorization"]
        if auth_header != f"Bearer {config.args.secret_key}":
            self._send_response(401, {"error": "Incorrect authorization key"})
            raise Exception

    def do_GET(self):
        config.server_logger.info(f'New API request @ "{self.path}"')

        try:
            self.authorize()
        except Exception as e:
            config.server_logger.error(f'Unauthorized request denied![{e}]')
            return

        content_length = int(self.headers["Content-Length"])
        request_body = self.rfile.read(content_length).decode()
        config.server_logger.debug(request_body)
        try:
            request_data = json.loads(request_body)
            client = request_data['client']
            config.server_logger.info(f'Request from {client}')

            if self.path == '/workers':
                self._send_response(200, {"workers": [{'id': x.id, 'port': x.port, 'status': x.status.name}
                                                      for x in config.server.worker_handler.get_list()]})
            elif self.path == '/recipes':
                self._send_response(200, {"recipes": [{'target': x.target, 'steps_count': len(x.steps)}
                                                      for x in config.server.recipe_handler.get_list()]})
            elif self.path == '/orders':
                only_active = request_data['only_active']
                self._send_response(200, {"orders": [{'recipe': x.recipe.target, 'status': x.status.name, 'current_step': x.current_step} for x in config.server.order_handler.get_list(only_active)]})
        except Exception as e:
            config.server_logger.error(str(e))
            self._send_response(500, {"error": str(e)})

    def do_POST(self):
        config.server_logger.info(f'New API request @ "{self.path}"')

        try:
            self.authorize()
        except Exception as e:
            config.server_logger.error(f'Unauthorized request denied![{e}]')
            return

        content_length = int(self.headers["Content-Length"])
        request_body = self.rfile.read(content_length).decode()
        config.server_logger.debug(request_body)
        try:
            request_data = json.loads(request_body)
            client = request_data['client']
            config.server_logger.info(f'Request from {client}')

            if self.path == '/kill':
                order_id = request_data['order_id']
                if order_id == '$LAST_ORDER':
                    order_id = config.server.order_handler.get_list(True)[-1].id
                config.server.order_handler.kill_order(order_id)
            elif self.path == '/order':
                target = request_data['target']
                config.server.order_handler.enqueue_order(
                    config.server.recipe_handler.get_recipe(target),
                    {
                        'client': client
                    }
                )
            self._send_response(200, {"message": "Success"})
        except json.JSONDecodeError:
            config.server_logger.error('Invalid request data!')
            self._send_response(400, {"error": "Invalid JSON data"})
            return
        except RecipeNotFound:
            config.server_logger.error(f'Tried ordering non-existent recipe')
            self._send_response(400, {"message": "bad recipe"})
        except Exception as e:
            config.server_logger.error(f'Exception raised: {e}')
            self._send_response(500, {"error": str(e)})

