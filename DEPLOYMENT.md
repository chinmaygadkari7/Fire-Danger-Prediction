# Deploying Flask Application on Google Cloud Platform

## 1. Setting up the environment

### 1.1 Update packages
```
sudo apt-get upgrade
sudo apt-get update
```
### 1.2 Installing required packages for system
```
sudo apt-get install python3-pip
sudo apt-get install virtualenv
sudo apt-get install ufw
```

### 1.3 Create Virtual environment and install dependencies

```
virtualenv env -p python3
. env/bin/activate
pip3 install -r requirements.txt
```

### 1.4 Installing NGINX server
```
sudo apt-get install nginx
```
### 1.5 Download dataset files to local machine
Make sure that you have enough access to the project. Setup Google cloud configuration first using command:
```
gcloud init
```
Once its done, download the data file using the command:
```
gsutil cp gs://hello-167512.appspot.com/soil_moisture_data.pkl <path-to-repository>/FIT5120_Epoch_BushFire/Prediction_API/data/
```

## 2 Adjust the firewall settings
```
sudo ufw enable
sudo ufw allow 'Nginx HTTP'
sudo ufw allow 'Nginx HTTPS'
```
Then we can check the status of the firewall as
```
sudo ufw status
```
and check the status of the Nginx server using command:
```
systemctl status nginx
```

## 3. Creating unit file
To create a service file for our app use the following command:
```
sudo nano /etc/systemd/system/app.service
```
Then add following content inside the file. It assumes that you have your virtual environment installed under path `/home/<username>/env`. If you are using different structure, then make sure to add your changes.
```
[Unit]
Description=A simple Flask uWSGI application
After=network.target

[Service]
User=<username>
Group=www-data
WorkingDirectory=<path-to-repository>/FIT5120_Epoch_BushFire/Prediction_API/
Environment="PATH=/home/<username>/env/bin"
ExecStart=/home/<username>/env/bin/uwsgi --ini app.ini

[Install]
WantedBy=multi-user.target
```

After this run the following set of commands to run the application and check the status:
```
sudo systemctl start app
sudo systemctl enable app
sudo systemctl status app
```

## 4. Setting up Nginx server with HTTP
We need to create new server block in Nginx sites-available. First open a file using command:
```
sudo nano /etc/nginx/sites-available/app
```
and then add the following contents:
```
server {
    listen 80;
    server_name fireprediction.ga www.foreprediction.ga;

    location / {
        include uwsgi_params;
        uwsgi_pass unix:<path-to-repository>/FIT5120_Epoch_BushFire/Prediction_API/app.sock;
    }
}
```

## 5. Generating SSL certificate public and private keys
### 5.1 Install `snapd`
```
sudo apt-get install snapd
sudo snap install core; sudo snap refresh core
```
### 5.2 Install certbot
```
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
```
### 5.3 Generating certificates
Run the following command and fill out the necessary details
```
sudo certbot certonly --nginx
```

Once you have your certificates, make sure you note down the path to public and private key `.pem` files.

## 6. Updating the Nginx
### 6.1 Adding certificates
Open the Nginx configuration file using
```
sudo nano /etc/nginx/sites-available/app
```
and update the file with following contents
```
server {
    listen 443 ssl;
    server_name fireprediction.ga www.foreprediction.ga;
    ssl_certificate     <path-to-public-key .pem>;
    ssl_certificate_key <path-to-private-key .pem>;
    ssl_protocols       TLSv1 TLSv1.1 TLSv1.2;
    ssl_ciphers         HIGH:!aNULL:!MD5;
    location / {
        include uwsgi_params;
        uwsgi_pass unix:<path-to-repository>/FIT5120_Epoch_BushFire/Prediction_API/app.sock;
    }
}
```
### 6.2 Creating links
```
sudo ln -s /etc/nginx/sites-available/app /etc/nginx/sites-enabled
sudo nginx -t
```
### 6.3 Restart the Nginx server
```
sudo systemctl restart nginx
```
