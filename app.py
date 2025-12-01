from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import bcrypt
from sqlalchemy import exc

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Set up the database (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vote_system.db'  # This creates a local SQLite database file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disables a feature we don't need

# Initialize the database and migrate objects
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Database Models

# User Model for registration/login
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    has_voted = db.Column(db.Boolean, default=False)  # Add this field


# Candidate Model
class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    votes = db.Column(db.Integer, default=0, nullable=False)

class VotingTime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voting_start_time = db.Column(db.DateTime, nullable=False)
    voting_end_time = db.Column(db.DateTime, nullable=False)

class VotingSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)  # Track if the session is active

# Admin credentials (in production, use hashed passwords)
admin_credentials = {
    "username": "admin",
    "password": "adminpassword"
}

# User Registration & Login Routes
@app.route('/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Hash the password using bcrypt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Check if the username already exists
        if User.query.filter_by(username=username).first():
            return "Username already exists", 400
        
        # Create new user in the database
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if user exists and verify password
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash):
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('vote'))
        else:
            return "Login Failed", 403

    return render_template('login.html')


@app.route('/vote', methods=['GET', 'POST'])
def vote():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    candidates = Candidate.query.all()
    user = User.query.filter_by(username=session['username']).first()
    voting_time = VotingTime.query.first()

    # Check if voting time is set and if we're within the voting period
    can_vote = False
    remaining_seconds = 0
    time_status = ""
    show_results = False

    if voting_time:
        current_time = datetime.now()
        voting_start_time = voting_time.voting_start_time
        voting_end_time = voting_time.voting_end_time
        
        # Check if voting has started
        if current_time < voting_start_time:
            time_until_start = voting_start_time - current_time
            remaining_seconds = max(0, time_until_start.total_seconds())
            time_status = "not_started"
        elif current_time <= voting_end_time:
            time_until_end = voting_end_time - current_time
            remaining_seconds = max(0, time_until_end.total_seconds())
            time_status = "active"
            can_vote = True
        else:
            time_status = "ended"
            remaining_seconds = 0
            show_results = True  # Show results when voting has ended
    else:
        time_status = "not_set"
    
    # Calculate results for display
    results = {candidate.name: candidate.votes for candidate in candidates}
    total_votes = sum(results.values())
    
    # If user has already voted, they can view but not vote again
    if user.has_voted:
        can_vote = False

    if request.method == 'POST' and can_vote:
        candidate_name = request.form['candidate']
        candidate = Candidate.query.filter_by(name=candidate_name).first()
        if candidate:
            candidate.votes += 1
            db.session.commit()

            user.has_voted = True
            db.session.commit()

            return redirect(url_for('vote_success'))

    return render_template('vote.html', 
                         candidates=candidates, 
                         remaining_seconds=remaining_seconds,
                         time_status=time_status,
                         can_vote=can_vote,
                         voting_time=voting_time,
                         user_has_voted=user.has_voted,
                         show_results=show_results,
                         results=results,
                         total_votes=total_votes)
    
    


@app.route('/vote_success')
def vote_success():
    # Get voting results to display
    candidates = Candidate.query.all()
    results = {candidate.name: candidate.votes for candidate in candidates}
    total_votes = sum(results.values())
    
    # Calculate the winner
    winner = None
    if results:
        max_votes = max(results.values())
        winners = [name for name, votes in results.items() if votes == max_votes]
        if len(winners) == 1:
            winner = winners[0]
        else:
            winner = "Tie between " + ", ".join(winners)
    
    # Check voting time status
    voting_time = VotingTime.query.first()
    time_status = ""
    remaining_seconds = 0
    show_results = False
    
    if voting_time:
        current_time = datetime.now()
        voting_start_time = voting_time.voting_start_time
        voting_end_time = voting_time.voting_end_time
        
        # Check if voting has started
        if current_time < voting_start_time:
            time_until_start = voting_start_time - current_time
            remaining_seconds = max(0, time_until_start.total_seconds())
            time_status = "not_started"
        elif current_time <= voting_end_time:
            time_until_end = voting_end_time - current_time
            remaining_seconds = max(0, time_until_end.total_seconds())
            time_status = "active"
        else:
            time_status = "ended"
            show_results = True
    else:
        time_status = "not_set"
    
    return render_template('voting_success.html', 
                         show_results=show_results,
                         results=results,
                         total_votes=total_votes,
                         winner=winner,
                         time_status=time_status,
                         remaining_seconds=remaining_seconds,
                         voting_time=voting_time)

