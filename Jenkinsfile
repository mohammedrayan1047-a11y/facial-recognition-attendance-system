pipeline {
    agent any

    stages {

        // =========================
        // 1. BUILD
        // =========================
        stage('Build') {
            steps {
                echo 'Creating Python virtual environment...'

                bat '"C:\\Users\\moham\\AppData\\Local\\Programs\\Python\\Python311\\python.exe" -m venv .venv'

                echo 'Installing dependencies...'

                bat '.venv\\Scripts\\python.exe -m pip install --upgrade pip setuptools wheel'

                bat '.venv\\Scripts\\python.exe -m pip install --only-binary=:all: -r requirements.txt'
            }
        }


        // =========================
        // 2. TEST
        // =========================
        stage('Test') {
            steps {

                echo 'Running Python syntax check...'

                bat '.venv\\Scripts\\python.exe -m compileall app.py database.py face_utils.py'


                echo 'Testing dependencies...'

                bat '.venv\\Scripts\\python.exe -c "import cv2, numpy, pandas, openpyxl, flask, flask_sqlalchemy; print(chr(65)+chr(108)+chr(108)+chr(32)+chr(100)+chr(101)+chr(112)+chr(101)+chr(110)+chr(100)+chr(101)+chr(110)+chr(99)+chr(105)+chr(101)+chr(115)+chr(32)+chr(105)+chr(109)+chr(112)+chr(111)+chr(114)+chr(116)+chr(101)+chr(100)+chr(32)+chr(115)+chr(117)+chr(99)+chr(99)+chr(101)+chr(115)+chr(115)+chr(102)+chr(117)+chr(108)+chr(108)+chr(121))"'


                echo 'Testing Flask application...'

                bat '.venv\\Scripts\\python.exe -c "import app; print(chr(70)+chr(108)+chr(97)+chr(115)+chr(107)+chr(32)+chr(97)+chr(112)+chr(112)+chr(108)+chr(105)+chr(99)+chr(97)+chr(116)+chr(105)+chr(111)+chr(110)+chr(32)+chr(105)+chr(109)+chr(112)+chr(111)+chr(114)+chr(116)+chr(101)+chr(100)+chr(32)+chr(115)+chr(117)+chr(99)+chr(99)+chr(101)+chr(115)+chr(115)+chr(102)+chr(117)+chr(108)+chr(108)+chr(121))"'
            }
        }


        // =========================
        // 3. DEPLOY
        // =========================
        stage('Deploy') {
            steps {

                echo 'Deploying Flask application...'

                bat 'if not exist deployed mkdir deployed'

                bat 'copy /Y app.py deployed\\app.py'

                bat 'copy /Y database.py deployed\\database.py'

                bat 'copy /Y face_utils.py deployed\\face_utils.py'

                bat 'copy /Y requirements.txt deployed\\requirements.txt'

                bat 'xcopy /E /I /Y templates deployed\\templates'

                bat 'xcopy /E /I /Y static deployed\\static'

                echo 'Flask application deployed successfully!'
            }
        }


        // =========================
        // 4. CI SUCCESS
        // =========================
        stage('CI Success') {
            steps {

                echo 'Facial Recognition Attendance System CI build completed successfully!'

            }
        }
    }
}