import numpy as np
from sklearn.linear_model import LinearRegression

X = np.array([[1, 1], [1, 2], [2, 2], [2, 3]])
y = np.array([2, 3, 4, 5])

def linearRegression (X, y):
    model = LinearRegression()
    model.fit(X, y)
    predictions = model.predict([[3, 5]])
    return predictions
