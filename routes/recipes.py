from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Recipe, MealPlan
from datetime import datetime, date, timedelta
from werkzeug.utils import secure_filename
import os
import json

recipes_bp = Blueprint('recipes', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@recipes_bp.route('/')
@login_required
def index():
    """Главная страница менеджера рецептов"""
    recipes = Recipe.query.filter_by(user_id=current_user.id).all()
    return render_template('recipes/index.html', recipes=recipes)

@recipes_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_recipe():
    """Добавление нового рецепта"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        ingredients = request.form.get('ingredients')
        instructions = request.form.get('instructions')
        prep_time = request.form.get('prep_time')
        cook_time = request.form.get('cook_time')
        servings = request.form.get('servings')
        category = request.form.get('category')
        calories = request.form.get('calories')
        
        if not title or not ingredients or not instructions:
            flash('Заполните все обязательные поля', 'error')
            return render_template('recipes/add_recipe.html')
        
        # Обработка изображения
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                upload_folder = os.path.join('uploads', 'recipes')
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                image_path = filepath
        
        recipe = Recipe(
            user_id=current_user.id,
            title=title,
            description=description,
            ingredients=ingredients,
            instructions=instructions,
            prep_time=int(prep_time) if prep_time else None,
            cook_time=int(cook_time) if cook_time else None,
            servings=int(servings) if servings else None,
            category=category,
            calories=float(calories) if calories else None,
            image_path=image_path
        )
        db.session.add(recipe)
        db.session.commit()
        
        flash('Рецепт добавлен', 'success')
        return redirect(url_for('recipes.index'))
    
    return render_template('recipes/add_recipe.html')

@recipes_bp.route('/view/<int:id>')
@login_required
def view_recipe(id):
    """Просмотр рецепта"""
    recipe = Recipe.query.get_or_404(id)
    
    if recipe.user_id != current_user.id:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('recipes.index'))
    
    return render_template('recipes/view_recipe.html', recipe=recipe)

@recipes_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_recipe(id):
    """Редактирование рецепта"""
    recipe = Recipe.query.get_or_404(id)
    
    if recipe.user_id != current_user.id:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('recipes.index'))
    
    if request.method == 'POST':
        recipe.title = request.form.get('title')
        recipe.description = request.form.get('description')
        recipe.ingredients = request.form.get('ingredients')
        recipe.instructions = request.form.get('instructions')
        recipe.prep_time = int(request.form.get('prep_time')) if request.form.get('prep_time') else None
        recipe.cook_time = int(request.form.get('cook_time')) if request.form.get('cook_time') else None
        recipe.servings = int(request.form.get('servings')) if request.form.get('servings') else None
        recipe.category = request.form.get('category')
        recipe.calories = float(request.form.get('calories')) if request.form.get('calories') else None
        
        # Обработка нового изображения
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                # Удаляем старое изображение
                if recipe.image_path and os.path.exists(recipe.image_path):
                    os.remove(recipe.image_path)
                
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                upload_folder = os.path.join('uploads', 'recipes')
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                recipe.image_path = filepath
        
        db.session.commit()
        flash('Рецепт обновлен', 'success')
        return redirect(url_for('recipes.view_recipe', id=recipe.id))
    
    return render_template('recipes/edit_recipe.html', recipe=recipe)

@recipes_bp.route('/delete/<int:id>')
@login_required
def delete_recipe(id):
    """Удаление рецепта"""
    recipe = Recipe.query.get_or_404(id)
    
    if recipe.user_id != current_user.id:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('recipes.index'))
    
    # Удаляем изображение
    if recipe.image_path and os.path.exists(recipe.image_path):
        os.remove(recipe.image_path)
    
    db.session.delete(recipe)
    db.session.commit()
    flash('Рецепт удален', 'success')
    return redirect(url_for('recipes.index'))

@recipes_bp.route('/meal_planner')
@login_required
def meal_planner():
    """Планировщик питания"""
    # Получаем план на текущую неделю
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    meal_plans = MealPlan.query.filter_by(user_id=current_user.id)\
        .filter(MealPlan.date >= week_start, MealPlan.date <= week_end)\
        .order_by(MealPlan.date, MealPlan.meal_type).all()
    
    # Группируем по датам
    plans_by_date = {}
    for plan in meal_plans:
        date_str = plan.date.isoformat()
        if date_str not in plans_by_date:
            plans_by_date[date_str] = {}
        plans_by_date[date_str][plan.meal_type] = plan
    
    # Получаем все рецепты для выбора
    recipes = Recipe.query.filter_by(user_id=current_user.id).all()
    
    # Создаем список дат для недели
    week_dates = []
    for i in range(7):
        week_dates.append(week_start + timedelta(days=i))
    
    return render_template('recipes/meal_planner.html',
                         plans_by_date=plans_by_date,
                         recipes=recipes,
                         week_start=week_start,
                         week_end=week_end,
                         week_dates=week_dates)

@recipes_bp.route('/meal_planner/add', methods=['POST'])
@login_required
def add_meal_plan():
    """Добавление блюда в план питания"""
    recipe_id = request.form.get('recipe_id')
    meal_date = request.form.get('date')
    meal_type = request.form.get('meal_type')
    
    if not recipe_id or not meal_date or not meal_type:
        flash('Заполните все поля', 'error')
        return redirect(url_for('recipes.meal_planner'))
    
    meal_date = datetime.strptime(meal_date, '%Y-%m-%d').date()
    
    # Проверяем, не существует ли уже план на это время
    existing = MealPlan.query.filter_by(
        user_id=current_user.id,
        date=meal_date,
        meal_type=meal_type
    ).first()
    
    if existing:
        existing.recipe_id = recipe_id
    else:
        meal_plan = MealPlan(
            user_id=current_user.id,
            recipe_id=recipe_id,
            date=meal_date,
            meal_type=meal_type
        )
        db.session.add(meal_plan)
    
    db.session.commit()
    flash('Блюдо добавлено в план', 'success')
    return redirect(url_for('recipes.meal_planner'))

@recipes_bp.route('/meal_planner/delete/<int:id>')
@login_required
def delete_meal_plan(id):
    """Удаление из плана питания"""
    meal_plan = MealPlan.query.get_or_404(id)
    
    if meal_plan.user_id != current_user.id:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('recipes.meal_planner'))
    
    db.session.delete(meal_plan)
    db.session.commit()
    flash('Блюдо удалено из плана', 'success')
    return redirect(url_for('recipes.meal_planner'))

@recipes_bp.route('/shopping_list')
@login_required
def shopping_list():
    """Автоматический список покупок на основе плана питания"""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    meal_plans = MealPlan.query.filter_by(user_id=current_user.id)\
        .filter(MealPlan.date >= week_start, MealPlan.date <= week_end)\
        .join(Recipe).all()
    
    # Собираем все ингредиенты
    all_ingredients = []
    for plan in meal_plans:
        ingredients = plan.recipe.ingredients.split('\n')
        all_ingredients.extend([ing.strip() for ing in ingredients if ing.strip()])
    
    # Удаляем дубликаты и сортируем
    unique_ingredients = sorted(set(all_ingredients))
    
    return render_template('recipes/shopping_list.html',
                         ingredients=unique_ingredients,
                         week_start=week_start,
                         week_end=week_end)

@recipes_bp.route('/search')
@login_required
def search():
    """Поиск рецептов"""
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    
    recipes_query = Recipe.query.filter_by(user_id=current_user.id)
    
    if query:
        recipes_query = recipes_query.filter(
            Recipe.title.contains(query) |
            Recipe.description.contains(query) |
            Recipe.ingredients.contains(query)
        )
    
    if category:
        recipes_query = recipes_query.filter_by(category=category)
    
    recipes = recipes_query.all()
    
    return render_template('recipes/search.html', recipes=recipes, query=query, category=category)

