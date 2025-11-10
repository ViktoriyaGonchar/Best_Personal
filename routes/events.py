from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Event
from datetime import datetime, date, timedelta
import requests
from bs4 import BeautifulSoup

events_bp = Blueprint('events', __name__)

@events_bp.route('/')
@login_required
def index():
    """Главная страница поиска событий"""
    category = request.args.get('category', '')
    date_filter = request.args.get('date', '')
    
    events_query = Event.query.filter(
        (Event.user_id == current_user.id) | (Event.user_id.is_(None))
    )
    
    if category:
        events_query = events_query.filter_by(category=category)
    
    if date_filter == 'today':
        today = date.today()
        events_query = events_query.filter(
            db.func.date(Event.date) == today
        )
    elif date_filter == 'week':
        week_start = date.today()
        week_end = week_start + timedelta(days=7)
        events_query = events_query.filter(
            db.func.date(Event.date) >= week_start,
            db.func.date(Event.date) <= week_end
        )
    elif date_filter == 'month':
        month_start = date.today().replace(day=1)
        next_month = month_start + timedelta(days=32)
        month_end = next_month.replace(day=1) - timedelta(days=1)
        events_query = events_query.filter(
            db.func.date(Event.date) >= month_start,
            db.func.date(Event.date) <= month_end
        )
    
    events = events_query.order_by(Event.date).all()
    
    # Получаем уникальные категории
    categories = db.session.query(Event.category)\
        .filter(Event.category.isnot(None))\
        .distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('events/index.html',
                         events=events,
                         categories=categories,
                         selected_category=category,
                         selected_date=date_filter)

@events_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_event():
    """Добавление события вручную"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        event_date = request.form.get('date')
        event_time = request.form.get('time', '00:00')
        location = request.form.get('location')
        price = request.form.get('price')
        price_type = request.form.get('price_type', 'free')
        source_url = request.form.get('source_url')
        
        if not title or not event_date:
            flash('Заполните обязательные поля', 'error')
            return render_template('events/add_event.html')
        
        # Объединяем дату и время
        datetime_str = f"{event_date} {event_time}"
        event_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        
        event = Event(
            user_id=current_user.id,
            title=title,
            description=description,
            category=category,
            date=event_datetime,
            location=location,
            price=float(price) if price else None,
            price_type=price_type,
            source_url=source_url
        )
        db.session.add(event)
        db.session.commit()
        
        flash('Событие добавлено', 'success')
        return redirect(url_for('events.index'))
    
    return render_template('events/add_event.html')

@events_bp.route('/view/<int:id>')
@login_required
def view_event(id):
    """Просмотр события"""
    event = Event.query.get_or_404(id)
    return render_template('events/view_event.html', event=event)

@events_bp.route('/save/<int:id>')
@login_required
def save_event(id):
    """Сохранение события в избранное"""
    event = Event.query.get_or_404(id)
    
    if event.user_id is None:
        # Создаем копию для пользователя
        new_event = Event(
            user_id=current_user.id,
            title=event.title,
            description=event.description,
            category=event.category,
            date=event.date,
            location=event.location,
            price=event.price,
            price_type=event.price_type,
            source_url=event.source_url,
            is_saved=True
        )
        db.session.add(new_event)
    else:
        event.is_saved = True
    
    db.session.commit()
    flash('Событие сохранено в избранное', 'success')
    return redirect(url_for('events.view_event', id=id))

@events_bp.route('/saved')
@login_required
def saved_events():
    """Сохраненные события"""
    events = Event.query.filter_by(user_id=current_user.id, is_saved=True)\
        .order_by(Event.date).all()
    
    return render_template('events/saved.html', events=events)

@events_bp.route('/delete/<int:id>')
@login_required
def delete_event(id):
    """Удаление события"""
    event = Event.query.get_or_404(id)
    
    if event.user_id != current_user.id:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('events.index'))
    
    db.session.delete(event)
    db.session.commit()
    flash('Событие удалено', 'success')
    return redirect(url_for('events.index'))

@events_bp.route('/import')
@login_required
def import_events():
    """Импорт событий из внешних источников (заглушка)"""
    # В реальном приложении здесь будет парсинг различных источников
    flash('Функция импорта событий в разработке', 'info')
    return redirect(url_for('events.index'))

@events_bp.route('/map')
@login_required
def events_map():
    """Карта событий"""
    events = Event.query.filter(
        (Event.user_id == current_user.id) | (Event.user_id.is_(None)),
        Event.location.isnot(None)
    ).all()
    
    return render_template('events/map.html', events=events)

