import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from io import BytesIO
from PIL import Image, ImageTk

class MovieRatingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Movie Rating App")
        self.root.geometry("800x600")
        
        # API configuration
        self.OMDB_API_KEY = '40a368d3'
        self.OMDB_URL = 'http://www.omdbapi.com/'
        
        # Local storage
        self.ratings_file = os.path.expanduser('~/.movie_ratings.json')
        self.ratings = self.load_ratings()
        
        # GUI elements
        self.create_widgets()
        
    def create_widgets(self):
        # Search section
        search_frame = ttk.Frame(self.root, padding=10)
        search_frame.pack(fill=tk.X)
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_btn = ttk.Button(search_frame, text="Search", command=self.search_movies)
        search_btn.pack(side=tk.LEFT, padx=5)
        
        # Results list
        self.results_list = tk.Listbox(self.root, height=10)
        self.results_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.results_list.bind('<<ListboxSelect>>', self.show_movie_details)
        
        # Movie details
        details_frame = ttk.Frame(self.root)
        details_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.poster_label = ttk.Label(details_frame)
        self.poster_label.pack(side=tk.LEFT)
        
        info_frame = ttk.Frame(details_frame)
        info_frame.pack(side=tk.LEFT, padx=10)
        
        self.title_label = ttk.Label(info_frame, text="Title: ")
        self.title_label.pack(anchor=tk.W)
        self.year_label = ttk.Label(info_frame, text="Year: ")
        self.year_label.pack(anchor=tk.W)
        self.rating_label = ttk.Label(info_frame, text="IMDB Rating: ")
        self.rating_label.pack(anchor=tk.W)
        
        # User rating
        rating_frame = ttk.Frame(self.root)
        rating_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(rating_frame, text="Your Rating (0-10):").pack(side=tk.LEFT)
        self.user_rating = ttk.Entry(rating_frame, width=5)
        self.user_rating.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(rating_frame, text="Review:").pack(side=tk.LEFT, padx=5)
        self.user_review = ttk.Entry(rating_frame, width=40)
        self.user_review.pack(side=tk.LEFT, padx=5)
        
        rate_btn = ttk.Button(rating_frame, text="Rate", command=self.save_rating)
        rate_btn.pack(side=tk.LEFT)
        
        # Ratings list
        self.ratings_tree = ttk.Treeview(self.root, columns=('title', 'year', 'rating', 'review'), show='headings')
        self.ratings_tree.heading('title', text='Title')
        self.ratings_tree.heading('year', text='Year')
        self.ratings_tree.heading('rating', text='Your Rating')
        self.ratings_tree.heading('review', text='Review')
        self.ratings_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.update_ratings_list()
        
    def search_movies(self):
        query = self.search_var.get()
        if not query:
            return
            
        params = {
            'apikey': self.OMDB_API_KEY,
            's': query,
            'type': 'movie',
            'page': 1
        }
        
        response = requests.get(self.OMDB_URL, params=params)
        data = response.json()
        
        self.results_list.delete(0, tk.END)
        
        if data.get('Search'):
            for movie in data['Search']:
                self.results_list.insert(tk.END, f"{movie['Title']} ({movie['Year']})")
                self.results_list.movies = data['Search']
        else:
            messagebox.showerror("Error", data.get('Error', 'Unknown error'))
    
    def show_movie_details(self, event):
        selection = self.results_list.curselection()
        if not selection:
            return
            
        movie = self.results_list.movies[selection[0]]
        
        # Load full details
        params = {
            'apikey': self.OMDB_API_KEY,
            'i': movie['imdbID'],
            'plot': 'short'
        }
        
        response = requests.get(self.OMDB_URL, params=params)
        details = response.json()
        
        self.title_label.config(text=f"Title: {details.get('Title', 'N/A')}")
        self.year_label.config(text=f"Year: {details.get('Year', 'N/A')}")
        self.rating_label.config(text=f"IMDB Rating: {details.get('imdbRating', 'N/A')}")
        
        # Load poster
        if details.get('Poster') and details['Poster'] != 'N/A':
            response = requests.get(details['Poster'])
            image_data = response.content
            image = Image.open(BytesIO(image_data))
            image.thumbnail((100, 150))
            photo = ImageTk.PhotoImage(image)
            self.poster_label.config(image=photo)
            self.poster_label.image = photo
    
    def save_rating(self):
        selection = self.results_list.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Select a movie first!")
            return
            
        try:
            rating = float(self.user_rating.get())
            if not (0 <= rating <= 10):
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid rating between 0 and 10")
            return
            
        review = self.user_review.get()
        movie = self.results_list.movies[selection[0]]
        
        # Check if already rated
        for idx, item in enumerate(self.ratings):
            if item['imdbID'] == movie['imdbID']:
                self.ratings[idx] = {
                    'imdbID': movie['imdbID'],
                    'title': movie['Title'],
                    'year': movie['Year'],
                    'user_rating': rating,
                    'review': review
                }
                break
        else:
            self.ratings.append({
                'imdbID': movie['imdbID'],
                'title': movie['Title'],
                'year': movie['Year'],
                'user_rating': rating,
                'review': review
            })
            
        self.save_ratings()
        self.update_ratings_list()
        messagebox.showinfo("Success", "Rating saved!")
    
    def load_ratings(self):
        try:
            with open(self.ratings_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_ratings(self):
        with open(self.ratings_file, 'w') as f:
            json.dump(self.ratings, f)
    
    def update_ratings_list(self):
        for row in self.ratings_tree.get_children():
            self.ratings_tree.delete(row)
            
        for rating in self.ratings:
            self.ratings_tree.insert('', tk.END, values=(
                rating['title'],
                rating['year'],
                rating['user_rating'],
                rating['review']
            ))

if __name__ == '__main__':
    root = tk.Tk()
    app = MovieRatingApp(root)
    root.mainloop()