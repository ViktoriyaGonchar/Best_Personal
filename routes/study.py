from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, StudyCard, StudySession
from datetime import datetime, timedelta
import random

study_bp = Blueprint('study', __name__)

@study_bp.route('/')
@login_required
def index():
    """Главная страница модуля обучения"""
    cards = StudyCard.query.filter_by(user_id=current_user.id).all()
    
    # Статистика
    total_cards = len(cards)
    cards_due = len([c for c in cards if c.next_review and c.next_review <= datetime.now()])
    recent_sessions = StudySession.query.filter_by(user_id=current_user.id)\
        .order_by(StudySession.date.desc()).limit(5).all()
    
    return render_template('study/index.html',
                         total_cards=total_cards,
                         cards_due=cards_due,
                         recent_sessions=recent_sessions)

@study_bp.route('/cards')
@login_required
def cards():
    """Список всех карточек"""
    topic = request.args.get('topic', '')
    cards_query = StudyCard.query.filter_by(user_id=current_user.id)
    
    if topic:
        cards_query = cards_query.filter_by(topic=topic)
    
    cards = cards_query.order_by(StudyCard.created_at.desc()).all()
    
    # Получаем список всех тем
    topics = db.session.query(StudyCard.topic).filter_by(user_id=current_user.id)\
        .distinct().all()
    topics = [t[0] for t in topics if t[0]]
    
    return render_template('study/cards.html', cards=cards, topics=topics, selected_topic=topic)

@study_bp.route('/cards/add', methods=['GET', 'POST'])
@login_required
def add_card():
    """Добавление новой карточки"""
    if request.method == 'POST':
        front = request.form.get('front')
        back = request.form.get('back')
        topic = request.form.get('topic')
        
        if not front or not back:
            flash('Заполните обе стороны карточки', 'error')
            return render_template('study/add_card.html')
        
        card = StudyCard(
            user_id=current_user.id,
            front=front,
            back=back,
            topic=topic,
            next_review=datetime.now()
        )
        db.session.add(card)
        db.session.commit()
        
        flash('Карточка добавлена', 'success')
        return redirect(url_for('study.cards'))
    
    return render_template('study/add_card.html')

@study_bp.route('/cards/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_card(id):
    """Редактирование карточки"""
    card = StudyCard.query.get_or_404(id)
    
    if card.user_id != current_user.id:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('study.cards'))
    
    if request.method == 'POST':
        card.front = request.form.get('front')
        card.back = request.form.get('back')
        card.topic = request.form.get('topic')
        
        db.session.commit()
        flash('Карточка обновлена', 'success')
        return redirect(url_for('study.cards'))
    
    return render_template('study/edit_card.html', card=card)

@study_bp.route('/cards/delete/<int:id>')
@login_required
def delete_card(id):
    """Удаление карточки"""
    card = StudyCard.query.get_or_404(id)
    
    if card.user_id != current_user.id:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('study.cards'))
    
    db.session.delete(card)
    db.session.commit()
    flash('Карточка удалена', 'success')
    return redirect(url_for('study.cards'))

@study_bp.route('/review')
@login_required
def review():
    """Интервальное повторение карточек"""
    topic = request.args.get('topic', '')
    
    # Получаем карточки, которые нужно повторить
    now = datetime.now()
    cards_query = StudyCard.query.filter_by(user_id=current_user.id)\
        .filter((StudyCard.next_review <= now) | (StudyCard.next_review.is_(None)))
    
    if topic:
        cards_query = cards_query.filter_by(topic=topic)
    
    cards = cards_query.all()
    
    if not cards:
        flash('Нет карточек для повторения', 'info')
        return redirect(url_for('study.index'))
    
    # Выбираем случайную карточку
    card = random.choice(cards)
    
    return render_template('study/review.html', card=card, total_due=len(cards))

@study_bp.route('/review/<int:card_id>/answer', methods=['POST'])
@login_required
def answer_card(card_id):
    """Обработка ответа на карточку"""
    card = StudyCard.query.get_or_404(card_id)
    
    if card.user_id != current_user.id:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    quality = int(request.json.get('quality', 3))  # 0-5
    
    # Алгоритм интервальных повторений (упрощенная версия SM-2)
    if card.difficulty == 0:
        card.difficulty = 2.5
    else:
        card.difficulty = max(0, card.difficulty + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
    
    # Вычисляем интервал
    if quality < 3:
        interval = 1  # Повторить завтра
    else:
        if card.review_count == 0:
            interval = 1
        elif card.review_count == 1:
            interval = 6
        else:
            interval = int(card.difficulty * card.review_count)
    
    card.last_reviewed = datetime.now()
    card.next_review = datetime.now() + timedelta(days=interval)
    card.review_count += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'next_review': card.next_review.isoformat(),
        'difficulty': card.difficulty
    })

@study_bp.route('/pomodoro')
@login_required
def pomodoro():
    """Таймер Pomodoro"""
    return render_template('study/pomodoro.html')

@study_bp.route('/pomodoro/save', methods=['POST'])
@login_required
def save_pomodoro_session():
    """Сохранение сессии Pomodoro"""
    duration = int(request.json.get('duration', 25))
    session_type = request.json.get('type', 'pomodoro')
    
    session = StudySession(
        user_id=current_user.id,
        session_type=session_type,
        duration=duration
    )
    db.session.add(session)
    db.session.commit()
    
    return jsonify({'success': True})

@study_bp.route('/statistics')
@login_required
def statistics():
    """Статистика обучения"""
    cards = StudyCard.query.filter_by(user_id=current_user.id).all()
    sessions = StudySession.query.filter_by(user_id=current_user.id).all()
    
    # Статистика по карточкам
    total_cards = len(cards)
    cards_reviewed = len([c for c in cards if c.review_count > 0])
    cards_due = len([c for c in cards if c.next_review and c.next_review <= datetime.now()])
    
    # Статистика по сессиям
    total_study_time = sum(s.duration for s in sessions)
    pomodoro_sessions = len([s for s in sessions if s.session_type == 'pomodoro'])
    
    # Статистика по темам
    topics = {}
    for card in cards:
        topic = card.topic or 'Без темы'
        if topic not in topics:
            topics[topic] = {'total': 0, 'reviewed': 0}
        topics[topic]['total'] += 1
        if card.review_count > 0:
            topics[topic]['reviewed'] += 1
    
    return render_template('study/statistics.html',
                         total_cards=total_cards,
                         cards_reviewed=cards_reviewed,
                         cards_due=cards_due,
                         total_study_time=total_study_time,
                         pomodoro_sessions=pomodoro_sessions,
                         topics=topics)

