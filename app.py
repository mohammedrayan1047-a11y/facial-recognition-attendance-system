from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import pickle
import cv2
import numpy as np

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Load face cascade classifier
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Database Models
class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    department = db.Column(db.String(100))
    year = db.Column(db.String(20))
    face_data = db.Column(db.LargeBinary, nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_face_data(self):
        return pickle.loads(self.face_data)
    
    def set_face_data(self, face_images):
        self.face_data = pickle.dumps(face_images)

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), unique=True, nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100))

class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(20), default='present')
    time_in = db.Column(db.Time, nullable=True)
    marked_by = db.Column(db.String(50))
    
    student = db.relationship('Student', backref='attendances')
    course = db.relationship('Course', backref='attendances')

# Create tables and add courses
with app.app_context():
    db.create_all()
    print("Database created successfully!")
    
    # Add all courses if none exist
    if Course.query.count() == 0:
        all_courses = [
            # Original 3 courses
            Course(course_code='CS101', course_name='Introduction to Programming', department='Computer Science'),
            Course(course_code='CS201', course_name='Data Structures', department='Computer Science'),
            Course(course_code='MA101', course_name='Mathematics', department='Mathematics'),
            # New 6 courses
            Course(course_code='CS301', course_name='Real Time Research Project', department='Computer Science'),
            Course(course_code='EC101', course_name='Business Economics and Financial Analysis', department='Economics'),
            Course(course_code='MA201', course_name='Discrete Mathematics', department='Mathematics'),
            Course(course_code='CS302', course_name='Software Engineering', department='Computer Science'),
            Course(course_code='CS303', course_name='Operating Systems', department='Computer Science'),
            Course(course_code='CS304', course_name='Database Management Systems', department='Computer Science')
        ]
        
        for course in all_courses:
            db.session.add(course)
        
        db.session.commit()
        print(f"{len(all_courses)} courses created successfully!")

