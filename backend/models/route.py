from flask import Blueprint, request, jsonify
from models.linearRegression.linearRegression import simpleLinearRegression
from models.cnn.cnn import train_cnn
from models.multivariableLinearRegression.multivariableLinearRegression import multivariateLinearRegression
from models.logisticRegression.logisticRegression import logisticRegression
from models.decisionTree.decisionTree import decisionTree
from models.randomForest.randomForest import randomForest
from models.knn.knn import knn
from models.supportVectorMachine.supportVectorMachine import supportVectorMachine
from models.naiveBayes.naiveBayes import naiveBayes
from models.kMeans.kMeans import kMeans
from models.dbscan.dbscan import dbscan

model_routes = Blueprint('model_routes', __name__)

@model_routes.route('/linear-regression', methods=['POST'])
def linear_regression():
    results = simpleLinearRegression(request)

    # Return results
    return jsonify(results)

@model_routes.route('/multivariable-linear-regression', methods=['POST'])
def multivariate_linear_regression():
    results = multivariateLinearRegression(request)

    return jsonify(results)

@model_routes.route('/logistic-regression', methods=['POST'])
def logistic_regression():
    results = logisticRegression(request)

    return jsonify(results)

@model_routes.route('/decision-tree', methods=['POST'])
def decision_tree():
    results = decisionTree(request)

    return jsonify(results)

@model_routes.route('/random-forest', methods=['POST'])
def random_forest():
    results = randomForest(request)

    return jsonify(results)

@model_routes.route('/knn', methods=['POST'])
def k_nearest_neighbors():
    results = knn(request)

    return jsonify(results)

@model_routes.route('/k-means', methods=['POST'])
def k_means():
    results = kMeans(request)

    return jsonify(results)

@model_routes.route('/support-vector-machine', methods=['POST'])
def support_vector_machine():
    results = supportVectorMachine(request)

    return jsonify(results)

@model_routes.route('/naive-bayes', methods=['POST'])
def naive_bayes():
    results = naiveBayes(request)

    return jsonify(results)

@model_routes.route('/dbscan', methods=['POST'])
def db_scan():
    results = dbscan(request)

    return jsonify(results)

@model_routes.route('/cnn', methods=['POST'])
def cnn():
    results = train_cnn(request)

    return jsonify(results)
