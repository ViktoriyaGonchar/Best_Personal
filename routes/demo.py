from flask import Blueprint, render_template

demo_bp = Blueprint('demo', __name__)

@demo_bp.route('/demo')
def demo():
    """Демонстрационная страница с примерами всех модулей"""
    
    # Демо-данные для финансов
    demo_finance = {
        'income': 50000.00,
        'expenses': 35000.00,
        'balance': 15000.00,
        'transactions': [
            {'date': '2024-11-10', 'category': 'Зарплата', 'type': 'income', 'amount': 50000, 'description': 'Оклад'},
            {'date': '2024-11-08', 'category': 'Еда', 'type': 'expense', 'amount': 2500, 'description': 'Продукты'},
            {'date': '2024-11-05', 'category': 'Транспорт', 'type': 'expense', 'amount': 1500, 'description': 'Проездной'},
            {'date': '2024-11-03', 'category': 'Развлечения', 'type': 'expense', 'amount': 3000, 'description': 'Кино'},
        ]
    }
    
    # Демо-данные для привычек
    demo_habits = [
        {'name': 'Утренняя зарядка', 'color': '#4CAF50', 'streak': 12, 'total': 25},
        {'name': 'Чтение книг', 'color': '#2196F3', 'streak': 8, 'total': 18},
        {'name': 'Медитация', 'color': '#9C27B0', 'streak': 5, 'total': 10},
    ]
    
    # Демо-данные для рецептов
    demo_recipes = [
        {'title': 'Паста Карбонара', 'category': 'Обед', 'prep_time': 15, 'cook_time': 20, 'servings': 4},
        {'title': 'Овсянка с фруктами', 'category': 'Завтрак', 'prep_time': 5, 'cook_time': 10, 'servings': 2},
        {'title': 'Салат Цезарь', 'category': 'Ужин', 'prep_time': 10, 'cook_time': 0, 'servings': 2},
    ]
    
    # Демо-данные для обучения
    demo_study = {
        'total_cards': 45,
        'cards_due': 12,
        'topics': ['Математика', 'Английский язык', 'Программирование'],
        'recent_sessions': [
            {'type': 'pomodoro', 'duration': 25, 'date': '2024-11-10'},
            {'type': 'review', 'duration': 30, 'cards': 15, 'date': '2024-11-09'},
        ]
    }
    
    # Демо-данные для имущества
    demo_inventory = {
        'total_items': 28,
        'total_value': 450000.00,
        'items': [
            {'name': 'Ноутбук MacBook Pro', 'category': 'Электроника', 'room': 'Кабинет', 'price': 150000},
            {'name': 'Диван', 'category': 'Мебель', 'room': 'Гостиная', 'price': 50000},
            {'name': 'Холодильник', 'category': 'Бытовая техника', 'room': 'Кухня', 'price': 80000},
        ],
        'warranty_warnings': 3
    }
    
    # Демо-данные для событий
    demo_events = [
        {'title': 'Концерт в парке', 'date': '2024-11-15', 'time': '19:00', 'location': 'Центральный парк', 'category': 'Концерт', 'price_type': 'free'},
        {'title': 'Выставка современного искусства', 'date': '2024-11-20', 'time': '10:00', 'location': 'Галерея', 'category': 'Выставка', 'price': 500},
        {'title': 'Мастер-класс по кулинарии', 'date': '2024-11-18', 'time': '18:00', 'location': 'Кулинарная школа', 'category': 'Обучение', 'price': 2000},
    ]
    
    return render_template('demo.html',
                         finance=demo_finance,
                         habits=demo_habits,
                         recipes=demo_recipes,
                         study=demo_study,
                         inventory=demo_inventory,
                         events=demo_events)

