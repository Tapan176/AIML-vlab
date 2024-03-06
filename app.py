from flask import Flask, request, jsonify
from flask_cors import CORS
from sklearn.linear_model import LinearRegression
import numpy as np

app = Flask(__name__)
CORS(app)

@app.route('/linear-regression', methods=['POST'])
def linear_regression():
    data = request.json
    X = np.array(data['X'])
    y = np.array(data['y'])

    # Fit linear regression model
    model = LinearRegression()
    model.fit(X.reshape(-1, 1), y)

    # Predict
    y_pred = model.predict(X.reshape(-1, 1))

    # Return results
    return jsonify({"coefficients": model.coef_.tolist(), "intercept": model.intercept_, "predictions": y_pred.tolist()})

if __name__ == '__main__':
    app.run(debug=True, port=5050)
