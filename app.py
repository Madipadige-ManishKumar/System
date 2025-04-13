import logging
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from flask_login import LoginManager, login_user, current_user, login_required, UserMixin
from math import ceil
import random
import requests

# Function to fetch solved problems from the new API
def get_leetcode_solved_problems():
    url = "https://leetcode-api-faisalshohag.vercel.app/oomanish459"  # URL with JSON data

    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        
        # Print total solved problems
        return str(data['totalSolved'])
                

# Create the Flask app instance
app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # SQLite Database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'pVO5gnZLnRhQIM2opVO5gnZLnRhQIM2o'

# Initialize the database
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login" 

# Model for user (tracking IQ, strength, speed, consistency)
class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer)
    IQ = db.Column(db.Integer, default=0)
    strength = db.Column(db.Integer, default=0)
    speed = db.Column(db.Integer, default=0)
    consistency = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=0)

# Model for tasks
class Quest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer)
    quest_name = db.Column(db.String(100), nullable=False)
    frequency = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    done = db.Column(db.Integer, default=0)  # 0 = not done, 1 = done

# Model for statistics (keeping track of completed and not completed tasks for each category)
class Statistics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer)
    category = db.Column(db.String(50), nullable=False)
    total_tasks = db.Column(db.Integer, default=0)
    done_tasks = db.Column(db.Integer, default=0)
    not_done_tasks = db.Column(db.Integer, default=0)
    mean = db.Column(db.Integer, default=0)
    date = db.Column(db.String(50), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
# Route for home page
@app.route('/signup')
def signup_page():
    return render_template('signup.html',val="")
@app.route("/signupauth", methods=['GET', 'POST'])
def signup():
    val=random_number = random.randint(1000000000, 9999999999)
    new_user=User(id=random_number,uid=random_number, IQ=0, strength=0, speed=0, consistency=0)
    db.session.add(new_user)
    db.session.commit()
    return render_template('signup.html',val=val)

@app.route('/')
def index():
    create_tables()
    return render_template('login.html')

@app.route('/loginauth', methods=['GET', 'POST'])
def login():
    uid=None
    if request.method == 'POST':
        print("the if")
        uid = request.form.get('myuid')  # For GET method, use request.args.get()# Debugging line
        print(uid)
        if uid:
            user = User.query.filter_by(uid=uid).first()
            if user:
                print(user.id,"is the user id ")
                login_user(user)
                return redirect(url_for('home'))
            else:   
                return "User not found"  # If user doesn't exist, return this message
    print("here i am ")
    return "UID is required!"  # If no UID is provided, return this message

@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    # Fetch user details
    user=User.query.filter_by(uid=current_user.uid).first()

    categories = ['IQ', 'strength', 'speed', 'consistency']
    stats = {}
    for category in categories:
        stat = Statistics.query.filter_by(category=category).order_by(Statistics.date.desc()).first()
        stats[category] = stat if stat else None

    if request.method == 'POST':
        # Update user stats
        user.IQ = request.form['IQ']
        user.strength = request.form['strength']
        user.speed = request.form['speed']
        user.consistency = request.form['consistency']
        db.session.commit()
    return render_template('home.html', stats=stats, user=user)

# Route for quest page (listing all tasks)
@app.route('/quest', methods=['GET', 'POST'])
def quest():
    tasks = Quest.query.filter_by(uid=current_user.uid).all()
    return render_template('quest.html', tasks=tasks)

# Route for adding tasks
@app.route('/add_task', methods=['GET', 'POST'])
def add_task():
    if request.method == 'POST':
        quest_name = request.form['task_name']
        frequency = request.form['frequency']
        category = request.form['category']
        if quest_name.lower() == "leetcode":
            quest_name=quest_name+' '+str(get_leetcode_solved_problems())
            print("the new quest name is ",quest_name)
        print(f"Received task: {quest_name}, Frequency: {frequency}, Category: {category}")  # Debugging line

        new_task = Quest(uid=current_user.uid,quest_name=quest_name, frequency=frequency, category=category)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('quest'))
    return render_template('add_task.html')

# Route for deleting tasks
@app.route('/delete_quest/<int:id>', methods=['GET', 'POST'])
def delete_task(id):
    task = Quest.query.get(id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('quest'))
@app.route('/update_quest/<int:id>', methods=['POST', 'GET'])
def update_quest(id):
    quest = Quest.query.get_or_404(id)
    if  "leetcode" in  quest.quest_name.lower():
        print(str(quest.quest_name))
        number  = quest.quest_name.split(' ')[1]
        if int(number) < int(get_leetcode_solved_problems()):
            quest.done = 1
        else:
            quest.done = 0
    else:
        if quest.done==1:
            quest.done = 0
        else:
            quest.done = 1
    db.session.commit()
    return redirect(url_for('quest'))

# Route to calculate statistics and update the task completion mean

def calculate_statistics():
    categories = ['IQ', 'strength', 'speed', 'consistency']
    today = datetime.now().strftime("%Y-%m-%d")
    users=User.query.filter_by().all()
    for category in categories:

        # Calculate the done and not done tasks for this category
        done_tasks = Quest.query.filter_by(category=category, done=1).count()
        not_done_tasks = Quest.query.filter_by(category=category, done=0).count()
        print(done_tasks,not_done_tasks,"is the done and not done tasks")
        # Calculate the total tasks (done + not done)
        total_tasks = done_tasks + not_done_tasks

        print(total_tasks,"is the total tasks")
        # Calculate the mean (percentage of tasks done), and round up to nearest integer using ceil
        if total_tasks > 0:
            mean_percentage = done_tasks / total_tasks
        else:
            mean_percentage = 0
        mean_percentage_ceil = ceil(mean_percentage)

        # Update the statistics table
        stat = Statistics.query.filter_by(category=category, date=today).first()
        db.session.commit()
        if not stat:
            # If no record exists for today, create a new record
            stat = Statistics(category=category, date=today, total_tasks=total_tasks, done_tasks=done_tasks, not_done_tasks=not_done_tasks, mean=mean_percentage_ceil)
            db.session.add(stat)
        else:
            # Update the statistics with the new calculated values
            stat.done_tasks += done_tasks
            stat.not_done_tasks += not_done_tasks
            stat.total_tasks += total_tasks
            stat.mean = mean_percentage_ceil
        print(stat.mean,"is the mean")
        for user in users:
            if category == 'IQ':
                user.IQ += stat.mean
            elif category == 'strength':
                user.strength += stat.mean
            elif category == 'speed':
                user.speed += stat.mean

            db.session.commit()

# After all categories are updated, calculate consistency:
        for user in users:
            user.consistency += (user.IQ + user.strength + user.speed) // 3
            user.level= (user.IQ + user.strength + user.speed+user.consistency) // 4
        db.session.commit()

    

# Function to reset task completion at midnight
def reset_tasks():
    print("Resetting tasks...")
    with app.app_context():
        # try:
           
            # Recalculate statistics after resetting tasks
            calculate_statistics()
            quests = Quest.query.all()
            for quest in quests:
                quest.done = 0  # Reset all tasks to not done
            db.session.commit()

        

# Set up APScheduler to run the task reset at midnight
scheduler = BackgroundScheduler()
scheduler.add_job(func=reset_tasks, trigger="cron", hour=1, minute=19)  # Runs at midnight every day
scheduler.start()
print("Scheduler started.")

# Initialize the database and create tables on first request
def create_tables():
    db.create_all()

# Run the Flask application
if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)
