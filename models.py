from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ==================== USER MODEL ====================
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade='all, delete-orphan')
    habits = db.relationship('Habit', backref='user', lazy=True, cascade='all, delete-orphan')
    recipes = db.relationship('Recipe', backref='user', lazy=True, cascade='all, delete-orphan')
    meal_plans = db.relationship('MealPlan', backref='user', lazy=True, cascade='all, delete-orphan')
    study_cards = db.relationship('StudyCard', backref='user', lazy=True, cascade='all, delete-orphan')
    study_sessions = db.relationship('StudySession', backref='user', lazy=True, cascade='all, delete-orphan')
    inventory_items = db.relationship('InventoryItem', backref='user', lazy=True, cascade='all, delete-orphan')
    saved_events = db.relationship('Event', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

# ==================== FINANCE MODULE ====================
class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'income' or 'expense'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    transactions = db.relationship('Transaction', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Transaction {self.amount} {self.date}>'

# ==================== HABITS MODULE ====================
class Habit(db.Model):
    __tablename__ = 'habits'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#4CAF50')
    reminder_time = db.Column(db.Time)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    logs = db.relationship('HabitLog', backref='habit', lazy=True, cascade='all, delete-orphan')
    
    def get_current_streak(self):
        """Вычисляет текущую серию дней"""
        logs = sorted(self.logs, key=lambda x: x.date, reverse=True)
        if not logs or logs[0].date != datetime.utcnow().date():
            return 0
        
        streak = 0
        current_date = datetime.utcnow().date()
        for log in logs:
            if log.date == current_date:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        return streak
    
    def __repr__(self):
        return f'<Habit {self.name}>'

class HabitLog(db.Model):
    __tablename__ = 'habit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habits.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('habit_id', 'date', name='unique_habit_date'),)
    
    def __repr__(self):
        return f'<HabitLog {self.habit_id} {self.date}>'

# ==================== RECIPES MODULE ====================
class Recipe(db.Model):
    __tablename__ = 'recipes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    ingredients = db.Column(db.Text, nullable=False)  # JSON или текст
    instructions = db.Column(db.Text, nullable=False)
    prep_time = db.Column(db.Integer)  # в минутах
    cook_time = db.Column(db.Integer)  # в минутах
    servings = db.Column(db.Integer)
    category = db.Column(db.String(50))  # завтрак, обед, ужин, десерт и т.д.
    calories = db.Column(db.Float)
    image_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    meal_plans = db.relationship('MealPlan', backref='recipe', lazy=True)
    
    def __repr__(self):
        return f'<Recipe {self.title}>'

class MealPlan(db.Model):
    __tablename__ = 'meal_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    meal_type = db.Column(db.String(20))  # breakfast, lunch, dinner, snack
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MealPlan {self.date} {self.meal_type}>'

# ==================== STUDY MODULE ====================
class StudyCard(db.Model):
    __tablename__ = 'study_cards'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    front = db.Column(db.Text, nullable=False)
    back = db.Column(db.Text, nullable=False)
    topic = db.Column(db.String(100))
    difficulty = db.Column(db.Integer, default=0)  # 0-5, для интервальных повторений
    last_reviewed = db.Column(db.DateTime)
    next_review = db.Column(db.DateTime)
    review_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<StudyCard {self.id}>'

class StudySession(db.Model):
    __tablename__ = 'study_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_type = db.Column(db.String(20))  # 'pomodoro', 'review', 'study'
    duration = db.Column(db.Integer)  # в минутах
    cards_reviewed = db.Column(db.Integer, default=0)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<StudySession {self.session_type} {self.date}>'

# ==================== INVENTORY MODULE ====================
class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))  # электроника, мебель, одежда и т.д.
    room = db.Column(db.String(100))  # гостиная, спальня, кухня и т.д.
    purchase_price = db.Column(db.Float)
    purchase_date = db.Column(db.Date)
    warranty_expiry = db.Column(db.Date)
    serial_number = db.Column(db.String(100))
    image_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<InventoryItem {self.name}>'

# ==================== EVENTS MODULE ====================
class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # null для публичных событий
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # концерт, выставка, спорт и т.д.
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    price = db.Column(db.Float)
    price_type = db.Column(db.String(20))  # 'free', 'paid', 'donation'
    source_url = db.Column(db.String(500))
    is_saved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Event {self.title}>'

