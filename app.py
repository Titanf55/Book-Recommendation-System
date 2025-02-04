import os 
import pandas as pd
from flask import Flask, jsonify, render_template,request,redirect, url_for, flash, session
from flask_cors import CORS
import requests
app = Flask(__name__)
CORS(app) 
app.secret_key = os.getenv('SECRET_KEY', 'fallback-secret-key')
df = pd.read_csv('data.csv')

# Process the data (drop nulls, remove unnecessary columns, etc.)
df = df.drop(columns=['isbn13', 'isbn10','subtitle','published_year','num_pages'], errors='ignore')
df = df.dropna(subset=['ratings_count', 'average_rating', 'categories'])  # Drop rows with null values in important columns

def recommend_books(title, df):
    # Convert the title to lowercase for case-insensitive matching
    title = title.lower()

    # Check if the book title exists in the DataFrame (case-insensitive)
    if not any(df['title'].str.lower() == title):
        return None  # If the title is not found, return None
    
    # Find the category of the input book
    book_category = df.loc[df['title'].str.lower() == title, 'categories'].iloc[0]
    
    # Filter books that belong to the same category
    same_category_books = df[df['categories'] == book_category]
    
    # Sort the books by ratings count and average rating
    sorted_books = same_category_books.sort_values(by=['ratings_count', 'average_rating'], ascending=[False, False])
    
    # Get the top 9 recommended books
    input_book = df[df['title'].str.lower() == title].iloc[0]
    top_books = sorted_books.head(9)
    
    # Concatenate the input book and the top recommended books
    top_books = pd.concat([input_book.to_frame().T, top_books], ignore_index=True)
    
    return top_books

# Temporary storage for users (In-memory dictionary)
users = {}

@app.route('/')
def home():
    # Redirect to signup page as the default
    return redirect(url_for('signup'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if email in users:
            flash('Email already registered! Please login.', 'error')
            return redirect(url_for('login'))
        
        users[email] = password  # Add new user
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if email in users and users[email] == password:
            session['user'] = email  # Store user session
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials. Please try again.', 'error')

    return render_template('login.html')

@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        title = request.form['title']  # Get the title from the form
        recommendations = recommend_books(title, df)  # Get book recommendations
        if recommendations is not None:
            # Convert DataFrame to a list of dictionaries for rendering
            return render_template('recommend.html', books=recommendations.to_dict(orient='records'))
        else:
            return render_template('index.html', error="Book not found. Please try again.")
    
    return render_template('index.html')  # Default GET request renders the main page

@app.route('/genre/<genre>')
def genre_books(genre):
    # Fetch books based on genre from Open Library API
    url = f"https://openlibrary.org/subjects/{genre}.json"
    response = requests.get(url)

    if response.status_code == 200:
        books_data = response.json().get('works', [])
        books = []
        for book in books_data:
            book_info = {
                'title': book['title'],
                'key': book['key'],
                'authors': [author['name'] for author in book.get('authors', [])],
                'cover_url': f"https://covers.openlibrary.org/b/id/{book['cover_id']}-L.jpg" if 'cover_id' in book else "https://via.placeholder.com/100x150?text=No+Cover",
                'description': book.get('description', 'No description available.')
            }
            books.append(book_info)
        return render_template('genre.html', genre=genre, books=books)
    else:
        return render_template('genre.html', genre=genre, books=None)

if __name__ == '__main__':
    app.run(debug=True)


