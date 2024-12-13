from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
from flask import flash, redirect, url_for

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///yourdatabase.db'  # Use your actual DB URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)  # Set a secure, random secret key
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    budgets = db.relationship('Budget', backref='user', lazy=True)  # Add this line

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    time_frame = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    budget_id = db.Column(db.Integer, db.ForeignKey('budget.id'), nullable=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid login credentials', 400
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("You already have an account with this username. Please login.", "error")
            return redirect(url_for('login'))
        
        # Create a new user if the username is unique
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        session['user_id'] = new_user.id
        session['username'] = new_user.username
        flash("Account created successfully! You are now logged in.", "success")
        return redirect(url_for('dashboard'))
    
    return render_template('signup.html')
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    budgets = user.budgets
    return render_template('dashboard.html', user=user, budgets=budgets)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        new_username = request.form['username']
        new_password = request.form['password']
        if new_username:
            user.username = new_username
        if new_password:
            user.password = new_password
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('settings.html', user=user)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/new_budget', methods=['GET', 'POST'])
def new_budget():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        amount = request.form['amount']
        time_frame = request.form['time_frame']
        user = User.query.get(session['user_id'])
        
        new_budget = Budget(
            name=name,
            amount=amount,
            user_id=user.id,
            category=category,  # Adding category field
            time_frame=time_frame  # Adding time_frame field
        )
        db.session.add(new_budget)
        db.session.commit()
        return redirect(url_for('dashboard'))
    
    return render_template('new_budget.html')

@app.route('/budget_details/<int:budget_id>', methods=['GET', 'POST'])
def budget_details(budget_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    budget = Budget.query.get_or_404(budget_id)
    if request.method == 'POST':
        name = request.form['name']
        amount = request.form['amount']
        new_expense = Expense(name=name, amount=amount, budget_id=budget.id)
        db.session.add(new_expense)
        db.session.commit()
    expenses = Expense.query.filter_by(budget_id=budget.id).all()
    return render_template('budget_details.html', budget=budget, expenses=expenses)

@app.route('/delete_budget/<int:budget_id>')
def delete_budget(budget_id):
    budget = Budget.query.get_or_404(budget_id)
    if budget.user_id == session['user_id']:
        db.session.delete(budget)
        db.session.commit()
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    with app.app_context():  # Ensure the app context is pushed
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True)
