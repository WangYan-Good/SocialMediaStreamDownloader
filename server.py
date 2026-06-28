import os
import sys
import traceback
import logging
from dotenv import load_dotenv

sys.path.append(os.getcwd())

from flask import Flask, request, jsonify, render_template
from werkzeug.exceptions import BadRequest

from backend.src.library.loglib import init_bootstrap_logger, get_logger
from backend.src.library.configlib import init_base_config
from backend.src.platform.platform_dispatcher import PlatformDispatcher


def load_environment():
    if os.getenv("ENVIRONMENT", None) is None:
        load_dotenv()


def init_runtime():
    init_bootstrap_logger()
    init_base_config()

    logger = get_logger() if callable(get_logger) else logging.getLogger(__name__)

    dispatcher = PlatformDispatcher()
    dispatcher.register()

    return logger, dispatcher


def create_app():
    load_environment()

    logger, platform_dispatcher = init_runtime()

    app = Flask(__name__, static_folder='./frontend/src/static', template_folder='./frontend/src/templates')

    @app.route('/', methods=['POST'])
    def process_request():
        try:
            if not request.is_json:
                return jsonify({"status":"error","message":"json required","code":400}),400

            data = request.get_json(silent=True)
            if data is None:
                return jsonify({"status":"error","message":"empty request","code":400}),400

            urls = data.get('urls')
            if not urls or not isinstance(urls, list):
                return jsonify({"status":"error","message":"urls required","code":400}),400

            for i,u in enumerate(urls):
                if not isinstance(u,str) or not u.startswith(('http://','https://')):
                    return jsonify({"status":"error","message":"invalid url","code":400}),400

            platform_dispatcher.dispatch(data)

        except BadRequest as e:
            logger.warning(str(e))
            return jsonify({"status":"error","message":"bad request","code":400}),400
        except ValueError as e:
            logger.warning(str(e))
            return jsonify({"status":"error","message":str(e),"code":400}),400
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(tb)
            debug = os.getenv('FLASK_DEBUG','false').lower() in ('true','1','yes')
            if debug:
                return jsonify({"status":"error","message":str(e),"traceback":tb.split('\n'),"code":500}),500
            return jsonify({"status":"error","message":"server error","code":500}),500

        return jsonify({"status":"success","message":"ok","code":200}),200

    @app.route('/', methods=['GET'])
    def index():
        return render_template('index.html')

    return app


if __name__ == '__main__':
    app = create_app()

    debug = os.getenv('FLASK_DEBUG','false').lower() in ('true','1','yes')
    host = os.getenv('SERVER_HOST','0.0.0.0')
    port = int(os.getenv('SERVER_PORT',5000))

    app.run(debug=debug, host=host, port=port)
