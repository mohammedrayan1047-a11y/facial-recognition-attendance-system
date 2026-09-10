import face_recognition
import cv2
import numpy as np
import pickle
import os

class FaceRecognitionSystem:
    def __init__(self, tolerance=0.6):
        self.tolerance = tolerance
        
    def encode_face_from_image(self, image_path):
        """Extract face encoding from uploaded image"""
        try:
            # Load image
            image = face_recognition.load_image_file(image_path)
            
            # Find face locations
            face_locations = face_recognition.face_locations(image)
            
            if len(face_locations) == 0:
                return None, "No face detected in the image"
            
            if len(face_locations) > 1:
                return None, "Multiple faces detected. Please upload a clear single face image"
            
            # Get face encoding
            face_encoding = face_recognition.face_encodings(image, face_locations)[0]
            
            return face_encoding, "Success"
            
        except Exception as e:
            return None, f"Error: {str(e)}"
    
    def detect_faces_from_camera(self):
        """Capture and detect faces from camera"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            return None, "Cannot access camera"
        
        print("\n📸 Camera opened. Press SPACE to capture, ESC to cancel...")
        
        face_locations = []
        frame = None
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Display the frame
            cv2.imshow('Face Registration - Press SPACE to capture, ESC to exit', frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == 32:  # SPACE key
                # Convert to RGB for face_recognition
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_frame)
                
                if len(face_locations) == 0:
                    print("❌ No face detected! Try again.")
                    continue
                
                if len(face_locations) > 1:
                    print("❌ Multiple faces detected! Only one person should be in frame.")
                    continue
                
                break
                
            elif key == 27:  # ESC key
                cap.release()
                cv2.destroyAllWindows()
                return None, "Cancelled by user"
        
        cap.release()
        cv2.destroyAllWindows()
        
        if frame is None:
            return None, "No frame captured"
        
        # Get face encoding
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        if len(face_encodings) == 0:
            return None, "Could not encode face"
        
        return face_encodings[0], "Success"
    
    def mark_attendance_from_camera(self, known_encodings, known_students):
        """Mark attendance by capturing from camera"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            return None, "Cannot access camera"
        
        print("\n📸 Camera opened. Looking for faces...")
        print("Press SPACE to capture attendance, ESC to cancel")
        
        marked_students = []
        frame = None
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Display the frame
            cv2.imshow('Mark Attendance - Press SPACE to capture, ESC to exit', frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == 32:  # SPACE key
                # Convert to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Detect faces
                face_locations = face_recognition.face_locations(rgb_frame)
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                
                if len(face_encodings) == 0:
                    print("❌ No face detected! Try again.")
                    continue
                
                # Match faces
                for face_encoding in face_encodings:
                    matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=self.tolerance)
                    
                    if True in matches:
                        matched_indices = [i for i, match in enumerate(matches) if match]
                        
                        for idx in matched_indices:
                            student = known_students[idx]
                            marked_students.append(student)
                            print(f"✅ Marked: {student.name} ({student.student_id})")
                
                if len(marked_students) == 0:
                    print("❌ No matching faces found in database!")
                else:
                    print(f"\n✅ Total marked: {len(marked_students)} students")
                
                break
                
            elif key == 27:  # ESC key
                cap.release()
                cv2.destroyAllWindows()
                return None, "Cancelled by user"
        
        cap.release()
        cv2.destroyAllWindows()
        
        return marked_students, "Success"