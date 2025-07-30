from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'b7he#fyy@gfv$dr%'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///connectcare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Fix mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Fixed this line
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'n.ntare@alustudent.com'
app.config['MAIL_PASSWORD'] = 'eytr yrnh fehr flci'

db = SQLAlchemy(app)
mail = Mail(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Define models inline to avoid circular imports
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Add missing home route
@app.route('/')
def home():
    return redirect(url_for('login'))

# Add missing book_appointment route
@app.route('/book')
@login_required
def book_appointment():
    return redirect(url_for('department_list'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_pw = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        user = User(name=request.form['name'], email=request.form['email'], password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('book_appointment'))
        else:
            flash('Login failed. Check email and password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/departments')
@login_required
def department_list():
    departments = ['Dentistry', 'General Medicine', 'Pediatrics', 'Gynecology']
    return render_template('departments.html', departments=departments)

@app.route('/book/<department>', methods=['GET', 'POST'])
@login_required
def book_by_department(department):
    if request.method == 'POST':
        date = request.form['date']
        time = request.form['time']
        appointment = Appointment(
            user_email=current_user.email,
            date=date,
            time=time,
            department=department
        )
        db.session.add(appointment)
        db.session.commit()

        # Email
        try:
            msg = Message(
                f"Your {department} Appointment is Confirmed",
                sender='n.ntare@alustudent.com',
                recipients=[current_user.email]
            )
            msg.body = f"""
Hi {current_user.name},

Your appointment for {department} has been booked.

📅 Date: {date}
🕒 Time: {time}

Thank you for choosing ConnectCare!
"""
            mail.send(msg)
            flash(f"Appointment for {department} booked! Confirmation email sent.", 'success')
        except Exception as e:
            # Handle email errors gracefully
            flash(f"Appointment for {department} booked! (Email notification failed)", 'warning')
        
        return redirect(url_for('my_appointments'))

    return render_template('book.html', department=department)

@app.route('/my-appointments')
@login_required
def my_appointments():
    appointments = Appointment.query.filter_by(user_email=current_user.email).order_by(Appointment.date.desc()).all()
    return render_template('my_appointments.html', appointments=appointments)

@app.route('/cancel/<int:appointment_id>', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)

    # Ensure user owns the appointment
    if appointment.user_email != current_user.email:
        flash("You are not authorized to cancel this appointment.", 'danger')
        return redirect(url_for('my_appointments'))

    db.session.delete(appointment)
    db.session.commit()
    flash("Appointment canceled successfully.", 'success')
    return redirect(url_for('my_appointments'))


@app.route('/health')
def health_check():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    app.run(debug=True)