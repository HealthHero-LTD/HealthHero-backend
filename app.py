
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def hello():
    return('hello')

@app.get("/idnex")
def index_get():
    return "GET request reveived"

@app.post("/index")
def index_post():
    data = request.get_json()
    print(f"received data: {data}")
    return jsonify({'message': 'data transferred!'})
    
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=6969, debug=True)