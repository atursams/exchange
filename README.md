# exchange
This service converts funds between different currencies.  
 
## General requirements
pip install django  
pip install aiohttp  
pip install redis  
pip install pandas  
pip install tabulate  
  
## Run dev server  
cd mainsite  
python manage.py runserver  
  
You can choose a port number like this:  
python manage.py runserver  

## Run django with asynchronous support

### requirements
sudo apt install gunicorn  
sudo apt-get install uvicorn  
pip install uvloop  

### Run  
cd mainsite 
gunicorn myproject.asgi:application -k uvicorn.workers.UvicornWorker
