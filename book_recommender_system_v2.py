# -*- coding: utf-8 -*-
"""book_recommender_system_v2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1iVx7GGTDmaSN0eQEvIetmnxtQEleX2th

#BOOK RECOMMENDER SYSTEM


*   Nama: Iva Raudyatuzzahra
*   Dataset : https://www.kaggle.com/datasets/arashnic/book-recommendation-dataset/code?datasetId=1004280&sortBy=voteCount

##Data Collection

Membaca dataset
"""

import pandas as pd

book = pd.read_csv('/content/Books.csv')
user = pd.read_csv('/content/Users.csv')
rating = pd.read_csv('/content/Ratings.csv')

"""##Exploratory Data Analysis

###Informasi Data

Data Buku
"""

book.info()

"""Data User"""

user.info()

"""Data Rating"""

rating.info()

rating.describe()

"""###Cek Missing Value"""

book.isnull().sum()

user.isnull().sum()

rating.isnull().sum()

"""### Cek Data Duplikat"""

print(book.duplicated().sum())
print(user.duplicated().sum())
print(rating.duplicated().sum())

"""##Data Preparation

###Menggabungkan data rating dan data buku
"""

rating_book = rating.merge(book,on='ISBN', how='left')
rating_book.head(2)

"""###Menggabungkan data user dan data rating_book"""

data = rating_book.merge(user,on='User-ID', how='left')
data.head(2)

"""###Menghapus fitur yang tidak diperlukan"""

data.drop(columns=["ISBN","Image-URL-S","Image-URL-M","Age"],axis=1,inplace=True)
data.info()

"""Cek Missing Value"""

data.isnull().sum()

"""Drop Missing Values"""

data_clean = data.dropna()

data_clean.isnull().sum()

"""Split data dalam fitur Location"""

data_clean['Location'] = data_clean['Location'].str.split(',').str[-1].str.strip()
data_clean.head()

"""Membuat dataframe berisi agregasi jumlah rating berdasarkan judul buku"""

n_rating = data_clean.groupby('Book-Title').count()['Book-Rating'].reset_index()
n_rating.rename(columns={'Book-Rating': 'num_ratings'}, inplace=True)
n_rating.head(3)

"""Membuat dataframe berisi rata-rata jumlah rating berdasarkan judul buku"""

avg_rating = data_clean.groupby('Book-Title').mean()['Book-Rating'].reset_index()
avg_rating.rename(columns={'Book-Rating': 'avg_ratings'}, inplace=True)
avg_rating.head(3)

"""Membuat dataframe buku populer"""

pop_data = n_rating.merge(avg_rating, on='Book-Title')
pop_data.head(3)

pop_data.sort_values("num_ratings",ascending=False).head(10)

"""##Data Preprocessing

### Mengubah tipe dan format data

Tipe data user id menjadi integer
"""

user_id = rating['User-ID'].unique().tolist()

user_to_user_encoded = {x: i for i, x in enumerate(user_id)}

user_encoded_to_user = {i: x for i, x in enumerate(user_id)}

book_id = rating['ISBN'].unique().tolist()
book_to_book_encoded = {x: i for i, x in enumerate(book_id)}
book_encoded_to_book = {i: x for i, x in enumerate(book_id)}

rating['user'] = rating['User-ID'].map(user_to_user_encoded)
rating['book'] = rating['ISBN'].map(book_to_book_encoded)

"""Mengubah tipe data rating menjadi float"""

import numpy as np
num_users = len(user_encoded_to_user)
print(num_users)
num_book = len(book_encoded_to_book)
print(num_book)
rating['Book-Rating'] = rating['Book-Rating'].values.astype(np.float32)

min_rating = min(rating['Book-Rating'])
max_rating = max(rating['Book-Rating'])

print('Number of User: {}, Number of Book: {}, Min Rating: {}, Max Rating: {}'.format(
    num_users, num_book, min_rating, max_rating
))

"""Membagi Dataset"""

rating = rating.sample(frac=1, random_state=42)
rating

x = rating[['user', 'book']].values

y = rating['Book-Rating'].apply(lambda x: (x - min_rating) / (max_rating - min_rating)).values

train_indices = int(0.70 * rating.shape[0])
x_train, x_val, y_train, y_val = (
    x[:train_indices],
    x[train_indices:],
    y[:train_indices],
    y[train_indices:]
)

print(x, y)

"""##Model Development menggunakan Collaborative Filtering

Impor Library dan Packages
"""

