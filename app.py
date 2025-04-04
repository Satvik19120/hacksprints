from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User, Medicine, Message, AssistanceRequest, Appointment, Prescription
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'h@cksprint@123#'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hacksprint.db'
app.app_context().push()
db.init_app(app)
print("----your application started----")


# Home Page
@app.route("/")
def home():
    return render_template("home.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        role = request.form['role']
        password = request.form['password']
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please log in.', 'error')
            return redirect(url_for('register'))
        
        # Create a new user
        new_user = User(name=name, email=email, role=role, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            # Log the user in
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_role'] = user.role
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access your dashboard.', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if user.role == 'Doctor':
        return redirect(url_for('doctor_dashboard'))
    elif user.role == 'MR':
        return redirect(url_for('mr_dashboard'))
    elif user.role == 'Patient':
        return redirect(url_for('patient_dashboard'))
    else:
        flash('Invalid user role.', 'error')
        return redirect(url_for('login'))


@app.route('/doctor_dashboard', methods=['GET', 'POST'])
def doctor_dashboard():
    if 'user_id' not in session or User.query.get(session['user_id']).role != 'Doctor':
        flash('Access denied. It\'s For Doctors Only.', 'error')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    #Fetch medicines and messages for the doctor
    user = User.query.get(session['user_id'])
    messages = Message.query.all()
    medicines = Medicine.query.all()
    # Fetch all appointment requests for this doctor
    appointments = Appointment.query.filter_by(doctor_id=user.id).all()
    #Fetch all created assistance request for background area patients
    assistance_requests = AssistanceRequest.query.filter_by(doctor_id=user.id).all()

    if request.method == 'POST':
        appointment_id = request.form.get('appointment_id')
        action = request.form.get('action')
        prescription_text = request.form.get('prescription')

        # Update appointment status or add prescription
        if appointment_id:
            appointment = Appointment.query.get(appointment_id)
            if appointment:
                if action == 'Approve':
                    appointment.status = 'Confirmed'
                elif action == 'Reject':
                    appointment.status = 'Rejected'
                elif action == 'Confirmed' and prescription_text:
                    # Add prescription
                    prescription = Prescription(
                        appointment_id=appointment.id,
                        medicine_id=request.form.get('medicine_id'),
                        dosage=request.form.get('dosage'),
                        duration=request.form.get('duration')
                    )
                    db.session.add(prescription)
                    appointment.status = 'Completed'

                db.session.commit()
                flash("Appointment updated successfully!", "success")
            else:
                flash("Appointment not found!", "danger")

    return render_template('doctor_dashboard.html', user=user, messages=messages, medicines=medicines, appointments=appointments, assistance_requests=assistance_requests)



@app.route('/mr_dashboard')
def mr_dashboard():
    if 'user_id' not in session or User.query.get(session['user_id']).role != 'MR':
        flash('Access denied. MRs only.', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    #Fetch messages sent by the MR and medicine stock details
    messages = Message.query.all()
    medicines = Medicine.query.all()
    #Fetch requests to donate medicines
    requests = AssistanceRequest.query.all()
    return render_template('mr_dashboard.html', user=user, messages=messages, medicines=medicines, requests=requests)



@app.route('/patient_dashboard', methods=['GET'])
def patient_dashboard():
    if 'user_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if user.role != 'Patient':
        flash("Access restricted to patients only.", "danger")
        return redirect(url_for('dashboard'))
    # Fetch all assistance requests for the logged-in patient
    assistance_requests = AssistanceRequest.query.filter_by(patient_name=user.name).all()
    # Fetch the patient’s appointments
    appointments = Appointment.query.filter_by(patient_id=user.id).all()
    medicines=Medicine.query.all()
    doctors=User.query.all()
    return render_template('patient_dashboard.html', user=user,doctors=doctors,medicines=medicines, appointments=appointments, assistance_requests=assistance_requests)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# Send a message
@app.route('/send_message', methods=['GET', 'POST'])
def send_message():
    if 'user_id' not in session:
        flash('Please log in to send messages.', 'error')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        recipient_id = request.form.get('recipient_id')
        content = request.form.get('content')

        if not recipient_id or not content:
            flash('All fields are required.', 'error')
            return redirect(url_for('send_message'))

        recipient = User.query.get(recipient_id)
        if not recipient:
            flash('Recipient not found.', 'error')
            return redirect(url_for('send_message'))

        # Create and save the message
        message = Message(sender_id=user.id, recipient_id=recipient.id, content=content, timestamp=datetime.utcnow())
        db.session.add(message)
        db.session.commit()

        flash('Message sent successfully!', 'success')
        return redirect(url_for('dashboard'))

    # Fetch potential recipients
    recipients = User.query.filter(User.id != user.id and User.role!=user.role).all()
    return render_template('send_message.html', user=user, recipients=recipients)

# View received messages
@app.route('/received_messages')
def received_messages():
    if 'user_id' not in session:
        flash('Please log in to view messages.', 'error')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    messages = user.messages_received

    return render_template('received_messages.html', user=user, messages=messages)

# View all medicines
@app.route('/medicines')
def view_medicines():
    if 'user_id' not in session:
        flash('Please log in to view medicines.', 'error')
        return redirect(url_for('login'))

    medicines = Medicine.query.all()
    return render_template('medicines.html', medicines=medicines)

# Add medicine (for MR)
@app.route('/add_medicine', methods=['GET', 'POST'])
def add_medicine():
    if 'user_id' not in session:
        flash('Please log in.', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if user.role != 'MR':
        flash('Access denied. Only MRs can add medicines.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        stock = request.form.get('stock')
        price = request.form.get('price')
        alternative = request.form.get('alternative')
        
        if not name or not stock or not price:
            flash('Name, stock, and price are required.', 'error')
            return redirect(url_for('add_medicine'))
        
        # Save medicine
        medicine = Medicine(name=name, stock=int(stock), price=float(price), alternative=alternative)
        db.session.add(medicine)
        db.session.commit()
        
        flash('Medicine added successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('add_medicine.html')




#Patient Assistance System
@app.route('/create_assistance_request', methods=['GET', 'POST'])
def create_assistance_request():
    if 'user_id' not in session:
        flash('Please log in.', 'error')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if user.role != 'Doctor':
        flash('Access denied. Only Doctors can create assistance requests.', 'error')
        return redirect(url_for('dashboard'))

    medicines = Medicine.query.all()  # Fetch all available medicines
    patients=User.query.all()
    if request.method == 'POST':
        patient_name = request.form.get('patient_name')
        medicine_id = request.form.get('medicine_id')
        reason = request.form.get('reason')

        if not patient_name or not medicine_id:
            flash('Please fill in all required fields.', 'error')
            check=[patient_name,medicine_id,reason]
            return redirect(url_for('create_assistance_request'))

        assistance_request = AssistanceRequest(
            patient_name=patient_name,
            doctor_id=user.id,
            medicine_id=medicine_id,
            reason=reason,
            status='Pending'
        )
        db.session.add(assistance_request)
        db.session.commit()

        flash('Patient Assistance Request created successfully!', 'success')
        return redirect(url_for('doctor_dashboard'))

    return render_template('create_assistance_request.html', medicines=medicines,patients=patients)

#Route for MRs to view and accept/reject request
@app.route('/view_assistance_requests', methods=['GET', 'POST'])
def view_assistance_requests():
    if 'user_id' not in session:
        flash('Please log in.', 'error')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if user.role != 'MR':
        flash('Access denied. Only MRs can view assistance requests.', 'error')
        return redirect(url_for('dashboard'))

    requests = AssistanceRequest.query.all()  # Fetch all pending requests

    if request.method == 'POST':
        request_id = request.form.get('request_id')
        action = request.form.get('action')

        assistance_request = AssistanceRequest.query.get(request_id)
        if action == 'approve':
            assistance_request.status = 'Approved'
        elif action == 'reject':
            assistance_request.status = 'Rejected'
        
        db.session.commit()
        flash(f'Request {action}ed successfully!', 'success')
        return redirect(url_for('view_assistance_requests'))

    return render_template('view_assistance_requests.html', requests=requests)


#appointment booking
@app.route('/book_appointment', methods=['GET', 'POST'])
def book_appointment():
    if 'user_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if user.role != 'Patient':
        flash("Access restricted to patients only.", "danger")
        return redirect(url_for('dashboard'))

    doctors = User.query.filter_by(role='Doctor').all()

    if request.method == 'POST':
        doctor_id = request.form['doctor_id']
        appointment_date_str = request.form['date']
        date = datetime.strptime(appointment_date_str, '%Y-%m-%dT%H:%M')
        new_appointment = Appointment(
            patient_id=user.id,
            doctor_id=doctor_id,
            date=date,
            status='Pending'
        )
        db.session.add(new_appointment)
        db.session.commit()
        flash("Your appointment request has been submitted!", "success")
        return redirect(url_for('patient_dashboard'))

    return render_template('book_appointment.html', doctors=doctors)


#manage appointment
@app.route('/manage_appointments', methods=['GET', 'POST'])
def manage_appointments():
    if 'user_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if user.role != 'Doctor':
        flash("Access restricted to doctors only.", "danger")
        return redirect(url_for('dashboard'))

    appointments = Appointment.query.filter_by(doctor_id=user.id).all()

    if request.method == 'POST':
        appointment_id = int(request.form['appointment_id'])
        action = request.form['action']  # Confirm or Cancel
        appointment = Appointment.query.get(appointment_id)

        if action == 'Confirm':
            appointment.status = 'Confirmed'
        elif action == 'Cancel':
            appointment.status = 'Cancelled'

        db.session.commit()
        flash(f"Appointment #{appointment_id} has been {action.lower()}ed.", "success")
        return redirect(url_for('manage_appointments'))

    return render_template('manage_appointments.html', appointments=appointments)


#medicine prescription


@app.route('/prescribe_medicine/<int:appointment_id>', methods=['GET', 'POST'])
def prescribe_medicine(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    medicines = Medicine.query.all()
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        # Retrieve form data
        medicine_id = request.form.get('medicine_id')
        dosage = request.form.get('dosage')
        duration = request.form.get('duration')

        # Validate the inputs
        if not medicine_id or not dosage or not duration:
            flash('All fields are required to prescribe medicine.', 'danger')
            return redirect(url_for('prescribe_medicine',user=user, appointment_id=appointment_id,medicines=medicines))

        # Add prescription to the database
        prescription = Prescription(
            appointment_id=appointment_id,
            medicine_id=medicine_id,
            dosage=dosage,
            duration=duration
        )
        db.session.add(prescription)
        appointment.status = 'Completed'  # Mark appointment as completed
        db.session.commit()

        flash('Prescription added successfully!', 'success')
        return redirect(url_for('doctor_dashboard'))

    return render_template('prescribe_medicine.html',user=user, appointment=appointment, medicines=medicines)




if __name__ == "__main__":
    app.run(debug=True)
