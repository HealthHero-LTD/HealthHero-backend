import os
import psycopg2
from flask import Flask, request, jsonify

# db configs
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}"
    f"@localhost:5432/{DB_NAME}"
)

app = Flask(__name__)

@app.route('/')
def hello():
    return('hello')

@app.get("/index")
def index_get():
    return "GET request reveived"

@app.post("/index")
def index_post():
    data = request.get_json()
    print(f"received data: {data}")
    
    try:
        dbConnection = psycopg2.connect(DATABASE_URL)
        print("connected to the db successfully")
        return jsonify({'message': 'data transferred!'})
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        dbConnection.close()
    
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=6969, debug=True)