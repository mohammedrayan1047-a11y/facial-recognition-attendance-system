pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build') {
            steps {
                echo 'Creating Python virtual environment...'
                bat 'python -m venv .venv'

                echo 'Installing dependencies...'
                bat '.venv\\Scripts\\python.exe -m pip install --upgrade pip setuptools wheel'
                bat '.venv\\Scripts\\python.exe -m pip install --only-binary=:all: -r requirements.txt'
            }
        }

        stage('Test') {
            steps {
                echo 'Running Python syntax check...'
                bat '.venv\\Scripts\\python.exe -m compileall app.py database.py face_utils.py'

                echo 'Testing application dependencies...'
                bat '.venv\\Scripts\\python.exe -c "import cv2, numpy, pandas, openpyxl, flask, flask_sqlalchemy; print(''All dependencies imported successfully'')"'

                echo 'Testing Flask application...'
                bat '.venv\\Scripts\\python.exe -c "import app; print(''Flask application imported successfully'')"'
            }
        }

        stage('CI Success') {
            steps {
                echo 'Facial Recognition Attendance System CI build completed successfully!'
            }
        }
    }
}