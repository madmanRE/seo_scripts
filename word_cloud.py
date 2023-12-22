# -*- coding: utf-8 -*-
"""Untitled0.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Jp5xYgH0bf_B8As4-LB02nLdK95naXvS
"""

!pip install stop-words

# Commented out IPython magic to ensure Python compatibility.
import re
import matplotlib.pyplot as plt

from wordcloud import WordCloud
from stop_words import get_stop_words

# %matplotlib inline

STOPWORDS_RU = get_stop_words('russian')

def plot_cloud(wordcloud):
    plt.figure(figsize=(20, 10))
    plt.imshow(wordcloud)
    plt.axis("off")

with open('data.txt', 'r', encoding='utf-8') as f:
  data = re.sub(r'==.*?==+', '', " ".join(f.readlines()).replace('\n', ' '))

  wordcloud = WordCloud(width = 2000,
                        height = 1500,
                        random_state=1,
                        background_color='black',
                        margin=20,
                        colormap='Pastel1',
                        collocations=False,
                        stopwords = STOPWORDS_RU).generate(data)

  plot_cloud(wordcloud)

