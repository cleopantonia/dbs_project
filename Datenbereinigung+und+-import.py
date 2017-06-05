# Befehle, die tables speichern oder Daten in die DB importieren wurden auskommentiert
import pandas as pd
import numpy as np

# lade Datensatz
df = pd.read_csv('american-election-tweets.csv', delimiter=';',
                 names=['handle','text','is_retweet', 'original_author','time',
                        'in_reply_to_screen_name','is_quote_status','retweet_count',
                        'favorite_count','source_url','truncated'], header=None)
print(df.head())

# entferne uninteressante Informationen aus dem Datensatz
# hier: is_retweet, original_author, is_quote_status_truncated
df_new = df.drop(['is_retweet','original_author','is_quote_status','truncated'],axis=1)
print(df_new.head())

# Formatiere die Zeitangaben der Tweets entsprechend des sql Datentyps timestamp - format: YYYY-MM-DD HH:MI:SS
# ersetze 'T' mit Leerzeichen
df_new['time'] = df_new['time'].str.replace('T',' ')
print(df_new.head())

# hier war mal: ersetze '%' durch den String 'percent', da Zeichen in sql einen wildcard character darstellt
#               df_new['text'] = df_new['text'].str.replace('%',' percent')
# NICHT NÖTIG, DA DURCH DIE RICHTIGE FORMATIERUNG (Mit "...string")
# IN DER SQL-QUERY DAS % NICHT ALS WILDCARD ERKANNT WIRD

# ersetze Apostrophe aus Tweet-Texten durch doppelte Apostrophe, um sql-Probleme von vornherein auszuschließen
# evtl. Interferenzen zwischen sql und Hochkommata o.Ä. werden durch richtige String-Formatierung in queries verhindert
df_new['text'] = df_new['text'].str.replace("'", "''")
# erster Test, ob es geklappt hat
print(df_new.head(10))
#zweiter Test, ob es geklappt hat
print(df_new.loc[[13]])

# überprüfe, ob alle Spalten, die keinen Null-Eintrag haben dürfen, auch wirklich keinen haben
# hier: handle,text,time,retweet_count,favorite_count,source_url
# gib alle Reihen aus, in denen eine Spalte gegen diese Anforderung widerspricht
assert any(~df_new['handle'].isnull())
assert any(~df_new['text'].isnull())
assert any(~df_new['time'].isnull())
assert any(~df_new['retweet_count'].isnull())
assert any(~df_new['favorite_count'].isnull())
assert any(~df_new['source_url'].isnull())

# will überprüfen, ob Datentypen jeder Spalte einheitlich sind
# gib Datentypen für jede Spalte aus
print(df_new.dtypes)
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
print(df_new.shape)
# entferne Duplikate: A und B seien Duplikate <=> A['handle']==B['handle'] und A['time']==B['time']
# unter der Annahme, dass nicht zwei verschiedene Tweets vom selben Account
# zur exakt selben Zeit gepostet werden können
df_new.drop_duplicates(subset=df_new[[0,2]], keep='first', inplace=False).head(n=10)
# Prüfe Zeilenanzahl nach Duplikaten-Entfernung
# Anzahl der entries unverändert, also existierten gar keine Duplikate
print(df_new.shape)

# konvertiere Datentyp von time(object) in den Datentyp datetime um
# wichtig für das Laden der Daten in die Datenbank (time hat in sql den Typ timestamp)
pd.to_datetime(df_new.time)
df_new.time = pd.to_datetime(df_new.time)

# passe Spaltennamen an die Attribut-Namen im Schema der Datenbank an
df_new.columns = ['handle','inhalt','zeit','in_reply_to','retweet_count','favorite_count','source_url']
print(df_new.head())

# ersetze die Null-Einträge bei in_reply_to durch einen leeren String
df_new.in_reply_to.fillna('')

# speichere gereinigten Datentyp
#df_new.to_csv('cleansed_dataframe.csv')

