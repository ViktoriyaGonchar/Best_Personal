from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from models import db, Transaction, Category
from datetime import datetime, timedelta
from sqlalchemy import func, extract
import pandas as pd
import io
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

finance_bp = Blueprint('finance', __name__)

@finance_bp.route('/')
@login_required
def index():
    """Главная страница финансового модуля"""
    # Получаем последние транзакции
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(Transaction.date.desc()).limit(10).all()
    
    # Статистика за текущий месяц
    today = datetime.now().date()
    month_start = today.replace(day=1)
    
    income = db.session.query(func.sum(Transaction.amount))\
        .join(Category)\
        .filter(Transaction.user_id == current_user.id,
                Transaction.date >= month_start,
                Category.type == 'income').scalar() or 0
    
    expenses = db.session.query(func.sum(Transaction.amount))\
        .join(Category)\
        .filter(Transaction.user_id == current_user.id,
                Transaction.date >= month_start,
                Category.type == 'expense').scalar() or 0
    
    balance = income - expenses
    
    return render_template('finance/index.html', 
                         transactions=transactions,
                         income=income,
                         expenses=expenses,
                         balance=balance)

@finance_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    """Добавление транзакции"""
    if request.method == 'POST':
        category_id = request.form.get('category_id')
        amount = float(request.form.get('amount'))
        description = request.form.get('description')
        date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        
        transaction = Transaction(
            user_id=current_user.id,
            category_id=category_id,
            amount=amount,
            description=description,
            date=date
        )
        db.session.add(transaction)
        db.session.commit()
        
        flash('Транзакция добавлена', 'success')
        return redirect(url_for('finance.index'))
    
    categories = Category.query.all()
    return render_template('finance/add_transaction.html', categories=categories)

@finance_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(id):
    """Редактирование транзакции"""
    transaction = Transaction.query.get_or_404(id)
    
    if transaction.user_id != current_user.id:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('finance.index'))
    
    if request.method == 'POST':
        transaction.category_id = request.form.get('category_id')
        transaction.amount = float(request.form.get('amount'))
        transaction.description = request.form.get('description')
        transaction.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        
        db.session.commit()
        flash('Транзакция обновлена', 'success')
        return redirect(url_for('finance.index'))
    
    categories = Category.query.all()
    return render_template('finance/edit_transaction.html', 
                         transaction=transaction, 
                         categories=categories)

@finance_bp.route('/delete/<int:id>')
@login_required
def delete_transaction(id):
    """Удаление транзакции"""
    transaction = Transaction.query.get_or_404(id)
    
    if transaction.user_id != current_user.id:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('finance.index'))
    
    db.session.delete(transaction)
    db.session.commit()
    flash('Транзакция удалена', 'success')
    return redirect(url_for('finance.index'))

@finance_bp.route('/statistics')
@login_required
def statistics():
    """Статистика по периодам"""
    period = request.args.get('period', 'month')
    
    today = datetime.now().date()
    
    if period == 'week':
        start_date = today - timedelta(days=7)
    elif period == 'month':
        start_date = today.replace(day=1)
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
    else:
        start_date = today.replace(day=1)
    
    # Транзакции за период
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .filter(Transaction.date >= start_date).all()
    
    # Статистика по категориям
    category_stats = db.session.query(
        Category.name,
        Category.type,
        func.sum(Transaction.amount).label('total')
    ).join(Transaction)\
     .filter(Transaction.user_id == current_user.id,
             Transaction.date >= start_date)\
     .group_by(Category.id, Category.name, Category.type).all()
    
    # Данные для графика
    chart_data = {
        'labels': [cat[0] for cat in category_stats],
        'data': [float(cat[2]) for cat in category_stats],
        'types': [cat[1] for cat in category_stats]
    }
    
    return render_template('finance/statistics.html',
                         period=period,
                         category_stats=category_stats,
                         chart_data=chart_data)

@finance_bp.route('/export/excel')
@login_required
def export_excel():
    """Экспорт данных в Excel"""
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(Transaction.date.desc()).all()
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Транзакции"
    
    # Заголовки
    ws.append(['Дата', 'Категория', 'Тип', 'Сумма', 'Описание'])
    
    # Данные
    for t in transactions:
        ws.append([
            t.date.strftime('%Y-%m-%d'),
            t.category.name,
            'Доход' if t.category.type == 'income' else 'Расход',
            t.amount,
            t.description or ''
        ])
    
    # Сохранение в память
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(output, 
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name=f'finance_export_{datetime.now().strftime("%Y%m%d")}.xlsx')

@finance_bp.route('/export/pdf')
@login_required
def export_pdf():
    """Экспорт данных в PDF"""
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(Transaction.date.desc()).limit(50).all()
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Заголовок
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "Отчет по финансам")
    p.setFont("Helvetica", 10)
    p.drawString(50, height - 70, f"Пользователь: {current_user.username}")
    p.drawString(50, height - 85, f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Таблица
    y = height - 120
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y, "Дата")
    p.drawString(150, y, "Категория")
    p.drawString(300, y, "Сумма")
    p.drawString(400, y, "Описание")
    
    y -= 20
    p.setFont("Helvetica", 9)
    for t in transactions:
        if y < 50:
            p.showPage()
            y = height - 50
        
        p.drawString(50, y, t.date.strftime('%Y-%m-%d'))
        p.drawString(150, y, t.category.name[:20])
        p.drawString(300, y, f"{t.amount:.2f}")
        p.drawString(400, y, (t.description or '')[:30])
        y -= 15
    
    p.save()
    buffer.seek(0)
    
    return send_file(buffer,
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=f'finance_report_{datetime.now().strftime("%Y%m%d")}.pdf')

