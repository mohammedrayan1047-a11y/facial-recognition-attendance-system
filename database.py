from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import pickle

db = SQLAlchemy()

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    department = db.Column(db.String(100))
    year = db.Column(db.String(20))
    face_encoding = db.Column(db.LargeBinary, nullable=False)
    face_image_path = db.Column(db.String(255))
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    attendances = db.relationship('Attendance', backref='student', lazy=True)
    
    def get_encoding(self):
        """Deserialize face encoding from database"""
        return pickle.loads(self.face_encoding)
    
    def set_encoding(self, encoding):
        """Serialize face encoding for database storage"""
        self.face_encoding = pickle.dumps(encoding)

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), unique=True, nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100))
    
    # Relationship
    attendances = db.relationship('Attendance', backref='course', lazy=True)

class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(20), default='present')  # present, absent, late
    time_in = db.Column(db.Time, nullable=True)
    time_out = db.Column(db.Time, nullable=True)
    marked_by = db.Column(db.String(50))  # faculty name or system
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure unique attendance per student per course per day
    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', 'date', name='unique_attendance'),
    )