from tensorflow import keras
from tensorflow.keras import layers
import tensorflow as tf

"""Model RecommenderNet"""

class RecommenderNet(tf.keras.Model):

  def __init__(self, num_users, num_book, embedding_size, **kwargs):
    super(RecommenderNet, self).__init__(**kwargs)
    self.num_users = num_users
    self.num_book = num_book
    self.embedding_size = embedding_size
    self.user_embedding = layers.Embedding(
        num_users,
        embedding_size,
        embeddings_initializer = 'he_normal',
        embeddings_regularizer = keras.regularizers.l2(1e-6)
    )
    self.user_bias = layers.Embedding(num_users, 1)
    self.book_embedding = layers.Embedding(
        num_book,
        embedding_size,
        embeddings_initializer = 'he_normal',
        embeddings_regularizer = keras.regularizers.l2(1e-6)
    )
    self.book_bias = layers.Embedding(num_book, 1)

  def call(self, inputs):
    user_vector = self.user_embedding(inputs[:,0])
    user_bias = self.user_bias(inputs[:, 0])
    book_vector = self.book_embedding(inputs[:, 1])
    book_bias = self.book_bias(inputs[:, 1])

    dot_user_book = tf.tensordot(user_vector, book_vector, 2)

    x = dot_user_book + user_bias + book_bias

    return tf.nn.sigmoid(x)

"""Compile Model"""

model = RecommenderNet(num_users, num_book, 50)

model.compile(
    loss = tf.keras.losses.BinaryCrossentropy(),
    optimizer = keras.optimizers.Adam(learning_rate=0.001),
    metrics=[tf.keras.metrics.RootMeanSquaredError()]
)

"""Training Model"""



history = model.fit(
    x = x_train,
    y = y_train,
    batch_size = 25,
    epochs = 5,
    validation_data = (x_val, y_val)
)

"""## Evaluasi

RMSE
"""

import matplotlib.pyplot as plt

plt.plot(history.history['root_mean_squared_error'])
plt.plot(history.history['val_root_mean_squared_error'])
plt.title('model_metrics')
plt.ylabel('root_mean_squared_error')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='upper left')
plt.show()

"""##Prediksi

Memahami riwayat bacaan pengguna

10 Rekomendasi Buku
"""

book_df = book
book_dataset = book_df.rename(columns={'Book-Title': 'book_title','Book-Author':'book_author','Year-Of-Publication':'year_of_publication','Image-URL-S':'Image_URL_S','Image-URL-M':'Image_URL_M','Image-URL-L':'Image_URL_L'})
rating_dataset = pd.read_csv('/content/Ratings.csv')
rating_dataset = rating_dataset.rename(columns={'Book-Rating': 'rating','User-ID':'user_id'})


user_id = rating_dataset.user_id.sample(1).iloc[0]
books_have_been_read_by_user = rating_dataset[rating_dataset.user_id == user_id]

books_have_not_been_read_by_user = book_df[book_df['ISBN'].isin(books_have_been_read_by_user.ISBN.values)]['ISBN']
books_have_not_been_read_by_user = list(
    set(books_have_not_been_read_by_user)
    .intersection(set(book_to_book_encoded.keys()))
)

books_have_not_been_read_by_user = [[book_to_book_encoded.get(x)] for x in books_have_not_been_read_by_user]
user_encoder = user_to_user_encoded.get(user_id)
user_book_array = np.hstack(
    ([[user_encoder]] * len(books_have_not_been_read_by_user), books_have_not_been_read_by_user)
)

ratings = model.predict(user_book_array).flatten()

top_ratings_indices = ratings.argsort()[-5:][::-1]
recommended_book_ids = [
    book_encoded_to_book.get(books_have_not_been_read_by_user[x][0]) for x in top_ratings_indices
]

top_books_recommended = (
    books_have_been_read_by_user.sort_values(
        by = 'rating',
        ascending=False
    )
    .head(5)
    .ISBN.values
)

books_row = book_dataset[book_dataset['ISBN'].isin(top_books_recommended)]
for row in books_row.itertuples():
    print(row.book_title, ':', row.book_author)

print('----' * 8)
print('Top 5 Books Recommendation for user: {}'.format(user_id))
print('----' * 8)

recommended_books = book_dataset[book_dataset['ISBN'].isin(recommended_book_ids)]
for row in recommended_books.itertuples():
    print(row.book_title, ':', row.book_author)