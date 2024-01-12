
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def hello():
    return('hello')

@app.route("/index", methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return "GET request reveived"
    elif request.method == 'POST':
        data = request.get_json()
        print('received data:', data)
        return jsonify({'message': 'data trasnferred!'})
    
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=6969, debug=True)