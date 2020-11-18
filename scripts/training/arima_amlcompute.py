
import os

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
#from sklearn.externals import joblib
import joblib

from pandas import Grouper
#from pandas.plotting import lag_plot
#from pandas.plotting import autocorrelation_plot
from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.graphics.tsaplots import plot_pacf
from sklearn.metrics import mean_squared_error
from sklearn.metrics import r2_score
#from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller
#from sklearn.model_selection import TimeSeriesSplit
#from statsmodels.graphics.gofplots import qqplot
#from statsmodels.tsa.ar_model import AR
from statsmodels.tsa.arima_model import ARIMA

from azureml.core import Dataset, Run

run = Run.get_context()
# get input dataset by name
#dataset = run.input_datasets['robberies']

ws = run.experiment.workspace
dataset = Dataset.get_by_name(workspace=ws, name='robberies')

df = dataset.to_pandas_dataframe()
df.index = df['Month']
df = df.drop('Month', axis=1)
df.columns = ['Robberies']
series = pd.Series(df['Robberies'])

def mean_and_variance(X):
    split = int(len(X) / 2)
    X1, X2 = X[0:split], X[split:]
    mean1, mean2 = X1.mean(), X2.mean()
    var1, var2 = X1.var(), X2.var()
    print('mean1=%f, mean2=%f' % (mean1, mean2))
    print('variance1=%f, variance2=%f' % (var1, var2))
    
mean_and_variance(series.values)

def fuller_test(X):
    result = adfuller(X)
    print('ADF Statistic: %f' % result[0])
    print('p-value: %f' % result[1])
    print('Critical Values:')
    for key, value in result[4].items():
    	print('\t%s: %.3f' % (key, value))
        
fuller_test(series.values)

plot_acf(series)

plot_pacf(series)

X = series.values
size = int(len(X) * 0.66)
train, test = X[0:size], X[size:len(X)]

model = ARIMA(train, order=(4,2,1))
model_fit = model.fit(disp=0)
print(model_fit.summary())

# plot residual errors
residuals = pd.DataFrame(model_fit.resid)
residuals.plot()
plt.show()
residuals.plot(kind='kde')
plt.show()
print(residuals.describe())

predictions=model_fit.forecast(steps=test.size)[0]

mse = mean_squared_error(test, predictions)
rmse = np.sqrt(mse)
r2 = r2_score(test,predictions)
print('Test RMSE: %.3f' % rmse)
print('Test R2: %.3f' % r2)

#### ROLLING FORECAST

history = [x for x in train]
predictions = list()
for t in range(len(test)):
    model = ARIMA(history, order=(4,2,1))
    model_fit = model.fit(disp=0)
    output = model_fit.forecast()
    yhat = output[0]
    predictions.append(yhat)
    obs = test[t]
    history.append(obs)
    print('predicted=%f, expected=%f' % (yhat, obs))
error = mean_squared_error(test, predictions)
rmse = np.sqrt(mse)
r2 = r2_score(test,predictions)
print('Test RMSE: %.3f' % rmse)
print('Test R2: %.3f' % r2)

# plot
plt.plot(test)
plt.plot(predictions, color='red')
plt.show()

run.log('RMSE', rmse)
run.log('R2', r2)

model_file_name = 'arima_model.pkl'

os.makedirs('./outputs', exist_ok=True)
with open(model_file_name, 'wb') as file:
    joblib.dump(value=model_fit, filename='outputs/' + model_file_name)
