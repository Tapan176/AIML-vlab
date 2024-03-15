from flask import Blueprint, request, jsonify
from models.linearRegression.linearRegression import simpleLinearRegression
from models.cnn.cnn import train_cnn

model_routes = Blueprint('model_routes', __name__)

@model_routes.route('/linear-regression', methods=['POST'])
def linear_regression():
    results = simpleLinearRegression(request)

    # Return results
    return jsonify(results)

@model_routes.route('/cnn', methods=['POST'])
def cnn():
    results = train_cnn(request)

    return jsonify(results)
