from flask import Flask, render_template, request, redirect, url_for, session
from bson.objectid import ObjectId

from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/userDatabase"
app.config['SECRET_KEY'] = 'mysecretkey'
mongo = PyMongo(app)
items_collection = mongo.db.items
cart_collection = mongo.db.carts





@app.route('/')
def home():
    return render_template('home.html')
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'username': request.form['username']})

        if existing_user:
            return 'Username already exists!'
        
        hashed_password = generate_password_hash(request.form['password'])
        users.insert_one({
            'name': request.form['name'],
            'username': request.form['username'],
            'password': hashed_password
        })
        return redirect(url_for('login'))
    
    return render_template('signup.html')




@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = mongo.db.users
        user = users.find_one({'username': request.form['username']})

        if user and check_password_hash(user['password'], request.form['password']):
            session['username'] = request.form['username']
            session['name'] = user['name']
            items = mongo.db.items.find()  # Fetch all items from the database
            return render_template('logged_in.html', name=session['name'], username=session['username'], items=items)
        
        return 'Invalid username or password'

    
    return render_template('login.html')




@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove the username from the session
    session.pop('name', None)  # If you're storing name in the session
    session.pop('admin', None)  # If you have an admin session variable, remove it as well
    return redirect(url_for('home'))





@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        users = mongo.db.users
        admin = users.find_one({'username': request.form['username'], 'role': 'admin'})

        if admin and check_password_hash(admin['password'], request.form['password']):
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        
        return 'Invalid admin credentials'
    
    return render_template('admin_login.html')




@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin' in session:
        users = mongo.db.users.find()
        items = mongo.db.items.find()  # Fetch all the items from the 'items' collection
        return render_template('admin_dashboard.html', users=users, items=items)  # Pass both users and items to the template
    return redirect(url_for('admin_login'))


@app.route('/create_admin', methods=['GET', 'POST'])
def create_admin():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'username': request.form['username']})

        if existing_user:
            return 'Username already exists!'
        
        hashed_password = generate_password_hash(request.form['password'])
        users.insert_one({
            'name': request.form['name'],
            'username': request.form['username'],
            'password': hashed_password,
            'role': 'admin'
        })
        return 'Admin account created!'
    
    return render_template('create_admin.html')




@app.route('/add_to_cart/<item_id>')
def add_to_cart(item_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user_cart = cart_collection.find_one({'username': session['username']})
    if not user_cart:
        cart_collection.insert_one({
            'username': session['username'],
            'items': [item_id]
        })
    else:
        cart_collection.update_one({'username': session['username']}, {'$push': {'items': item_id}})
    
    return redirect(url_for('logged_in_page'))



@app.route('/logged_in_page')
def logged_in_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    items = mongo.db.items.find()
    user_cart = cart_collection.find_one({'username': session['username']})
    cart_count = len(user_cart['items']) if user_cart else 0
    
    return render_template('logged_in.html', name=session['name'], username=session['username'], items=items, cart_count=cart_count)

@app.route('/checkout')
def checkout():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user_cart = cart_collection.find_one({'username': session['username']})
    cart_items = []
    for item_id in user_cart.get('items', []):
        cart_items.append(items_collection.find_one({'_id': ObjectId(item_id)}))
    
    return render_template('checkout.html', items=cart_items)



@app.route('/confirm_purchase')
def confirm_purchase():
    if 'username' not in session:  # Ensure the user is logged in before confirming purchase
        return redirect(url_for('login'))
    
    # Retrieve the user's cart
    user_cart = cart_collection.find_one({'username': session['username']})

    if not user_cart or not user_cart['items']:  # Check if the cart exists and if there are items in it
        return "Your cart is empty. No purchase to confirm.", 400

    # At this point, you'd typically handle payment processing, inventory management, and other purchase-related tasks.
    # For simplicity, I'll skip these details and simply clear the cart after 'purchase'.

    # Remove items from cart after purchase
    cart_collection.update_one({'username': session['username']}, {'$set': {'items': []}})
    
    # Render the confirm_purchase template to let the user know the purchase was successful
    return render_template('confirm_purchase.html')






if __name__ == '__main__':
    app.run(debug=True)
