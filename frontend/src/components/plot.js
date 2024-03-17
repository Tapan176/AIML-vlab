{/* <Plot
              data={[
                  {
                      x: (datasetData && datasetData.csvData && Object.values(datasetData.csvData)[0]) ? 
                          Object.values(datasetData.csvData)[0].map(value => parseFloat(value)) : 
                          inputData.X,
                      y: (datasetData && datasetData.csvData && Object.values(datasetData.csvData)[1]) ? 
                          Object.values(datasetData.csvData)[1].map(value => parseFloat(value)) : 
                          inputData.y,
                      type: 'scatter',
                      mode: 'markers+lines',
                      marker: { color: 'blue' },
                  },
              ]}
              layout={{ width: 600, height: 400, title: 'Linear Regression Prediction' }}
            /> */}