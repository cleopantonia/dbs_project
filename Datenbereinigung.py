import pandas as pd
import numpy as np

# lade Datensatz und gib die ersten paar Eintraege aus
df = pd.read_csv('american-election-tweets.csv', delimiter=';',
                 names=['handle','text','is_retweet', 'original_author','time',
                        'in_reply_to_screen_name','is_quote_status','retweet_count',
                        'favorite_count','source_url','truncated'], header=None)
print(df.head())

# entferne uninteressante Informationen aus dem Datensatz und gib den Kopf aus
# hier: is_retweet, original_author, is_quote_status_truncated
df_new = df.drop(['is_retweet','original_author','is_quote_status','truncated'],axis=1)
print(df_new.head())

# Formatiere die Zeitangaben der Tweets entsprechend des sql Datentyps timestamp - format: YYYY-MM-DD HH:MI:SS
# ersetze 'T' mit Leerzeichen
# gib den Kopf aus
df_new['time'] = df_new['time'].str.replace('T',' ')
print(df_new.head())

# hier war mal: ersetze '%' durch den String 'percent', da Zeichen in sql einen wildcard character darstellt
#               df_new['text'] = df_new['text'].str.replace('%',' percent')
# NICHT NoeTIG, DA DURCH DIE RICHTIGE FORMATIERUNG (Mit "...string")
# IN DER SQL-QUERY DAS % NICHT ALS WILDCARD ERKANNT WIRD

# ersetze Apostrophe aus Tweet-Texten durch doppelte Apostrophe, um sql-Probleme von vornherein auszuschliessen
# evtl. Interferenzen zwischen sql und Hochkommata o.ae. werden durch richtige String-Formatierung in queries verhindert
df_new['text'] = df_new['text'].str.replace("'", "''")
# erster Test, ob es geklappt hat
print(df_new.head(10))
# zweiter Test, ob es geklappt hat
print(df_new.loc[[13]])

# ueberpruefe, ob alle Spalten, die keinen Null-Eintrag haben duerfen, auch wirklich keinen haben
# hier: handle,text,time,retweet_count,favorite_count,source_url
# gib alle Reihen aus, in denen eine Spalte gegen diese Anforderung widerspricht
assert any(~df_new['handle'].isnull())
assert any(~df_new['text'].isnull())
assert any(~df_new['time'].isnull())
assert any(~df_new['retweet_count'].isnull())
assert any(~df_new['favorite_count'].isnull())
assert any(~df_new['source_url'].isnull())

# will ueberpruefen, ob Datentypen jeder Spalte einheitlich sind
# gib Datentypen fuer jede Spalte aus
df_new.dtypes
# check, ob jede Spalte den jeweiligen Datentyp bedient und gib einen Error aus, falls eine Spalte einen Eintrag mit
# dem falschen Datentyp hat
# handle,text,time,in_reply_to_screen_name,source_url sind vom Datentyp object
# favorite_count,retweet_count sind vom Datentyp int64
assert df_new.handle.dtype == 'object'
assert df_new.retweet_count.dtype == 'int64'
assert df_new.text.dtype == 'object'
assert df_new.time.dtype == 'object'
assert df_new.in_reply_to_screen_name.dtype == 'object'
assert df_new.favorite_count.dtype == 'int64'
assert df_new.source_url.dtype == 'object'

# gib Anzahl der Objekte in dataframe aus
# 6126 Zeilen
df_new.shape
# entferne Duplikate: A und B seien Duplikate <=> A['handle']==B['handle'] und A['time']==B['time']
# unter der Annahme, dass nicht zwei verschiedene Tweets vom selben Account
# zur exakt selben Zeit gepostet werden koennen
df_new.drop_duplicates(subset=df_new[[0,2]], keep='first', inplace=False).head(n=10)
# Pruefe Zeilenanzahl nach Duplikaten-Entfernung
# Anzahl der entries unveraendert, also existierten gar keine Duplikate
df_new.shape

# konvertiere Datentyp von time(object) ZUM Datentyp datetime um
# => wichtig fuer das Laden der Daten in die Datenbank (time hat in sql den Typ timestamp)
pd.to_datetime(df_new.time)
df_new.time = pd.to_datetime(df_new.time)

# passe Spaltennamen an die Attribut-Namen im Schema der Datenbank an
# gib Kopf aus
# time -> zeit, in_reply_to_screen_name -> in_reply_to,.....WAS NOCH?
df_new.columns = ['handle','inhalt','zeit','in_reply_to','retweet_count','favorite_count','source_url']
print(df_new.head())

# in_reply_to darf Null-Eintraege haben
# ersetze die Null-Eintraege bei in_reply_to durch einen leeren String
df_new.in_reply_to.fillna('')


# speichere gereinigten Datensatz
df_new.to_csv('cleansed_dataframe.csv')
# evtl an den Anfang der Datei...
from sqlalchemy import create_engine
# Lade Datensatz in die Datenbank election ueber die erstellte connection:
engine = create_engine('postgres://postgres:postgres@localhost:5432/election')
df_new.to_sql(name='tweet',con=engine ,index_label='t_id', schema='e_schema',if_exists='append')
