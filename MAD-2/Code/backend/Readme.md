### Steps to run the projects

* Create a virtual env using python 3.10 and install requirements.txt
* Open terminal in the root folder
* Navigate to the backend folder and run 
```sh
    python -m src.app
```
* And in another terminal navigate to backend folder and run the below command
```sh
    celery -A src.app.celery worker -B -l INFO # for linux / macos
    celery -A src.app.celery worker --pool=solo -l INFO # for windows
    celery -A src.app.celery beat -l INFO # for windows
```
* Now open a new terminal and navigate to the frontend folder and run below comamnds
``` sh
    npm i
    npm run dev
```
* Open the url [Application Url](http://localhost:3000) and check