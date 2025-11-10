from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, InventoryItem
from datetime import datetime, date, timedelta
from werkzeug.utils import secure_filename
import os

inventory_bp = Blueprint('inventory', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@inventory_bp.route('/')
@login_required
def index():
    """Главная страница учета имущества"""
    category = request.args.get('category', '')
    room = request.args.get('room', '')
    
    items_query = InventoryItem.query.filter_by(user_id=current_user.id)
    
    if category:
        items_query = items_query.filter_by(category=category)
    if room:
        items_query = items_query.filter_by(room=room)
    
    items = items_query.order_by(InventoryItem.created_at.desc()).all()
    
    # Статистика
    total_value = sum(item.purchase_price or 0 for item in items)
    total_items = len(items)
    
    # Получаем уникальные категории и комнаты
    categories = db.session.query(InventoryItem.category)\
        .filter_by(user_id=current_user.id)\
        .distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    rooms = db.session.query(InventoryItem.room)\
        .filter_by(user_id=current_user.id)\
        .distinct().all()
    rooms = [r[0] for r in rooms if r[0]]
    
    # Предупреждения о гарантии
    today = date.today()
    warranty_warnings = [item for item in items 
                        if item.warranty_expiry 
                        and item.warranty_expiry <= today + timedelta(days=30)]
    
    return render_template('inventory/index.html',
                         items=items,
                         total_value=total_value,
                         total_items=total_items,
                         categories=categories,
                         rooms=rooms,
                         selected_category=category,
                         selected_room=room,
                         warranty_warnings=warranty_warnings)

@inventory_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_item():
    """Добавление предмета"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        category = request.form.get('category')
        room = request.form.get('room')
        purchase_price = request.form.get('purchase_price')
        purchase_date = request.form.get('purchase_date')
        warranty_expiry = request.form.get('warranty_expiry')
        serial_number = request.form.get('serial_number')
        
        if not name:
            flash('Название предмета обязательно', 'error')
            return render_template('inventory/add_item.html')
        
        # Обработка изображения
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                upload_folder = os.path.join('uploads', 'inventory')
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                image_path = filepath
        
        item = InventoryItem(
            user_id=current_user.id,
            name=name,
            description=description,
            category=category,
            room=room,
            purchase_price=float(purchase_price) if purchase_price else None,
            purchase_date=datetime.strptime(purchase_date, '%Y-%m-%d').date() if purchase_date else None,
            warranty_expiry=datetime.strptime(warranty_expiry, '%Y-%m-%d').date() if warranty_expiry else None,
            serial_number=serial_number,
            image_path=image_path
        )
        db.session.add(item)
        db.session.commit()
        
        flash('Предмет добавлен', 'success')
        return redirect(url_for('inventory.index'))
    
    return render_template('inventory/add_item.html')

@inventory_bp.route('/view/<int:id>')
@login_required
def view_item(id):
    """Просмотр предмета"""
    item = InventoryItem.query.get_or_404(id)
    
    if item.user_id != current_user.id:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('inventory.index'))
    
    return render_template('inventory/view_item.html', item=item)

@inventory_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_item(id):
    """Редактирование предмета"""
    item = InventoryItem.query.get_or_404(id)
    
    if item.user_id != current_user.id:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('inventory.index'))
    
    if request.method == 'POST':
        item.name = request.form.get('name')
        item.description = request.form.get('description')
        item.category = request.form.get('category')
        item.room = request.form.get('room')
        item.purchase_price = float(request.form.get('purchase_price')) if request.form.get('purchase_price') else None
        purchase_date = request.form.get('purchase_date')
        item.purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d').date() if purchase_date else None
        warranty_expiry = request.form.get('warranty_expiry')
        item.warranty_expiry = datetime.strptime(warranty_expiry, '%Y-%m-%d').date() if warranty_expiry else None
        item.serial_number = request.form.get('serial_number')
        
        # Обработка нового изображения
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                # Удаляем старое изображение
                if item.image_path and os.path.exists(item.image_path):
                    os.remove(item.image_path)
                
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                upload_folder = os.path.join('uploads', 'inventory')
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                item.image_path = filepath
        
        db.session.commit()
        flash('Предмет обновлен', 'success')
        return redirect(url_for('inventory.view_item', id=item.id))
    
    return render_template('inventory/edit_item.html', item=item)

@inventory_bp.route('/delete/<int:id>')
@login_required
def delete_item(id):
    """Удаление предмета"""
    item = InventoryItem.query.get_or_404(id)
    
    if item.user_id != current_user.id:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('inventory.index'))
    
    # Удаляем изображение
    if item.image_path and os.path.exists(item.image_path):
        os.remove(item.image_path)
    
    db.session.delete(item)
    db.session.commit()
    flash('Предмет удален', 'success')
    return redirect(url_for('inventory.index'))

@inventory_bp.route('/search')
@login_required
def search():
    """Поиск по имуществу"""
    query = request.args.get('q', '')
    
    if not query:
        return redirect(url_for('inventory.index'))
    
    items = InventoryItem.query.filter_by(user_id=current_user.id)\
        .filter(
            InventoryItem.name.contains(query) |
            InventoryItem.description.contains(query) |
            InventoryItem.serial_number.contains(query)
        ).all()
    
    return render_template('inventory/search.html', items=items, query=query)

@inventory_bp.route('/warranty')
@login_required
def warranty():
    """Список предметов с гарантией"""
    today = date.today()
    days_ahead = int(request.args.get('days', 30))
    
    items = InventoryItem.query.filter_by(user_id=current_user.id)\
        .filter(InventoryItem.warranty_expiry.isnot(None))\
        .filter(InventoryItem.warranty_expiry <= today + timedelta(days=days_ahead))\
        .order_by(InventoryItem.warranty_expiry).all()
    
    # Вычисляем дни до истечения для каждого предмета
    items_with_days = []
    for item in items:
        days_left = (item.warranty_expiry - today).days
        items_with_days.append((item, days_left))
    
    return render_template('inventory/warranty.html', items_with_days=items_with_days, days_ahead=days_ahead, today=today)

@inventory_bp.route('/statistics')
@login_required
def statistics():
    """Статистика по имуществу"""
    items = InventoryItem.query.filter_by(user_id=current_user.id).all()
    
    # Статистика по категориям
    category_stats = {}
    for item in items:
        category = item.category or 'Без категории'
        if category not in category_stats:
            category_stats[category] = {'count': 0, 'value': 0}
        category_stats[category]['count'] += 1
        category_stats[category]['value'] += item.purchase_price or 0
    
    # Статистика по комнатам
    room_stats = {}
    for item in items:
        room = item.room or 'Не указано'
        if room not in room_stats:
            room_stats[room] = {'count': 0, 'value': 0}
        room_stats[room]['count'] += 1
        room_stats[room]['value'] += item.purchase_price or 0
    
    total_value = sum(item.purchase_price or 0 for item in items)
    
    return render_template('inventory/statistics.html',
                         category_stats=category_stats,
                         room_stats=room_stats,
                         total_value=total_value,
                         total_items=len(items))

