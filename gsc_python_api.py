# -*- coding: utf-8 -*-
"""GSC Python API.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/13pZlwl4o9AENle754icBmVywQzY9kWJl

# Импорт библиотек
"""

import pandas as pd
import datetime
from datetime import date, timedelta
import httplib2
from googleapiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow
from collections import defaultdict
from dateutil import relativedelta
import argparse
from oauth2client import client
from oauth2client import file
from oauth2client import tools
import re
import os
from urllib.parse import urlparse

"""# Создание каталога"""

# Get Domain Name to Create a Project
def get_domain_name(start_url):
    domain_name = '{uri.netloc}'.format(uri=urlparse(start_url))  # Get Domain Name To Name Project
    domain_name = domain_name.replace('.','_')
    return domain_name


# Create a project Directory for this website
def create_project(directory):
    if not os.path.exists(directory):
        print('Create project: '+ directory)
        os.makedirs(directory)

"""# Авторизация в API"""

def authorize_creds(creds):
    # Variable parameter that controls the set of resources that the access token permits.
    SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']

    # Path to client_secrets.json file
    CLIENT_SECRETS_PATH = creds

    # Create a parser to be able to open browser for Authorization
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[tools.argparser])
    flags = parser.parse_args([])

    flow = client.flow_from_clientsecrets(
        CLIENT_SECRETS_PATH, scope = SCOPES,
        message = tools.message_if_missing(CLIENT_SECRETS_PATH))

    # Prepare credentials and authorize HTTP
    # If they exist, get them from the storage object
    # credentials will get written back to a file.
    storage = file.Storage('authorizedcreds.dat')
    credentials = storage.get()

    # If authenticated credentials don't exist, open Browser to authenticate
    if credentials is None or credentials.invalid:
        credentials = tools.run_flow(flow, storage, flags)
    http = credentials.authorize(http=httplib2.Http())
    webmasters_service = build('webmasters', 'v3', http=http)
    return webmasters_service

"""# Выполняем запрос"""

def execute_request(service, property_uri, request):
    return service.searchanalytics().query(siteUrl=property_uri, body=request).execute()

"""# Создание функции для обработки CSV-файлов"""

# Create function to write to CSV
def write_to_csv(data,filename):
    if not os.path.isfile(filename):
        data.to_csv(filename)
    else: # else it exists so append without writing the header
        data.to_csv(filename, mode='a', header=False)

# Read CSV if it exists to find dates that have already been processed.
def get_dates_from_csv(path):
    if os.path.isfile(path):
        data = pd.read_csv(path)
        data = pd.Series(data['date'].unique())
        return data
    else:
        pass

"""# Функция для извлечения всех данных"""

# Create function to extract all the data
def extract_data(site,creds,num_days,output):
    domain_name = get_domain_name(site)
    create_project(domain_name)
    full_path = domain_name + '/' + output
    current_dates = get_dates_from_csv(full_path)

    webmasters_service = authorize_creds(creds)

    # Set up Dates
    end_date = datetime.date.today() - relativedelta.relativedelta(days=3)
    start_date = end_date - relativedelta.relativedelta(days=num_days)
    delta = datetime.timedelta(days=1) # This will let us loop one day at the time
    scDict = defaultdict(list)

    while start_date <= end_date:

        if current_dates is not None and current_dates.str.contains(datetime.datetime.strftime(start_date,'%Y-%m-%d')).any():
            print('Existing Date: %s' % start_date)
            start_date += delta
        else:
            print('Start date at beginning: %s' % start_date)

            maxRows = 25000 # Maximum 25K per call
            numRows = 0     # Start at Row Zero
            status = ''     # Initialize status of extraction


            while (status != 'Finished') : # Test with i < 10 just to see how long the task will take to process.
                request = {
                    'startDate': datetime.datetime.strftime(start_date,'%Y-%m-%d'),
                    'endDate': datetime.datetime.strftime(start_date,'%Y-%m-%d'),
                    'dimensions': ['date','page','query'],
                    'rowLimit': maxRows,
                    'startRow': numRows
                }

                response = execute_request(webmasters_service, site, request)

                try:
                #Process the response
                    for row in response['rows']:
                        scDict['date'].append(row['keys'][0] or 0)
                        scDict['page'].append(row['keys'][1] or 0)
                        scDict['query'].append(row['keys'][2] or 0)
                        scDict['clicks'].append(row['clicks'] or 0)
                        scDict['ctr'].append(row['ctr'] or 0)
                        scDict['impressions'].append(row['impressions'] or 0)
                        scDict['position'].append(row['position'] or 0)
                    print('successful at %i' % numRows)

                except:
                    print('error occurred at %i' % numRows)

                #Add response to dataframe
                df = pd.DataFrame(data = scDict)
                df['clicks'] = df['clicks'].astype('int')
                df['ctr'] = df['ctr']*100
                df['impressions'] = df['impressions'].astype('int')
                df['position'] = df['position'].round(2)

                print('Numrows at the start of loop: %i' % numRows)

                try:
                    numRows = numRows + len(response['rows'])
                except:
                    status = 'Finished'

                print('Numrows at the end of loop: %i' % numRows)
                if numRows % maxRows != 0:
                    status = 'Finished'

            start_date += delta
            print('Start date at end: %s' % start_date)
            write_to_csv(df,full_path)
    return df

"""# Выполнить запрос"""

# @title
site = 'https://www.site.com' # Property to extract
site_name = site.split("//")[1]
num_days = 1 # Number of Days to Extract
creds = 'client_secret.json' # Credential file from GSC.
output = f'gsc_data_{site_name}.csv'

extract_data(site,creds,num_days,output)

#df = extract_data(site,creds,num_days,output)
#df.sort_values('clicks',ascending=False)

"""# Работа с файлом"""

df_clicks = pd.read_csv('/content/www_ultimate-guitar_com/gsc_data_www.ultimate-guitar.com.csv', index_col=0) # Hardcode the filename for test
res = df_clicks.loc[df_clicks['position'] > 10, ['query',]]
#res = df_clicks.loc[df_clicks['position'] > 10, ['page', 'query', 'clicks', 'impressions', 'position']]
#res.to_csv('res.csv', mode='a', header=False)

"""# Кластеризация k-means"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import MiniBatchKMeans

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(res['query'])

num_clusters = 100

kmeans = MiniBatchKMeans(n_clusters=num_clusters, random_state=42)
kmeans.fit(X)

res['cluster_label'] = kmeans.labels_

clusters = pd.DataFrame({'query': res['query'], 'cluster_label': res['cluster_label']})

clusters.to_csv('res.csv', mode='a', header=False)