#from sqlalchemy import create_engine
# Lade Datensatz in die Datenbank election über die erstellte connection:
#engine = create_engine('postgres://postgres:postgres@localhost:5432/election')
#df_new.to_sql(name='tweet',con=engine ,index_label='t_id', schema='e_schema',if_exists='append')


# erstelle neuen dataframe hash_tag mit 2 columns name,abs_hauf
# (h_id wird beim importieren d. Daten durch den Index gestellt)
hash_tag = pd.DataFrame(columns=['name','abs_hauf'])

# behalte nur die rows, in denen der Tweet ein Rautezeichen hat
df_help = df_new[df_new['inhalt'].str.contains("#")]
hash_tag['name'] = df_help['inhalt']
hash_tag
# Index stellt später Hashtag_ID => zwei Hashtags in einem Tweet müssen verschiedene IDs haben, deshalb einen
# neuen fortlaufenden Index erstellen
# Überschreibe den Index
hash_tag.reset_index(drop=True)

import re
# finde alle Hashtags mit den folgenden Eigenschaften:
# String beginnt direkt nach einem Rautezeichen und enthält NUR Groß-/Kleinbuchstaben und Zahlen,
# keine Sonderzeichen und kein Leerzeichen
# das Rautezeichen selbst soll nicht gespeichert werden
pat = re.compile(r"#([a-zA-Z0-9]+)")
# gib gleich tags aus und zeige leere Liste in letzter Zeile
tags = []
# speichere das Ergebnis für jeden Zell-Eintrag in einer Liste, da ein Tweet mehrere Hashtags haben kann
for i in hash_tag['name']:
    tags += [pat.findall(i)]
# erstelle ein leeres Set und fülle es mit allen Hashtags aus der Liste tags
# sets enthalten keine Duplikate
set_tags = set()
for l in tags:
    for element in l:
        set_tags.add(element)

# Gib Menge der eindeutigen Hashtags aus
print(len(set_tags))

# erstelle neuen data frame und fülle name-column mit den eindeutigen Hashtags
df_tags = pd.DataFrame(columns=['name','abs_hauf'])
df_tags['name'] = list(set_tags)
print(df_tags)

# definiere Zählfunktion für absolute Häufigkeiten
def count_occurrences(hashtag):
    count = 0
    for l in tags:
        if hashtag in l:
            count += 1
    return count
# zähle für jeden Hashtag im set die absolute Häufigkeit in der Liste tags (nicht-eindeutigen Hashtag-Liste)
df_tags.abs_hauf = df_tags.name.apply(count_occurrences)
print(df_tags)

#df_tags.to_csv('hashtag_dataframe.csv')
#from sqlalchemy import create_engine
#engine2 = create_engine('postgres://postgres:postgres@localhost:5432/election')
#df_tags.to_sql(name='hashtag',con=engine2 ,index_label='h_id', schema='e_schema',if_exists='append')


# erstelle data frame für enthaelt-table (e_schema) => Zieltabelle
df_contains = pd.DataFrame(columns=['f_t_id','f_h_id'])
# erstelle dataframe hilfe2 mit den tweet-IDs und der jeweiligen Liste von Hashtags
hilfe = df_new[df_new['inhalt'].str.contains("#")]
hilfe2 = hilfe.drop(['handle','zeit','in_reply_to','retweet_count','favorite_count','source_url'],axis=1)
hilfe2['inhalt'] = tags

# im Tweet mit der ID 6125 wollte Trump einen Hashtag zum Thema 'Make America Great again' posten,
# hat diesen aber falsch getippt (# (Leerzeichen) MAKE...), sodass dieser von Twitter nicht als Hashtag registriert
# wurde. In der hilfe2-Tabelle steht daher im entsprechenden Eintrag nur eine leere Liste
print(hilfe2)

