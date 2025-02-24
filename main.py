#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# import os
# import sys

# WORK_SPACE = sys.path[0]
# sys.path.append(os.path.join(WORK_SPACE))

# def parse_user_command():
#   pass

# def apply_user_parameters():
#   pass

# def run():
#   pass

# if __name__ == "__main__":

#   try:
#     ##
#     ## Get download command parameter
#     ##
#     parse_user_command()

#     ##
#     ## Apply user parameter
#     ##
#     apply_user_parameters()

#     ##
#     ## Execute command
#     ##
#     run()
#   except Exception as e:
#     print("ERROR: run download command failed!\n{}".format(e))
#     raise e

from flask import Flask, request, jsonify
import re

app = Flask(__name__)

@app.route('/process-link', methods=['POST'])
def process_link():
    data = request.json
    links = data.get('links', [])

    # 在这里处理链接
    for link in links:
        print(f"Processing link: {link}")
        # 你可以在这里添加处理链接的逻辑

    return jsonify({"status": "success", "processed_links": links})

if __name__ == '__main__':
    app.run(debug=True)