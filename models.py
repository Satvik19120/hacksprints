from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'Doctor' or 'MR' or 'Patient'
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    
    # Relationship for messages sent by the user
    messages_sent = db.relationship('Message',
                                    foreign_keys='Message.sender_id',
                                    backref='sender',
                                    lazy=True)
    
    # Relationship for messages received by the user
    messages_received = db.relationship('Message',
                                        foreign_keys='Message.recipient_id',
                                        backref='recipient',
                                        lazy=True)

# Medicine model
class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    alternative = db.Column(db.String(100), nullable=True)  # Generic/Substitute

# Message model for Doctor-MR communication
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

# Patient Assistance Request model
class AssistanceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(100), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Link to the assisting doctor
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'), nullable=False)  # Requested medicine
    status = db.Column(db.String(50), default='Pending')  # Status: Pending, Approved, Rejected
    reason = db.Column(db.String(255), nullable=True)  # Optional: Reason for request
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    doctor = db.relationship('User', backref='assistance_requests', lazy=True)
    medicine = db.relationship('Medicine', backref='assistance_requests', lazy=True)


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Patient booking the appointment
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Doctor for the appointment
    date = db.Column(db.DateTime, nullable=False)  # Appointment date and time
    status = db.Column(db.String(50), default='Pending')  # "Pending", "Confirmed", "Completed", "Cancelled"
    prescription = db.relationship('Prescription', backref='appointment', uselist=False)  # One-to-one relationship with Prescription

class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)  # Link to appointment
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'), nullable=False)  # Medicine prescribed
    dosage = db.Column(db.String(100), nullable=False)  # Dosage instructions
    duration = db.Column(db.String(100), nullable=False)  # Duration of medication (e.g., "5 days", "2 weeks")