# lösche Reihe mit leerem Hashtag
hilfe2.drop(hilfe2.index[len(hilfe2)-1])
# füge für jeden Hashtag eines Tweets die Tweet-ID in die Liste indexe ein
indexe = []
for idx, x in hilfe2['inhalt'].iteritems():
    for k in x:
        indexe.append(idx)

# füge für jeden Hashtag in einem Tweet die entsprechende Hashtag-ID aus df_tags in die Liste indices
# indices ist Liste von Listen, da Hashtags in hilfe2['inhalt'] ebenfalls als Listen in einer Liste gespeichert sind
indices = []
for l in hilfe2['inhalt']:
    for m in l:
        indices.append(df_tags[df_tags['name'] == m].index.tolist())

# speichere Hashtag-IDs als Liste von ints in der entsprechenden Spalte der Zieltabelle
df_contains['f_h_id'] = [lis[0] for lis in indices]

# speichere Liste mit Tweet-IDs in der entsprechenden Spalte der Zieltabelle
df_contains['f_t_id'] = indexe
print(df_contains)

#df_contains.to_csv('enthaelt_dataframe.csv')
#from sqlalchemy import create_engine
#engine3 = create_engine('postgres://postgres:postgres@localhost:5432/election')
# die Daten aus df_contains können nicht in die Datenbank importiert werden, da im Tweet mit der ID
# 4969 zweimal der Hashtag #Trump vorkommt
# Lösung: füge eine ID als primary Key zum table hinzu, sodass Tupel nicht mehr identisch
#df_contains.to_sql(name='enthaelt',con=engine3 ,index_label='c_id',schema='e_schema',if_exists='append')


# erstelle data frame, welches später in DB importiert wird
df_paarweise = pd.DataFrame(columns=['f_h_id1','f_h_id2','p_hauf'])

# definiere Hilfsfunktion, die prüft, ob zwei Hashtags X und Y bereits in der einen oder anderen Reihenfolge ((X,Y),(Y,X))
# paarweise auftreten => wenn True, gib den entsprechenden index aus, sonst return None
def tupel_check(a,b):
    for i in range(len(f_h_id1)):
        if f_h_id1[i]==a and f_h_id2[i]==b:
            return i
    return None
# erstelle leere Listen, die später den Spalten von df_paarweise entsprechen sollen
f_h_id1 = []
f_h_id2 = []
p_hauf = []
# iteriere durch die Hashtag-Liste jedes Tweets
# wenn Tweet mehr als einen Hashtag enthält => prüfe für jedes Hashtag-Paar das bisherige paarweise Auftreten
# wenn Paar noch nicht aufgetreten, füge es in die Listen f_h_id1 und f_h_id2 ein
# erhöhe den Counter jeweils entsprechend
for idx,x in hilfe2['inhalt'].iteritems():
    if len(x) >= 2:
        i=0
        while i<len(x):
            j=i+1
            while j<len(x):
                id1 = df_tags[df_tags['name'] == x[i]].index.tolist()
                id2 = df_tags[df_tags['name'] == x[j]].index.tolist()
                if tupel_check(id1[0],id2[0])is not None:
                    index = tupel_check(id1,id2)
                    p_hauf[index] +=1
                elif tupel_check(id2[0],id1[0])is not None:
                    index = tupel_check(id2,id1)
                    p_hauf[index] +=1
                else:
                    f_h_id1.append(id1[0])
                    f_h_id2.append(id2[0])
                    p_hauf.append(1)
                j += 1
            i +=1

# lade Listen in data frame
df_paarweise['f_h_id1'] = f_h_id1
df_paarweise['f_h_id2'] = f_h_id2
df_paarweise['p_hauf']  = p_hauf
print(df_paarweise)

#from sqlalchemy import create_engine
#engine4 = create_engine('postgres://postgres:postgres@localhost:5432/election')
# speichere table
#df_paarweise.to_csv('paarweise_dataframe.csv')
# importiere table in die DB
#df_paarweise.to_sql(name='paarweise',con=engine4,index=False,schema='e_schema',if_exists='append')