# Admin Routes for Login and Dashboard
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Verify admin credentials
        if username == admin_credentials['username'] and password == admin_credentials['password']:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return "Invalid credentials", 403
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

     # Fetch all users, candidates, and voting time
    users = User.query.all()
    candidates = Candidate.query.all()
    voting_time = VotingTime.query.first()
    
    # Calculate results
    results = {candidate.name: candidate.votes for candidate in candidates}
    total_votes = sum(results.values())

    if request.method == 'POST':
        new_candidate_name = request.form['candidate_name']
        
        # Check if candidate already exists
        if Candidate.query.filter_by(name=new_candidate_name).first():
            flash("Candidate already exists", 'error')
            return redirect(url_for('admin_dashboard'))
        
        # Add new candidate to the database
        new_candidate = Candidate(name=new_candidate_name)
        db.session.add(new_candidate)
        db.session.commit()
        flash(f"Candidate '{new_candidate_name}' added successfully", 'success')

    return render_template('admin_dashboard.html', 
                         users=users, 
                         candidates=candidates, 
                         results=results, 
                         total_votes=total_votes,
                         voting_time=voting_time)

@app.route('/admin/add_candidate', methods=['POST'])
def add_candidate():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    candidate_name = request.form['candidate_name']
    
    # Check if candidate already exists
    if Candidate.query.filter_by(name=candidate_name).first():
        return "Candidate already exists", 400
    
    # Add new candidate to the database
    new_candidate = Candidate(name=candidate_name)
    db.session.add(new_candidate)
    db.session.commit()
    
    return redirect(url_for('admin_dashboard'))

# Edit candidate
@app.route('/admin/edit_candidate/<int:candidate_id>', methods=['POST'])
def edit_candidate(candidate_id):
    if 'admin_logged_in' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    data = request.get_json()
    new_name = data.get('name', '').strip()
    
    if not new_name:
        return jsonify({'success': False, 'message': 'Candidate name cannot be empty'})
    
    candidate = Candidate.query.get_or_404(candidate_id)
    
    # Check if another candidate already has this name
    existing = Candidate.query.filter_by(name=new_name).first()
    if existing and existing.id != candidate_id:
        return jsonify({'success': False, 'message': 'Another candidate already has this name'})
    
    candidate.name = new_name
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Candidate updated successfully'})

# Delete candidate
@app.route('/admin/delete_candidate/<int:candidate_id>', methods=['POST'])
def delete_candidate(candidate_id):
    if 'admin_logged_in' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    candidate = Candidate.query.get_or_404(candidate_id)
    db.session.delete(candidate)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Candidate deleted successfully'})

# Reset user vote status
@app.route('/admin/reset_user_vote/<int:user_id>', methods=['POST'])
def reset_user_vote(user_id):
    if 'admin_logged_in' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    user = User.query.get_or_404(user_id)
    user.has_voted = False
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'User vote status reset'})

# Delete user
@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'admin_logged_in' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'User deleted successfully'})

# Start voting immediately
@app.route('/admin/start_voting', methods=['POST'])
def start_voting():
    if 'admin_logged_in' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    voting_time = VotingTime.query.first()
    if not voting_time:
        voting_time = VotingTime(
            voting_start_time=datetime.now(),
            voting_end_time=datetime.now() + timedelta(hours=24)  # Default 24 hours
        )
        db.session.add(voting_time)
    else:
        voting_time.voting_start_time = datetime.now()
        # Set end time to 24 hours from now if it's in the past
        if voting_time.voting_end_time < datetime.now():
            voting_time.voting_end_time = datetime.now() + timedelta(hours=24)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Voting started successfully'})

# End voting immediately
@app.route('/admin/end_voting', methods=['POST'])
def end_voting():
    if 'admin_logged_in' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    voting_time = VotingTime.query.first()
    if voting_time:
        voting_time.voting_end_time = datetime.now()
        db.session.commit()
    
    return jsonify({'success': True, 'message': 'Voting ended successfully'})

# Reset all votes
@app.route('/admin/reset_all_votes', methods=['POST'])
def reset_all_votes():
    if 'admin_logged_in' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    # Reset all candidate votes
    candidates = Candidate.query.all()
    for candidate in candidates:
        candidate.votes = 0
    
    # Reset all user voting status
    users = User.query.all()
    for user in users:
        user.has_voted = False
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'All votes reset successfully'})

@app.route('/admin/set_voting_time', methods=['POST'])
def set_voting_time():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    start_time = request.form['start_time']
    end_time = request.form['end_time']
    
    # Convert to datetime objects
    start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M")
    end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M")

    # Store the times in the database
    voting_time = VotingTime.query.first()
    if not voting_time:
        voting_time = VotingTime(voting_start_time=start_time, voting_end_time=end_time)
        db.session.add(voting_time)
    else:
        voting_time.voting_start_time = start_time
        voting_time.voting_end_time = end_time

    db.session.commit()
    flash(f"Voting times set: Start - {start_time}, End - {end_time}", 'success')

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

# User Logout Route
@app.route('/logout')
def user_logout():
    session.pop('logged_in', None)
    return redirect(url_for('register'))

# Initialize the database tables on the first request (using `before_request` for every request)
@app.before_request
def setup():
    # Ensure the database tables are created on the first request if not already created
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
