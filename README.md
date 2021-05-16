# Setting up prediction API

## 1. Setup

### 1.1 Setting up virtual environment
Setup a python virtual environment in your computer
```
virtualenv venv -p python3`
```

To activate virtual environment use following command:
- In Windows use: `venv\Scripts\activate`
- In Debian (Linux) use: `. venv/bin/activate`

### 1.2 Installing requirements
Run:
```
cd FIT5120_Epoch_BushFire/Prediction_API/
pip install -r requirements.txt
```
## 2. Running Application in local environment
TO run the flask application locally, run the following command:
```
python -m app
```
You can access the API using the endpoint http://localhost:5000/forecast?locality={locality}

## 3.Deploying the application on GCloud Compute Engine VM instance

To deploy this application use the [deployment documentation](DEPLOYMENT.md)
