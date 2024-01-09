from flask import Flask, render_template, request
import linearRegression from 'models/linear_regression.py'

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/linear-regression', methods=['POST'])
def linear_regression():
    model_name = request.form['model_name']
    parameters = {param: request.form[param] for param in request.form if param != 'model_name'}
    
    # Set default values if not provided by the user
    for param, default_value in linearRegression.default_parameters.items():
        parameters.setdefault(param, default_value)

    result = linearRegression.run_model(parameters)
    
    return render_template('result.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)
