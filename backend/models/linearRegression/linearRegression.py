from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np
import csv
import os
import matplotlib.pyplot as plt

def get_column_names(csv_file):
    with open(csv_file, 'r', newline='') as file:
        reader = csv.reader(file)
        column_names = next(reader)  # Read the first row which contains column names
    return column_names

def simpleLinearRegression(request):
    data = request.json

    X = None
    y = None

    if 'X' in data and 'y' in data:  # If X and y are provided
        X = np.array(data['X'])
        y = np.array(data['y'])
        X = X.reshape(-1, 1)
    elif 'filename' in data:  # If filename is provided
        # Construct file path
        directory = 'static/uploads'
        filepath = os.path.join(directory, data['filename'])

        try:
            # Read CSV file
            dataset = pd.read_csv(filepath)
            X = dataset.iloc[:, :-1].values
            y = dataset.iloc[:, -1].values
        except FileNotFoundError:
            return {"error": "File not found"}
        except Exception as e:
            return {"error": str(e)}
    else:
        return {"error": "Neither X and y nor filename provided"}

    # Splitting the dataset into the Training set and Test set
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 1/3, random_state = 0)

    # Fitting Simple Linear Regression to the Training set
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Predicting the Test set results
    y_pred = model.predict(X_test)

    columnNames = get_column_names(filepath)
    print(columnNames)

    outputImageUrls = [
        os.path.join(directory, 'linearRegressionTrainGraph.jpg'),
        os.path.join(directory, 'linearRegressionTestGraph.jpg')
    ]

    # Visualising the Training set results
    plt.scatter(X_train, y_train, color = 'red')
    plt.plot(X_train, model.predict(X_train), color = 'blue')
    plt.title('Salary vs Experience (Training set)')
    plt.xlabel('Years of Experience')
    plt.ylabel('Salary')
    plt.savefig(outputImageUrls[0])

    # Visualising the Test set results
    plt.scatter(X_test, y_test, color = 'red')
    plt.plot(X_train, model.predict(X_train), color = 'blue')
    plt.title('Salary vs Experience (Test set)')
    plt.xlabel('Years of Experience')
    plt.ylabel('Salary')
    plt.savefig(outputImageUrls[1])

    # model.fit(X.reshape(-1, 1), y)

    # # Predict
    # y_pred = model.predict(X.reshape(-1, 1))

    # Return results
    return ({"coefficients": model.coef_.tolist(), "intercept": model.intercept_, "predictions": y_pred.tolist(), "outputImageUrls": outputImageUrls})
