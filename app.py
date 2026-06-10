from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'foodwaste_secret_key_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///foodwaste.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ─── MODELS ───────────────────────────────────────────────────────────────────

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(15))
    role = db.Column(db.String(10), nullable=False)  # donor / ngo / admin
    org_name = db.Column(db.String(150))
    address = db.Column(db.String(250))
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    donations = db.relationship('Donation', backref='donor', lazy=True)
    requests = db.relationship('FoodRequest', backref='ngo', lazy=True)

class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    food_name = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.String(100), nullable=False)
    serves_people = db.Column(db.Integer)
    food_type = db.Column(db.String(10))  # veg / non-veg
    cooked_at = db.Column(db.DateTime)
    expiry_time = db.Column(db.DateTime, nullable=False)
    pickup_address = db.Column(db.String(250), nullable=False)
    contact = db.Column(db.String(15))
    instructions = db.Column(db.Text)
    status = db.Column(db.String(20), default='available')  # available / requested / completed / expired
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    requests = db.relationship('FoodRequest', backref='donation', lazy=True)

class FoodRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donation_id = db.Column(db.Integer, db.ForeignKey('donation.id'), nullable=False)
    ngo_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending / accepted / rejected / completed
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'role' not in session or session['role'] not in roles:
                flash('Access denied.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated
    return decorator

def mark_expired_donations():
    now = datetime.utcnow()
    expired = Donation.query.filter(
        Donation.expiry_time < now,
        Donation.status == 'available'
    ).all()
    for d in expired:
        d.status = 'expired'
    db.session.commit()

# ─── PUBLIC ROUTES ────────────────────────────────────────────────────────────

@app.route('/')
def index():
    mark_expired_donations()
    total_donations = Donation.query.filter_by(status='completed').count()
    total_donors = User.query.filter_by(role='donor', is_active=True).count()
    total_ngos = User.query.filter_by(role='ngo', is_active=True).count()
    available = Donation.query.filter_by(status='available').count()
    recent = Donation.query.filter_by(status='available').order_by(Donation.created_at.desc()).limit(4).all()
    return render_template('index.html',
        total_donations=total_donations,
        total_donors=total_donors,
        total_ngos=total_ngos,
        available=available,
        recent=recent,
        now=datetime.utcnow()
    )

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        role = request.form['role']
        org_name = request.form.get('org_name', '')
        address = request.form.get('address', '')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))

        user = User(
            name=name, email=email,
            password=generate_password_hash(password),
            phone=phone, role=role,
            org_name=org_name, address=address,
            is_verified=(role == 'donor')
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            if not user.is_active:
                flash('Your account has been suspended.', 'danger')
                return redirect(url_for('login'))
            session['user_id'] = user.id
            session['name'] = user.name
            session['role'] = user.role
            session['email'] = user.email
            flash(f'Welcome back, {user.name}!', 'success')
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'donor':
                return redirect(url_for('donor_dashboard'))
            else:
                return redirect(url_for('ngo_dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

# ─── DONOR ROUTES ─────────────────────────────────────────────────────────────

@app.route('/donor/dashboard')
@login_required
@role_required('donor')
def donor_dashboard():
    mark_expired_donations()
    user = User.query.get(session['user_id'])
    my_donations = Donation.query.filter_by(donor_id=user.id).order_by(Donation.created_at.desc()).all()
    pending_requests = FoodRequest.query.join(Donation).filter(
        Donation.donor_id == user.id,
        FoodRequest.status == 'pending'
    ).all()
    stats = {
        'total': len(my_donations),
        'available': sum(1 for d in my_donations if d.status == 'available'),
        'completed': sum(1 for d in my_donations if d.status == 'completed'),
        'pending_req': len(pending_requests)
    }
    return render_template('donor_dashboard.html', user=user, donations=my_donations,
                           pending_requests=pending_requests, stats=stats, now=datetime.utcnow())

@app.route('/donor/add-food', methods=['GET', 'POST'])
@login_required
@role_required('donor')
def add_food():
    if request.method == 'POST':
        expiry_str = request.form['expiry_time']
        cooked_str = request.form.get('cooked_at', '')
        try:
            expiry_dt = datetime.strptime(expiry_str, '%Y-%m-%dT%H:%M')
        except:
            flash('Invalid expiry date format.', 'danger')
            return redirect(url_for('add_food'))
        cooked_dt = None
        if cooked_str:
            try:
                cooked_dt = datetime.strptime(cooked_str, '%Y-%m-%dT%H:%M')
            except:
                pass

        donation = Donation(
            donor_id=session['user_id'],
            food_name=request.form['food_name'],
            quantity=request.form['quantity'],
            serves_people=int(request.form.get('serves_people') or 0),
            food_type=request.form['food_type'],
            cooked_at=cooked_dt,
            expiry_time=expiry_dt,
            pickup_address=request.form['pickup_address'],
            contact=request.form['contact'],
            instructions=request.form.get('instructions', '')
        )
        db.session.add(donation)
        db.session.commit()
        flash('Food listed successfully! NGOs can now view and request it.', 'success')
        return redirect(url_for('donor_dashboard'))
    return render_template('add_food.html')

@app.route('/donor/request/<int:req_id>/accept')
@login_required
@role_required('donor')
def accept_request(req_id):
    req = FoodRequest.query.get_or_404(req_id)
    if req.donation.donor_id != session['user_id']:
        flash('Access denied.', 'danger')
        return redirect(url_for('donor_dashboard'))
    req.status = 'accepted'
    req.donation.status = 'requested'
    req.updated_at = datetime.utcnow()
    # Reject all other pending requests for same donation
    others = FoodRequest.query.filter_by(donation_id=req.donation_id, status='pending').all()
    for o in others:
        if o.id != req_id:
            o.status = 'rejected'
    db.session.commit()
    flash('Request accepted! Please coordinate pickup with the NGO.', 'success')
    return redirect(url_for('donor_dashboard'))

@app.route('/donor/request/<int:req_id>/reject')
@login_required
@role_required('donor')
def reject_request(req_id):
    req = FoodRequest.query.get_or_404(req_id)
    if req.donation.donor_id != session['user_id']:
        flash('Access denied.', 'danger')
        return redirect(url_for('donor_dashboard'))
    req.status = 'rejected'
    req.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Request rejected.', 'info')
    return redirect(url_for('donor_dashboard'))

@app.route('/donor/donation/<int:don_id>/complete')
@login_required
@role_required('donor')
def complete_donation(don_id):
    don = Donation.query.get_or_404(don_id)
    if don.donor_id != session['user_id']:
        flash('Access denied.', 'danger')
        return redirect(url_for('donor_dashboard'))
    don.status = 'completed'
    accepted_req = FoodRequest.query.filter_by(donation_id=don_id, status='accepted').first()
    if accepted_req:
        accepted_req.status = 'completed'
    db.session.commit()
    flash('Donation marked as completed! Thank you for your generosity.', 'success')
    return redirect(url_for('donor_dashboard'))

@app.route('/donor/donation/<int:don_id>/delete')
@login_required
@role_required('donor')
def delete_donation(don_id):
    don = Donation.query.get_or_404(don_id)
    if don.donor_id != session['user_id']:
        flash('Access denied.', 'danger')
        return redirect(url_for('donor_dashboard'))
    FoodRequest.query.filter_by(donation_id=don_id).delete()
    db.session.delete(don)
    db.session.commit()
    flash('Donation removed.', 'info')
    return redirect(url_for('donor_dashboard'))

# ─── NGO ROUTES ───────────────────────────────────────────────────────────────

@app.route('/ngo/dashboard')
@login_required
@role_required('ngo')
def ngo_dashboard():
    mark_expired_donations()
    user = User.query.get(session['user_id'])
    my_requests = FoodRequest.query.filter_by(ngo_id=user.id).order_by(FoodRequest.requested_at.desc()).all()
    available = Donation.query.filter_by(status='available').order_by(Donation.expiry_time.asc()).all()
    # Filter out donations NGO already requested
    requested_ids = {r.donation_id for r in my_requests}
    available = [d for d in available if d.id not in requested_ids]
    stats = {
        'pending': sum(1 for r in my_requests if r.status == 'pending'),
        'accepted': sum(1 for r in my_requests if r.status == 'accepted'),
        'completed': sum(1 for r in my_requests if r.status == 'completed'),
        'available': len(available)
    }
    return render_template('ngo_dashboard.html', user=user, my_requests=my_requests,
                           available=available, stats=stats, now=datetime.utcnow())

@app.route('/ngo/request/<int:don_id>', methods=['POST'])
@login_required
@role_required('ngo')
def request_food(don_id):
    user = User.query.get(session['user_id'])
    if not user.is_verified:
        flash('Your NGO account is pending verification by admin.', 'warning')
        return redirect(url_for('ngo_dashboard'))
    don = Donation.query.get_or_404(don_id)
    existing = FoodRequest.query.filter_by(donation_id=don_id, ngo_id=user.id).first()
    if existing:
        flash('You have already requested this donation.', 'warning')
        return redirect(url_for('ngo_dashboard'))
    message = request.form.get('message', '')
    req = FoodRequest(donation_id=don_id, ngo_id=user.id, message=message)
    db.session.add(req)
    db.session.commit()
    flash('Request sent to donor! Wait for their response.', 'success')
    return redirect(url_for('ngo_dashboard'))

# ─── ADMIN ROUTES ─────────────────────────────────────────────────────────────

@app.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    mark_expired_donations()
    users = User.query.filter(User.role != 'admin').all()
    donations = Donation.query.order_by(Donation.created_at.desc()).all()
    requests = FoodRequest.query.order_by(FoodRequest.requested_at.desc()).all()
    pending_ngos = User.query.filter_by(role='ngo', is_verified=False, is_active=True).all()
    stats = {
        'donors': User.query.filter_by(role='donor').count(),
        'ngos': User.query.filter_by(role='ngo').count(),
        'verified_ngos': User.query.filter_by(role='ngo', is_verified=True).count(),
        'total_donations': Donation.query.count(),
        'available': Donation.query.filter_by(status='available').count(),
        'completed': Donation.query.filter_by(status='completed').count(),
        'total_requests': FoodRequest.query.count(),
    }
    return render_template('admin_dashboard.html',
        users=users, donations=donations, requests=requests,
        pending_ngos=pending_ngos, stats=stats, now=datetime.utcnow()
    )

@app.route('/admin/ngo/<int:user_id>/verify')
@login_required
@role_required('admin')
def verify_ngo(user_id):
    user = User.query.get_or_404(user_id)
    user.is_verified = True
    db.session.commit()
    flash(f'{user.name} has been verified.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/user/<int:user_id>/toggle')
@login_required
@role_required('admin')
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    status = 'activated' if user.is_active else 'suspended'
    flash(f'{user.name} has been {status}.', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/user/<int:user_id>/delete')
@login_required
@role_required('admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted.', 'info')
    return redirect(url_for('admin_dashboard'))

# ─── API ──────────────────────────────────────────────────────────────────────

@app.route('/api/donations')
def api_donations():
    mark_expired_donations()
    donations = Donation.query.filter_by(status='available').all()
    data = []
    for d in donations:
        data.append({
            'id': d.id,
            'food_name': d.food_name,
            'quantity': d.quantity,
            'serves_people': d.serves_people,
            'food_type': d.food_type,
            'pickup_address': d.pickup_address,
            'expiry_time': d.expiry_time.isoformat(),
            'donor_name': d.donor.org_name or d.donor.name
        })
    return jsonify(data)

# ─── INIT ─────────────────────────────────────────────────────────────────────

def create_tables():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(role='admin').first():
            admin = User(
                name='Admin',
                email='admin@foodconnector.org',
                password=generate_password_hash('admin123'),
                phone='9999999999',
                role='admin',
                is_verified=True
            )
            db.session.add(admin)
            db.session.commit()
            print('Admin created: admin@foodconnector.org / admin123')

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