def capture_face_images():
    """Capture multiple face images from camera"""
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        return None, "Cannot access camera. Please check if camera is connected."
    
    print("\n" + "="*50)
    print("📸 FACE REGISTRATION")
    print("="*50)
    print("Please look at the camera")
    print("Press SPACE to capture image (need 20 images)")
    print("Press ESC to cancel")
    print("="*50 + "\n")
    
    face_images = []
    count = 0
    
    while count < 20:
        ret, frame = cap.read()
        if not ret:
            break
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        # Draw rectangle and display info
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            cv2.putText(frame, f"Captured: {count}/20", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, "Press SPACE to capture", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imshow('Face Registration - Press SPACE to capture, ESC to exit', frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == 32:  # SPACE key
            if len(faces) > 0:
                (x, y, w, h) = faces[0]
                face_roi = gray[y:y+h, x:x+w]
                face_resized = cv2.resize(face_roi, (100, 100))
                face_images.append(face_resized)
                count += 1
                print(f"Captured image {count}/20")
            else:
                print("No face detected! Please look directly at camera.")
        
        elif key == 27:  # ESC key
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    if len(face_images) < 10:
        return None, f"Only captured {len(face_images)} images. Need at least 10 for good recognition."
    
    print(f"\nSuccessfully captured {len(face_images)} face images!")
    return face_images, "Success"

def mark_attendance_with_camera():
    """Mark attendance by recognizing faces from camera"""
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        return None, "Cannot access camera"
    
    # Get all students
    students = Student.query.all()
    
    if len(students) == 0:
        cap.release()
        return None, "No students registered"
    
    # Prepare training data
    faces = []
    labels = []
    label_map = {}
    
    for idx, student in enumerate(students):
        face_images = student.get_face_data()
        for face_img in face_images:
            faces.append(face_img)
            labels.append(idx)
        label_map[idx] = student
    
    # Train recognizer
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels))
    
    print("\n" + "="*50)
    print("ATTENDANCE MARKING")
    print("="*50)
    print("Please position faces in front of camera")
    print("Press SPACE to capture and mark attendance")
    print("Press ESC to cancel")
    print("="*50 + "\n")
    
    marked_students = []
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces_detected = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        # Process each detected face
        for (x, y, w, h) in faces_detected:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            face_roi = gray[y:y+h, x:x+w]
            face_resized = cv2.resize(face_roi, (100, 100))
            
            # Try to recognize the face
            label, confidence = recognizer.predict(face_resized)
            
            # Lower confidence = better match
            if confidence < 100:
                student = label_map.get(label)
                if student and student not in marked_students:
                    marked_students.append(student)
                    cv2.putText(frame, f"{student.name} ({100-confidence:.1f}%)", 
                               (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "Unknown", (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        # Display instructions
        cv2.putText(frame, f"Marked: {len(marked_students)} students", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Press SPACE to confirm attendance", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imshow('Mark Attendance - Press SPACE to confirm, ESC to cancel', frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == 32:  # SPACE key
            break
            
        elif key == 27:  # ESC key
            marked_students = None
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    return marked_students, "Success"

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and password == 'admin123':
            session['user'] = 'admin'
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    total_students = Student.query.count()
    total_courses = Course.query.count()
    today_attendance = Attendance.query.filter_by(date=date.today()).count()
    recent_attendance = Attendance.query.order_by(Attendance.date.desc()).limit(10).all()
    
    return render_template('dashboard.html', 
                         total_students=total_students,
                         total_courses=total_courses,
                         today_attendance=today_attendance,
                         recent_attendance=recent_attendance)

@app.route('/register_student', methods=['GET', 'POST'])
def register_student():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        name = request.form.get('name')
        email = request.form.get('email')
        department = request.form.get('department')
        year = request.form.get('year')
        
        # Check if student already exists
        existing = Student.query.filter_by(student_id=student_id).first()
        if existing:
            flash(f'Student with ID {student_id} already exists!', 'error')
            return redirect(url_for('register_student'))
        
        # Capture face images
        face_images, message = capture_face_images()
        
        if face_images is None:
            flash(f'Face capture failed: {message}', 'error')
            return redirect(url_for('register_student'))
        
        # Create new student
        student = Student(
            student_id=student_id,
            name=name,
            email=email,
            department=department,
            year=year
        )
        student.set_face_data(face_images)
        
        try:
            db.session.add(student)
            db.session.commit()
            flash(f'Student {name} registered successfully with {len(face_images)} face images!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
        
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/mark_attendance', methods=['GET', 'POST'])
def mark_attendance():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        
        if not course_id:
            flash('Please select a course!', 'error')
            return redirect(url_for('mark_attendance'))
        
        course = Course.query.get(course_id)
        if not course:
            flash('Course not found!', 'error')
            return redirect(url_for('mark_attendance'))
        
        # Check if any students are registered
        if Student.query.count() == 0:
            flash('No students registered in the system! Please register students first.', 'error')
            return redirect(url_for('mark_attendance'))
        
        print(f"\n📸 Starting attendance marking for course: {course.course_name}")
        
        # Mark attendance
        marked_students, message = mark_attendance_with_camera()
        
        if marked_students is None:
            flash(f'Attendance marking failed: {message}', 'error')
            return redirect(url_for('mark_attendance'))
        
        # Save attendance records
        today = date.today()
        marked_count = 0
        
        for student in marked_students:
            # Check if attendance already marked for today
            existing = Attendance.query.filter_by(
                student_id=student.id,
                course_id=course_id,
                date=today
            ).first()
            
            if not existing:
                attendance = Attendance(
                    student_id=student.id,
                    course_id=course_id,
                    date=today,
                    status='present',
                    time_in=datetime.now().time(),
                    marked_by=session.get('username', 'system')
                )
                db.session.add(attendance)
                marked_count += 1
        
        db.session.commit()
        
        if marked_count > 0:
            flash(f'Attendance marked for {marked_count} students in {course.course_name}!', 'success')
        else:
            flash('No new attendance marked. Students may have already been marked today.', 'warning')
        
        return redirect(url_for('dashboard'))
    
    courses = Course.query.all()
    return render_template('mark_attendance.html', courses=courses)

@app.route('/view_attendance')
def view_attendance():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    course_id = request.args.get('course_id')
    month = request.args.get('month')
    year = request.args.get('year')
    
    query = Attendance.query
    
    if course_id:
        query = query.filter_by(course_id=course_id)
    
    if month and year:
        query = query.filter(db.extract('month', Attendance.date) == int(month))
        query = query.filter(db.extract('year', Attendance.date) == int(year))
    
    attendance_records = query.order_by(Attendance.date.desc()).all()
    
    total_records = len(attendance_records)
    present_count = len([a for a in attendance_records if a.status == 'present'])
    
    # Calculate student statistics
    student_stats = {}
    for record in attendance_records:
        if record.student_id not in student_stats:
            student_stats[record.student_id] = {'total': 0, 'present': 0, 'name': record.student.name}
        student_stats[record.student_id]['total'] += 1
        if record.status == 'present':
            student_stats[record.student_id]['present'] += 1
    
    for student_id in student_stats:
        total = student_stats[student_id]['total']
        present = student_stats[student_id]['present']
        student_stats[student_id]['percentage'] = (present / total * 100) if total > 0 else 0
    
    courses = Course.query.all()
    
    return render_template('reports.html', 
                         attendance_records=attendance_records,
                         student_stats=student_stats,
                         courses=courses,
                         total_records=total_records,
                         present_count=present_count)

@app.route('/monthly_report')
def monthly_report():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Get current month
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Get all attendance for current month
    attendance_data = Attendance.query.filter(
        db.extract('month', Attendance.date) == current_month,
        db.extract('year', Attendance.date) == current_year
    ).all()
    
    # Calculate monthly statistics
    students = Student.query.all()
    monthly_stats = []
    
    for student in students:
        student_attendance = [a for a in attendance_data if a.student_id == student.id]
        total_days = len(set([a.date for a in student_attendance]))
        present_days = len([a for a in student_attendance if a.status == 'present'])
        
        percentage = (present_days / total_days * 100) if total_days > 0 else 0
        
        monthly_stats.append({
            'student_id': student.student_id,
            'name': student.name,
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': total_days - present_days,
            'percentage': round(percentage, 2)
        })
    
    return render_template('monthly_report.html', 
                         monthly_stats=monthly_stats,
                         month=current_month,
                         year=current_year)

@app.route('/export_attendance')
def export_attendance():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Get all attendance records
    records = Attendance.query.all()
    
    # Prepare data for export
    data = []
    for record in records:
        data.append({
            'Date': record.date,
            'Student ID': record.student.student_id,
            'Student Name': record.student.name,
            'Course': record.course.course_name,
            'Status': record.status,
            'Time In': record.time_in,
            'Marked By': record.marked_by
        })
    
    # Create DataFrame
    import pandas as pd
    from io import BytesIO
    
    df = pd.DataFrame(data)
    
    # Create Excel file
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Attendance', index=False)
        
        # Add summary sheet
        if len(data) > 0:
            summary = df.groupby(['Student Name', 'Course']).agg({
                'Status': lambda x: (x == 'present').sum(),
                'Date': 'count'
            }).reset_index()
            summary.columns = ['Student Name', 'Course', 'Present Days', 'Total Days']
            summary['Percentage'] = (summary['Present Days'] / summary['Total Days'] * 100).round(2)
            summary.to_excel(writer, sheet_name='Summary', index=False)
    
    output.seek(0)
    
    # Send file
    from flask import send_file
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'attendance_report_{date.today()}.xlsx'
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎯 FACE RECOGNITION ATTENDANCE SYSTEM")
    print("="*60)
    print("\nSystem starting...")
    print("Access the application at: http://127.0.0.1:5000")
    print("\nDefault Login:")
    print("   Username: admin")
    print("   Password: admin123")
    print("\nAvailable Courses:")
    print("   1. CS101 - Introduction to Programming")
    print("   2. CS201 - Data Structures")
    print("   3. MA101 - Mathematics")
    print("   4. CS301 - Real Time Research Project")
    print("   5. EC101 - Business Economics and Financial Analysis")
    print("   6. MA201 - Discrete Mathematics")
    print("   7. CS302 - Software Engineering")
    print("   8. CS303 - Operating Systems")
    print("   9. CS304 - Database Management Systems")
    print("\n Important Notes:")
    print("   1. Make sure your camera is connected")
    print("   2. Register students first with their face")
    print("   3. Good lighting improves face recognition")
    print("   4. Student should look directly at camera during registration")
    print("="*60 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000)