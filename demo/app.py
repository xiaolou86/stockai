from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__)

# Enable CORS for all routes (you can restrict it as needed)
CORS(app)

@app.route('/')
def home():
        return render_template('index.html')

@app.route('/get_image_json', methods=['GET'])
def get_image_json():
    param1 = request.args.get('param1')
    param2 = request.args.get('param2')
    
    # Example: Simulate some data processing
    if not param1 or not param2:
        return jsonify({"error": "Missing parameters"}), 400
    
    data = {
        "image": "R0lGODdhAQABAIABAAAAAP///yH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==",  # 1x1 pixel base64-encoded GIF
        "info": {
            "param1": param1,
            "param2": param2,
            "description": "This is an example response."
        }
    }
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=50080)

