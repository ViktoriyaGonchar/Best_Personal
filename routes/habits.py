from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Habit, HabitLog
from datetime import datetime, date, timedelta

habits_bp = Blueprint('habits', __name__)

@habits_bp.route('/')
@login_required
def index():
    """Главная страница трекера привычек"""
    habits = Habit.query.filter_by(user_id=current_user.id).all()
    
    # Добавляем информацию о текущей серии для каждой привычки
    for habit in habits:
        habit.current_streak = habit.get_current_streak()
        habit.total_logs = len(habit.logs)
    
    return render_template('habits/index.html', habits=habits)

@habits_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_habit():
    """Добавление новой привычки"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        color = request.form.get('color', '#4CAF50')
        reminder_time = request.form.get('reminder_time')
        
        if not name:
            flash('Название привычки обязательно', 'error')
            return render_template('habits/add_habit.html')
        
        habit = Habit(
            user_id=current_user.id,
            name=name,
            description=description,
            color=color,
            reminder_time=datetime.strptime(reminder_time, '%H:%M').time() if reminder_time else None
        )
        db.session.add(habit)
        db.session.commit()
        
        flash('Привычка добавлена', 'success')
        return redirect(url_for('habits.index'))
    
    return render_template('habits/add_habit.html')

@habits_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_habit(id):
    """Редактирование привычки"""
    habit = Habit.query.get_or_404(id)
    
    if habit.user_id != current_user.id:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('habits.index'))
    
    if request.method == 'POST':
        habit.name = request.form.get('name')
        habit.description = request.form.get('description')
        habit.color = request.form.get('color', '#4CAF50')
        reminder_time = request.form.get('reminder_time')
        habit.reminder_time = datetime.strptime(reminder_time, '%H:%M').time() if reminder_time else None
        
        db.session.commit()
        flash('Привычка обновлена', 'success')
        return redirect(url_for('habits.index'))
    
    return render_template('habits/edit_habit.html', habit=habit)

@habits_bp.route('/delete/<int:id>')
@login_required
def delete_habit(id):
    """Удаление привычки"""
    habit = Habit.query.get_or_404(id)
    
    if habit.user_id != current_user.id:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('habits.index'))
    
    db.session.delete(habit)
    db.session.commit()
    flash('Привычка удалена', 'success')
    return redirect(url_for('habits.index'))

@habits_bp.route('/log/<int:habit_id>', methods=['POST'])
@login_required
def log_habit(habit_id):
    """Отметка выполнения привычки"""
    habit = Habit.query.get_or_404(habit_id)
    
    if habit.user_id != current_user.id:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    log_date = request.json.get('date', date.today().isoformat())
    log_date = datetime.strptime(log_date, '%Y-%m-%d').date()
    
    # Проверяем, не существует ли уже запись на эту дату
    existing_log = HabitLog.query.filter_by(habit_id=habit_id, date=log_date).first()
    
    if existing_log:
        db.session.delete(existing_log)
        db.session.commit()
        return jsonify({'status': 'removed', 'streak': habit.get_current_streak()})
    else:
        log = HabitLog(habit_id=habit_id, date=log_date)
        db.session.add(log)
        db.session.commit()
        return jsonify({'status': 'added', 'streak': habit.get_current_streak()})

@habits_bp.route('/view/<int:id>')
@login_required
def view_habit(id):
    """Просмотр детальной информации о привычке"""
    habit = Habit.query.get_or_404(id)
    
    if habit.user_id != current_user.id:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('habits.index'))
    
    # Получаем логи за последние 30 дней
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    logs = HabitLog.query.filter_by(habit_id=habit.id)\
        .filter(HabitLog.date >= start_date)\
        .order_by(HabitLog.date.desc()).all()
    
    # Статистика
    current_streak = habit.get_current_streak()
    total_days = len(habit.logs)
    completion_rate = (total_days / 30) * 100 if total_days > 0 else 0
    
    # Данные для календаря
    log_dates = {log.date.isoformat() for log in logs}
    
    return render_template('habits/view_habit.html',
                         habit=habit,
                         logs=logs,
                         current_streak=current_streak,
                         total_days=total_days,
                         completion_rate=completion_rate,
                         log_dates=log_dates)

@habits_bp.route('/statistics')
@login_required
def statistics():
    """Общая статистика по всем привычкам"""
    habits = Habit.query.filter_by(user_id=current_user.id).all()
    
    stats = []
    for habit in habits:
        stats.append({
            'name': habit.name,
            'current_streak': habit.get_current_streak(),
            'total_logs': len(habit.logs),
            'color': habit.color
        })
    
    return render_template('habits/statistics.html', stats=stats)

