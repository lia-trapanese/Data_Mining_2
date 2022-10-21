import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# import pickle

!pip install tslearn

!pip install pyts

from tslearn.metrics import dtw, dtw_path, cdist_dtw, subsequence_cost_matrix

from tslearn.clustering import TimeSeriesKMeans, silhouette_score
from tslearn.generators import random_walks

import matplotlib_inline.backend_inline
matplotlib_inline.backend_inline.set_matplotlib_formats('png', 'pdf')
plt.rcParams.update({'font.size': 12,
                     'xtick.labelsize' : 12,
                     'ytick.labelsize' : 12,
                     'axes.grid': False})

y_train = pd.read_fwf("y_train.txt", header = None)[0]
y_test = pd.read_fwf("y_test.txt", header = None)[0]

subject_train = pd.read_csv("subject_train.txt", header = None)[0]
subject_test = pd.read_csv("subject_test.txt", header = None)[0]

body_x = pd.read_fwf("body_acc_x_train.txt", header = None)
body_y = pd.read_fwf("body_acc_y_train.txt", header = None)
body_z = pd.read_fwf("body_acc_z_train.txt", header = None)

acc_x = pd.read_fwf("total_acc_x_train.txt", header = None)
acc_y = pd.read_fwf("total_acc_y_train.txt", header = None)
acc_z = pd.read_fwf("total_acc_z_train.txt", header = None)

gyro_x = pd.read_fwf("body_gyro_x_train.txt", header = None)
gyro_y = pd.read_fwf("body_gyro_y_train.txt", header = None)
gyro_z = pd.read_fwf("body_gyro_z_train.txt", header = None)

body_x_test = pd.read_fwf("body_acc_x_test.txt", header = None)
body_y_test = pd.read_fwf("body_acc_y_test.txt", header = None)
body_z_test = pd.read_fwf("body_acc_z_test.txt", header = None)

acc_x_test = pd.read_fwf("total_acc_x_test.txt", header = None)
acc_y_test = pd.read_fwf("total_acc_y_test.txt", header = None)
acc_z_test = pd.read_fwf("total_acc_z_test.txt", header = None)

gyro_x_test = pd.read_fwf("body_gyro_x_test.txt", header = None)
gyro_y_test = pd.read_fwf("body_gyro_y_test.txt", header = None)
gyro_z_test = pd.read_fwf("body_gyro_z_test.txt", header = None)

with open("features.txt") as f:
    lines = f.read().splitlines()
    
features = {}
for line in lines:
    idx, name = line.split()
    features[int(idx)-1] = name

with open('activity_labels.txt') as f:
    lines = f.read().splitlines()

activities = {}
for line in lines:
    label, activity = line.split()
    activities[int(label)] = activity

y_train_mapped = y_train.map(activities)
y_test_mapped = y_test.map(activities)

"""# Time series dataframe
Creiamo un dizionario con tutti e 6 i dataframe: body_x, body_y, body_z, gyro_x, gyro_y, gyro_z. Per ognuno di questi dataframe andiamo poi a prenderci solamente le prime 64 colonne (letture). Dobbiamo però considerare che, così facendo, le letture che vanno dalla 64esima alla 127esima colonna dell'ultima riga di ciascun dataframe verrebbero perse. Per tale motivo, prendiamo l'ultima riga per intero. Più precisamente, con le ultime 64 letture dell'ultima riga andiamo a crearci una nuova riga. Alla fine, ciascun dataset non avrà più 7352 righe, bensì 7353.
"""

dict_dfs = {'body_x': body_x,
            'body_y': body_y,
            'body_z': body_z,
            #'acc_x' : acc_x,
            #'acc_y' : acc_y,
            #'acc_z' : acc_z,
            'gyro_x': gyro_x,
            'gyro_y': gyro_y,
            'gyro_z': gyro_z}

for name_df, df in dict_dfs.items():
    last_row = df.iloc[-1:,64:]
    last_row.columns = np.arange(64) # rename columns of the last raw
    first64 = df.iloc[:,:64]
    dict_dfs[name_df] = pd.concat([first64, last_row], ignore_index=True)
    # aggiungiamo anche le colonne ID soggetto e tipo di attività svolta
    dict_dfs[name_df]['subject'] = subject_train
    dict_dfs[name_df]['activity'] = y_train_mapped
    dict_dfs[name_df].iloc[-1, -2:] = dict_dfs[name_df].iloc[-2, -2:]
    dict_dfs[name_df]['subject'] = dict_dfs[name_df]['subject'].astype(int)

dict_dfs_test = {'body_x_test': body_x_test,
                 'body_y_test': body_y_test,
                 'body_z_test': body_z_test,
                 #'acc_x_test': acc_x_test,
                 #'acc_y_test': acc_y_test,
                 #'acc_z_test': acc_z_test,
                 'gyro_x_test': gyro_x_test,
                 'gyro_y_test': gyro_y_test,
                 'gyro_z_test': gyro_z_test}

for name_df, df in dict_dfs_test.items():
    last_row = df.iloc[-1:,64:]
    last_row.columns = np.arange(64) # rename columns of the last raw
    first64 = df.iloc[:,:64]
    dict_dfs_test[name_df] = pd.concat([first64, last_row], ignore_index=True)
    # aggiungiamo anche le colonne ID soggetto e tipo di attività svolta
    dict_dfs_test[name_df]['subject'] = subject_test
    dict_dfs_test[name_df]['activity'] = y_train_mapped
    dict_dfs_test[name_df].iloc[-1, -2:] = dict_dfs_test[name_df].iloc[-2, -2:]
    dict_dfs_test[name_df]['subject'] = dict_dfs_test[name_df]['subject'].astype(int)
    
                
#df_ts_test = pd.DataFrame(dict_dfs_ts_test)

"""#WALKING"""

windows = 100

for name_df,df in dict_dfs.items():
  X_train=[]
  X_test=[]
  temp_train=df
  temp_test=dict_dfs_test[name_df+'_test']

  temp1_train=temp_train.loc[temp_train['activity']=='WALKING']
  temp1_test=temp_test.loc[temp_test['activity']=='WALKING']

  for subject in subject_train.unique():
    temp2=temp1_train.loc[temp1_train['subject']==subject]
    temp2=temp2.iloc[:,:-2]
    ts=temp2.values.ravel()
    ts=pd.Series(ts - ts.mean()/ts.std()).rolling(windows).mean()[windows-1:]
    ts=np.array(ts)
    X_train.append(ts)
  
  for subject in subject_test.unique():
    temp2=temp1_test.loc[temp1_test['subject']==subject]
    temp2=temp2.iloc[:,:-2]
    ts=temp2.values.ravel()
    ts=pd.Series(ts - ts.mean()/ts.std()).rolling(windows).mean()[windows-1:]
    ts=np.array(ts)
    X_test.append(ts)



  df_X_train = pd.DataFrame(X_train)
  cluster_train=df_X_train.values

  df_X_test = pd.DataFrame(X_test)
  cluster_test=df_X_test.values

  km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=1, random_state=0)
  km_dtw.fit(cluster_train)

  clus_train=np.squeeze(km_dtw.cluster_centers_)

  plt.plot(np.squeeze(km_dtw.cluster_centers_).T)
  plt.title(name_df+' WALKING '+' train')
  plt.show()


  km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=1, random_state=0)
  km_dtw.fit(cluster_test)

  clus_test=np.squeeze(km_dtw.cluster_centers_)

  plt.plot(np.squeeze(km_dtw.cluster_centers_).T)
  plt.title(name_df+' WALKING '+' test')

  plt.show()

  temp_dtw=dtw(clus_train,clus_test)
  dtw_array.append(temp_dtw)
print(temp_dtw)

type(clus_test)

"""#WALKING UPSTAIRS"""

act='WALKING_UPSTAIRS'
windows = 100
dtw_array=[]
for name_df,df in dict_dfs.items():
  X_train=[]
  X_test=[]
  temp_train=df
  temp_test=dict_dfs_test[name_df+'_test']

  temp1_train=temp_train.loc[temp_train['activity']==act]
  temp1_test=temp_test.loc[temp_test['activity']==act]

  for subject in subject_train.unique():
    temp2=temp1_train.loc[temp1_train['subject']==subject]
    temp2=temp2.iloc[:,:-2]
    ts=temp2.values.ravel()
    ts=pd.Series(ts - ts.mean()/ts.std()).rolling(windows).mean()[windows-1:]
    ts=np.array(ts)
    X_train.append(ts)
  
  for subject in subject_test.unique():
    temp2=temp1_test.loc[temp1_test['subject']==subject]
    temp2=temp2.iloc[:,:-2]
    ts=temp2.values.ravel()
    ts=pd.Series(ts - ts.mean()/ts.std()).rolling(windows).mean()[windows-1:]
    ts=np.array(ts)
    X_test.append(ts)



  df_X_train = pd.DataFrame(X_train)
  cluster_train=df_X_train.values

  df_X_test = pd.DataFrame(X_test)
  cluster_test=df_X_test.values

  km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=1, random_state=0)
  km_dtw.fit(cluster_train)

  clus_train=np.squeeze(km_dtw.cluster_centers_)

  plt.plot(np.squeeze(km_dtw.cluster_centers_).T)
  plt.title(name_df+' '+act+' train')
  plt.show()


  km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=1, random_state=0)
  km_dtw.fit(cluster_test)

  clus_test=np.squeeze(km_dtw.cluster_centers_)

  plt.plot(np.squeeze(km_dtw.cluster_centers_).T)
  plt.title(name_df+' '+act+' test')

  plt.show()

  temp_dtw=dtw(clus_train,clus_test)
  dtw_array.append(temp_dtw)
print(temp_dtw)

"""#WALKING DOWNSTAIRS"""

act='WALKING_DOWNSTAIRS'
windows = 100
dtw_array=[]
for name_df,df in dict_dfs.items():
  X_train=[]
  X_test=[]
  temp_train=df
  temp_test=dict_dfs_test[name_df+'_test']

  temp1_train=temp_train.loc[temp_train['activity']==act]
  temp1_test=temp_test.loc[temp_test['activity']==act]

  for subject in subject_train.unique():
    temp2=temp1_train.loc[temp1_train['subject']==subject]
    temp2=temp2.iloc[:,:-2]
    ts=temp2.values.ravel()
    ts=pd.Series(ts - ts.mean()/ts.std()).rolling(windows).mean()[windows-1:]
    ts=np.array(ts)
    X_train.append(ts)
  
  for subject in subject_test.unique():
    temp2=temp1_test.loc[temp1_test['subject']==subject]
    temp2=temp2.iloc[:,:-2]
    ts=temp2.values.ravel()
    ts=pd.Series(ts - ts.mean()/ts.std()).rolling(windows).mean()[windows-1:]
    ts=np.array(ts)
    X_test.append(ts)



  df_X_train = pd.DataFrame(X_train)
  cluster_train=df_X_train.values

  df_X_test = pd.DataFrame(X_test)
  cluster_test=df_X_test.values

  km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=1, random_state=0)
  km_dtw.fit(cluster_train)

  clus_train=np.squeeze(km_dtw.cluster_centers_)

  plt.plot(np.squeeze(km_dtw.cluster_centers_).T)
  plt.title(name_df+' '+act+' train')
  plt.show()


  km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=1, random_state=0)
  km_dtw.fit(cluster_test)

  clus_test=np.squeeze(km_dtw.cluster_centers_)

  plt.plot(np.squeeze(km_dtw.cluster_centers_).T)
  plt.title(name_df+' '+act+' test')

  plt.show()

  temp_dtw=dtw(clus_train,clus_test)
  dtw_array.append(temp_dtw)
print(temp_dtw)

"""#SITTING"""

act='SITTING'
windows = 100
dtw_array=[]
for name_df,df in dict_dfs.items():
  X_train=[]
  X_test=[]
  temp_train=df
  temp_test=dict_dfs_test[name_df+'_test']

  temp1_train=temp_train.loc[temp_train['activity']==act]
  temp1_test=temp_test.loc[temp_test['activity']==act]

  for subject in subject_train.unique():
    temp2=temp1_train.loc[temp1_train['subject']==subject]
    temp2=temp2.iloc[:,:-2]
    ts=temp2.values.ravel()
    ts=pd.Series(ts - ts.mean()/ts.std()).rolling(windows).mean()[windows-1:]
    ts=np.array(ts)
    X_train.append(ts)
  
  for subject in subject_test.unique():
    temp2=temp1_test.loc[temp1_test['subject']==subject]
    temp2=temp2.iloc[:,:-2]
    ts=temp2.values.ravel()
    ts=pd.Series(ts - ts.mean()/ts.std()).rolling(windows).mean()[windows-1:]
    ts=np.array(ts)
    X_test.append(ts)



  df_X_train = pd.DataFrame(X_train)
  cluster_train=df_X_train.values

  df_X_test = pd.DataFrame(X_test)
  cluster_test=df_X_test.values

  km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=1, random_state=0)
  km_dtw.fit(cluster_train)

  clus_train=np.squeeze(km_dtw.cluster_centers_)

  plt.plot(np.squeeze(km_dtw.cluster_centers_).T)
  plt.title(name_df+' '+act+' train')
  plt.show()


  km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=1, random_state=0)
  km_dtw.fit(cluster_test)

  clus_test=np.squeeze(km_dtw.cluster_centers_)

  plt.plot(np.squeeze(km_dtw.cluster_centers_).T)
  plt.title(name_df+' '+act+' test')

  plt.show()

  temp_dtw=dtw(clus_train,clus_test)
  dtw_array.append(temp_dtw)
print(temp_dtw)

"""#STANDING"""

act='STANDING'
windows = 100
dtw_array=[]
for name_df,df in dict_dfs.items():
  X_train=[]
  X_test=[]
  temp_train=df
  temp_test=dict_dfs_test[name_df+'_test']

  temp1_train=temp_train.loc[temp_train['activity']==act]
  temp1_test=temp_test.loc[temp_test['activity']==act]

  for subject in subject_train.unique():
    temp2=temp1_train.loc[temp1_train['subject']==subject]
    temp2=temp2.iloc[:,:-2]
    ts=temp2.values.ravel()
    ts=pd.Series(ts - ts.mean()/ts.std()).rolling(windows).mean()[windows-1:]
    ts=np.array(ts)
    X_train.append(ts)
  
  for subject in subject_test.unique():
    temp2=temp1_test.loc[temp1_test['subject']==subject]
    temp2=temp2.iloc[:,:-2]
    ts=temp2.values.ravel()
    ts=pd.Series(ts - ts.mean()/ts.std()).rolling(windows).mean()[windows-1:]
    ts=np.array(ts)
    X_test.append(ts)



  df_X_train = pd.DataFrame(X_train)
  cluster_train=df_X_train.values

  df_X_test = pd.DataFrame(X_test)
  cluster_test=df_X_test.values

  km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=1, random_state=0)
  km_dtw.fit(cluster_train)

  clus_train=np.squeeze(km_dtw.cluster_centers_)

  plt.plot(np.squeeze(km_dtw.cluster_centers_).T)
  plt.title(name_df+' '+act+' train')
  plt.show()


  km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=1, random_state=0)
  km_dtw.fit(cluster_test)

  clus_test=np.squeeze(km_dtw.cluster_centers_)

  plt.plot(np.squeeze(km_dtw.cluster_centers_).T)
  plt.title(name_df+' '+act+' test')

  plt.show()

  temp_dtw=dtw(clus_train,clus_test)
  dtw_array.append(temp_dtw)
print(temp_dtw)

"""##Body x
###WALKING
"""

X_bodyx_walking=[]
windows = 100
temp=dict_dfs['body_x']
temp1=temp.loc[temp['activity']=='WALKING']
#X_temp=[]
for subject in subject_train.unique():
  temp2=temp1.loc[temp1['subject']==subject]
  temp2=temp2.iloc[:,:-2]
  ts=temp2.values.ravel()
  ts=pd.Series(ts - ts.mean()/ts.std()).rolling(windows).mean()[windows-1:]
  ts=np.array(ts)
  X_bodyx_walking.append(ts)
#X_temp=np.array(X_temp)
#X_bodyx.append(X_temp)
#X_bodyx=np.array(X_bodyx_standing)



df_bodyx_walking = pd.DataFrame(X_bodyx_walking)
cluster_bodyx_walking=df_bodyx_walking.values

#plt.plot(cluster_bodyx_walking.T)
#plt.ylim(-0.5,0.5)

km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=1, random_state=0)
km_dtw.fit(cluster_bodyx_walking)

clus_bodyx_walking=np.squeeze(km_dtw.cluster_centers_)

plt.plot(np.squeeze(km_dtw.cluster_centers_).T)
plt.show()

np.squeeze(km_dtw.cluster_centers_)

X_bodyx_walking=[]
windows = 100
temp=dict_dfs_test['body_x_test']
temp1=temp.loc[temp['activity']=='WALKING']
#X_temp=[]
for subject in subject_test.unique():
  temp2=temp1.loc[temp1['subject']==subject]
  temp2=temp2.iloc[:,:-2]
  ts=temp2.values.ravel()
  ts=pd.Series(ts - ts.mean()/ts.std()).rolling(windows).mean()[windows-1:]
  ts=np.array(ts)
  X_bodyx_walking.append(ts)
#X_temp=np.array(X_temp)
#X_bodyx.append(X_temp)
#X_bodyx=np.array(X_bodyx_standing)



df_bodyx_walking = pd.DataFrame(X_bodyx_walking)
cluster_bodyx_walking=df_bodyx_walking.values

#plt.plot(cluster_bodyx_walking.T)
#plt.ylim(-0.5,0.5)

km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=1, random_state=0)
km_dtw.fit(cluster_bodyx_walking)

clus_bodyx_walking_test=np.squeeze(km_dtw.cluster_centers_)

plt.plot(np.squeeze(km_dtw.cluster_centers_).T)
plt.show()

dtw(clus_bodyx_walking,clus_bodyx_walking_test)

"""###WALKING UPSTAIRS"""

X=[]
windows = 100
temp=dict_dfs['body_x']
temp1=temp.loc[temp['activity']=='WALKING_UPSTAIRS']

for subject in subject_train.unique():
  temp2=temp1.loc[temp1['subject']==subject]
  temp2=temp2.iloc[:,:-2]
  ts=temp2.values.ravel()
  ts=pd.Series(ts - ts.mean()/ts.std()).rolling(windows).mean()[windows-1:]
  ts=np.array(ts)
  X.append(ts)



df_X = pd.DataFrame(X)
cluster_train=df_X.values

km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=1, random_state=0)
km_dtw.fit(cluster_train)

clus_train=np.squeeze(km_dtw.cluster_centers_)

plt.plot(np.squeeze(km_dtw.cluster_centers_).T)
plt.show()



X=[]
windows = 100
temp=dict_dfs_test['body_x_test']
temp1=temp.loc[temp['activity']=='WALKING_UPSTAIRS']

for subject in subject_test.unique():
  temp2=temp1.loc[temp1['subject']==subject]
  temp2=temp2.iloc[:,:-2]
  ts=temp2.values.ravel()
  ts=pd.Series(ts - ts.mean()/ts.std()).rolling(windows).mean()[windows-1:]
  ts=np.array(ts)
  X.append(ts)



df_X = pd.DataFrame(X)
cluster_test=df_X.values

km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=1, random_state=0)
km_dtw.fit(cluster_test)

clus_test=np.squeeze(km_dtw.cluster_centers_)

plt.plot(np.squeeze(km_dtw.cluster_centers_).T)
plt.show()

dtw(clus_train,clus_test)

"""###WALKING DOWNSTAIRS"""

X_bodyx_standing=[]
temp=dict_dfs['body_x']
temp1=temp.loc[temp['activity']=='WALKING_DOWNSTAIRS']
#X_temp=[]
for subject in subject_train.unique():
  temp2=temp1.loc[temp1['subject']==subject]
  temp2=temp2.iloc[:,:-2]
  ts=temp2.values.ravel()
  X_bodyx_standing.append(ts)
#X_temp=np.array(X_temp)
#X_bodyx.append(X_temp)
X_bodyx=np.array(X_bodyx_standing)

df_ts_prova = pd.DataFrame(X_bodyx_standing)
X_cluster_prova=df_ts_prova.values
km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=5, random_state=0)
km_dtw.fit(X_cluster_prova)

plt.plot(np.squeeze(km_dtw.cluster_centers_).T)
plt.show()

"""###SITTING"""

X_bodyx_standing=[]
temp=dict_dfs['body_x']
temp1=temp.loc[temp['activity']=='SITTING']
#X_temp=[]
for subject in subject_train.unique():
  temp2=temp1.loc[temp1['subject']==subject]
  temp2=temp2.iloc[:,:-2]
  ts=temp2.values.ravel()
  X_bodyx_standing.append(ts)
#X_temp=np.array(X_temp)
#X_bodyx.append(X_temp)
X_bodyx=np.array(X_bodyx_standing)

df_ts_prova = pd.DataFrame(X_bodyx_standing)
X_cluster_prova=df_ts_prova.values
km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=5, random_state=0)
km_dtw.fit(X_cluster_prova)

plt.plot(np.squeeze(km_dtw.cluster_centers_).T)
plt.show()

"""### Standing"""

X_bodyx_standing=[]
temp=dict_dfs['body_x']
#for activity in [activities[k] for k in range(1,6)]:
temp1=temp.loc[temp['activity']=='STANDING']
#X_temp=[]
for subject in subject_train.unique():
  temp2=temp1.loc[temp1['subject']==subject]
  temp2=temp2.iloc[:,:-2]
  ts=temp2.values.ravel()
  X_bodyx_standing.append(ts)
#X_temp=np.array(X_temp)
#X_bodyx.append(X_temp)
X_bodyx=np.array(X_bodyx_standing)

df_ts_prova = pd.DataFrame(X_bodyx_standing)

X_cluster_prova=df_ts_prova.values

km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=5, random_state=0)
km_dtw.fit(X_cluster_prova)

plt.plot(np.squeeze(km_dtw.cluster_centers_).T)
plt.show()

"""##BODY Y
###WALKING
"""

X_bodyx_standing=[]
temp=dict_dfs['body_y']
temp1=temp.loc[temp['activity']=='WALKING']
#X_temp=[]
for subject in subject_train.unique():
  temp2=temp1.loc[temp1['subject']==subject]
  temp2=temp2.iloc[:,:-2]
  ts=temp2.values.ravel()
  X_bodyx_standing.append(ts)
#X_temp=np.array(X_temp)
#X_bodyx.append(X_temp)
X_bodyx=np.array(X_bodyx_standing)

df_ts_prova = pd.DataFrame(X_bodyx_standing)
X_cluster_prova=df_ts_prova.values
km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=5, random_state=0)
km_dtw.fit(X_cluster_prova)

plt.plot(np.squeeze(km_dtw.cluster_centers_).T)
plt.show()

"""###WALKING UPSTAIRS"""

X_bodyx_standing=[]
temp=dict_dfs['body_y']
temp1=temp.loc[temp['activity']=='WALKING_UPSTAIRS']
#X_temp=[]
for subject in subject_train.unique():
  temp2=temp1.loc[temp1['subject']==subject]
  temp2=temp2.iloc[:,:-2]
  ts=temp2.values.ravel()
  X_bodyx_standing.append(ts)
#X_temp=np.array(X_temp)
#X_bodyx.append(X_temp)
X_bodyx=np.array(X_bodyx_standing)

df_ts_prova = pd.DataFrame(X_bodyx_standing)
X_cluster_prova=df_ts_prova.values
km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=5, random_state=0)
km_dtw.fit(X_cluster_prova)

plt.plot(np.squeeze(km_dtw.cluster_centers_).T)
plt.show()

"""###WALKING DOWNSTAIRS"""

X_bodyx_standing=[]
temp=dict_dfs['body_y']
temp1=temp.loc[temp['activity']=='WALKING_DOWNSTAIRS']
#X_temp=[]
for subject in subject_train.unique():
  temp2=temp1.loc[temp1['subject']==subject]
  temp2=temp2.iloc[:,:-2]
  ts=temp2.values.ravel()
  X_bodyx_standing.append(ts)
#X_temp=np.array(X_temp)
#X_bodyx.append(X_temp)
X_bodyx=np.array(X_bodyx_standing)

df_ts_prova = pd.DataFrame(X_bodyx_standing)
X_cluster_prova=df_ts_prova.values
km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=5, random_state=0)
km_dtw.fit(X_cluster_prova)

plt.plot(np.squeeze(km_dtw.cluster_centers_).T)
plt.show()

"""###SITTING"""

X_bodyx_standing=[]
temp=dict_dfs['body_y']
temp1=temp.loc[temp['activity']=='SITTING']
#X_temp=[]
for subject in subject_train.unique():
  temp2=temp1.loc[temp1['subject']==subject]
  temp2=temp2.iloc[:,:-2]
  ts=temp2.values.ravel()
  X_bodyx_standing.append(ts)
#X_temp=np.array(X_temp)
#X_bodyx.append(X_temp)
X_bodyx=np.array(X_bodyx_standing)

df_ts_prova = pd.DataFrame(X_bodyx_standing)
X_cluster_prova=df_ts_prova.values
km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=5, random_state=0)
km_dtw.fit(X_cluster_prova)

plt.plot(np.squeeze(km_dtw.cluster_centers_).T)
plt.show()

"""###STANDING"""

X_bodyx_standing=[]
temp=dict_dfs['body_y']
temp1=temp.loc[temp['activity']=='STANDING']
#X_temp=[]
for subject in subject_train.unique():
  temp2=temp1.loc[temp1['subject']==subject]
  temp2=temp2.iloc[:,:-2]
  ts=temp2.values.ravel()
  X_bodyx_standing.append(ts)
#X_temp=np.array(X_temp)
#X_bodyx.append(X_temp)
X_bodyx=np.array(X_bodyx_standing)

df_ts_prova = pd.DataFrame(X_bodyx_standing)
X_cluster_prova=df_ts_prova.values
km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=5, random_state=0)
km_dtw.fit(X_cluster_prova)

plt.plot(np.squeeze(km_dtw.cluster_centers_).T)
plt.show()

"""##BODY Z
###WALKING
"""

X_bodyx_standing=[]
temp=dict_dfs['body_z']
temp1=temp.loc[temp['activity']=='WALKING']
#X_temp=[]
for subject in subject_train.unique():
  temp2=temp1.loc[temp1['subject']==subject]
  temp2=temp2.iloc[:,:-2]
  ts=temp2.values.ravel()
  X_bodyx_standing.append(ts)
#X_temp=np.array(X_temp)
#X_bodyx.append(X_temp)
X_bodyx=np.array(X_bodyx_standing)

df_ts_prova = pd.DataFrame(X_bodyx_standing)
X_cluster_prova=df_ts_prova.values
km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=5, random_state=0)
km_dtw.fit(X_cluster_prova)

plt.plot(np.squeeze(km_dtw.cluster_centers_).T)
plt.show()

"""###WALKING UPSTAIRS"""

X_bodyx_standing=[]
temp=dict_dfs['body_z']
temp1=temp.loc[temp['activity']=='WALKING_UPSTAIRS']
#X_temp=[]
for subject in subject_train.unique():
  temp2=temp1.loc[temp1['subject']==subject]
  temp2=temp2.iloc[:,:-2]
  ts=temp2.values.ravel()
  X_bodyx_standing.append(ts)
#X_temp=np.array(X_temp)
#X_bodyx.append(X_temp)
X_bodyx=np.array(X_bodyx_standing)

df_ts_prova = pd.DataFrame(X_bodyx_standing)
X_cluster_prova=df_ts_prova.values
km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=5, random_state=0)
km_dtw.fit(X_cluster_prova)

plt.plot(np.squeeze(km_dtw.cluster_centers_).T)
plt.show()

"""###WALKING DOWNSTAIRS"""

X_bodyx_standing=[]
temp=dict_dfs['body_z']
temp1=temp.loc[temp['activity']=='WALKING_DOWNSTAIRS']
#X_temp=[]
for subject in subject_train.unique():
  temp2=temp1.loc[temp1['subject']==subject]
  temp2=temp2.iloc[:,:-2]
  ts=temp2.values.ravel()
  X_bodyx_standing.append(ts)
#X_temp=np.array(X_temp)
#X_bodyx.append(X_temp)
X_bodyx=np.array(X_bodyx_standing)

df_ts_prova = pd.DataFrame(X_bodyx_standing)
X_cluster_prova=df_ts_prova.values
km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=5, random_state=0)
km_dtw.fit(X_cluster_prova)

plt.plot(np.squeeze(km_dtw.cluster_centers_).T)
plt.show()

"""###SITTING
#ALTRO
Partendo dai dataframe appena definiti, creiamo un dataset di time series come di seguito mostrato. Ciascuno dei 21 soggetti nel train set svolge 5 attività differenti, quindi per ogni colonna avremo $21\cdot5=105$ time series.
| index | body_x | body_y | body_z | gyro_x | gyro_y | gyro_z | subject | activity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | TS | TS | TS | TS | TS | TS | 1 | 'WALKING' |
| 1 | TS | TS | TS | TS | TS | TS | 1 | 'WALKING_UPSTAIRS' |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |
| 4 | TS | TS | TS | TS | TS | TS | 1 | 'STANDING' |
| 5 | TS | TS | TS | TS | TS | TS | 2 | 'WALKING' |
| 6 | TS | TS | TS | TS | TS | TS | 2 | 'WALKING_UPSTAIRS' |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |
| 9 | TS | TS | TS | TS | TS | TS | 2 | 'STANDING' |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |
Per costruire questa tabella, creiamo prima il dizionario associato
"""

dict_dfs_ts = {name_df: [] for name_df in dict_dfs}
dict_dfs_ts['subject'] = []
dict_dfs_ts['activity'] = []
for name_df, df in dict_dfs.items():
    for subject in subject_train.unique():
        for activity in [activities[k] for k in range(1,6)]: 
            # non consideriamo LAYING
            mask = (df['activity'] == activity) & (df['subject'] == subject)
            time_series = df.iloc[mask.values, :-2].values.ravel()
            dict_dfs_ts[name_df].append(time_series)
            # all'ultima iterazione del lool più esterno ci salviamo anche
            # gli ID dei soggetti e le attività nell'ordine di comparizione
            if name_df == 'gyro_z':
                dict_dfs_ts['subject'].append(subject) 
                dict_dfs_ts['activity'].append(activity)

df_ts = pd.DataFrame(dict_dfs_ts)











df_ts = pd.DataFrame(dict_dfs_ts)



# with open('df_ts.pkl', 'wb') as f:
#         pickle.dump(df_ts, f)

# with open('df_ts.pkl', 'rb') as f:
#     df_ts = pickle.load(f)

"""Facciamo la stessa cosa per il test set"""

dict_dfs_test = {'body_x': body_x_test,
                 'body_y': body_y_test,
                 'body_z': body_z_test,
                 'acc_x': acc_x_test,
                 'acc_y': acc_y_test,
                 'acc_z': acc_z_test,
                 'gyro_x': gyro_x_test,
                 'gyro_y': gyro_y_test,
                 'gyro_z': gyro_z_test}

for name_df, df in dict_dfs_test.items():
    last_row = df.iloc[-1:,64:]
    last_row.columns = np.arange(64) # rename columns of the last raw
    first64 = df.iloc[:,:64]
    dict_dfs_test[name_df] = pd.concat([first64, last_row], ignore_index=True)
    # aggiungiamo anche le colonne ID soggetto e tipo di attività svolta
    dict_dfs_test[name_df]['subject'] = subject_test
    dict_dfs_test[name_df]['activity'] = y_train_mapped
    dict_dfs_test[name_df].iloc[-1, -2:] = dict_dfs_test[name_df].iloc[-2, -2:]
    dict_dfs_test[name_df]['subject'] = dict_dfs_test[name_df]['subject'].astype(int)
    
dict_dfs_ts_test = {name_df: [] for name_df in dict_dfs_test}
dict_dfs_ts_test['subject'] = []
dict_dfs_ts_test['activity'] = []
for name_df, df in dict_dfs_test.items():
    for subject in subject_test.unique():
        for activity in [activities[k] for k in range(1,6)]: 
            # non consideriamo LAYING
            mask = (df['activity'] == activity) & (df['subject'] == subject)
            time_series = df.iloc[mask.values, :-2].values.ravel()
            dict_dfs_ts_test[name_df].append(time_series)
            # all'ultima iterazione del lool più esterno ci salviamo anche
            # gli ID dei soggetti e le attività nell'ordine di comparizione
            if name_df == 'gyro_z':
                dict_dfs_ts_test['subject'].append(subject) 
                dict_dfs_ts_test['activity'].append(activity)
                
df_ts_test = pd.DataFrame(dict_dfs_ts_test)
print(df_ts_test.shape)
df_ts_test

# with open('df_ts_test.pkl', 'wb') as f:
#         pickle.dump(df_ts_test, f)

"""Proviamo a plottare tutte le TS del record 0 (soggetto 1, attività `WALKING`))"""

df_ts.columns

plt.figure(figsize=(15,15), tight_layout=True)
record_idx = 102
subj_id, act = df_ts.iloc[record_idx, -2:].values
plt.suptitle(f'Subject = {subj_id}, Activity = {act}\n')
for i, TS in enumerate(df_ts.iloc[record_idx, :-2], 1):
    plt.subplot(9,1,i)
    plt.plot(TS)
    title = df_ts.columns[i-1]
    plt.title(title)
    plt.ylim(-2,2)
plt.show()

# test set 

# plt.figure(figsize=(15,15), tight_layout=True)
# for i, TS in enumerate(df_ts.iloc[0, :-2], 1):
#     plt.subplot(6,1,i)
#     plt.plot(TS)
#     title = df_ts.columns[i-1]
#     plt.title(title)
#     plt.ylim(-2,2)
# plt.show()

# media mobile 

plt.figure(figsize=(15,15), tight_layout=True)
window = 5
record_idx = 102
subj_id, act = df_ts.iloc[record_idx, -2:].values
plt.suptitle(f'Subject = {subj_id}, Activity = {act}\n')
for i, TS in enumerate(df_ts.iloc[record_idx, :-2], 1):
    plt.subplot(6,1,i)
    plt.plot(pd.Series(TS).rolling(window).mean()[window-1:])
    title = df_ts.columns[i-1]
    plt.title(title)
    plt.ylim(-2,2)
plt.show()

plt.figure(figsize=(15,50), tight_layout=True)
windows = 100
for act in [activities[k] for k in range(1,6)]:
    mask = df_ts['activity'] == act
    for i, col in enumerate(df_ts.columns[:-2], 1):
        plt.subplot(30,1,i)
        plt.title(act + ' ' + col)
        for ts in df_ts.loc[mask, col].values:        
            #new_ts= ts - ts.mean()/ts.std()).rolling(windows).mean()[windows-1:]   
            plt.plot(pd.Series(ts - ts.mean()/ts.std()).rolling(windows).mean()[windows-1:])
        #plt.ylim(-2,2)
plt.show()

mask = df_ts['activity'] == 'WALKING'
ts_body_x = df_ts.loc[mask,'body_x'].values

from itertools import combinations
from tslearn.metrics import dtw, dtw_path, cdist_dtw, subsequence_cost_matrix

len(list(combinations(ts_body_x, 2)))

summation = 0
for ts1, ts2 in combinations(ts_body_x, 2):
    dtw_dist = dtw(ts1, ts2)
    summation += dtw_dist
summation/210







"""---
#Classic Time Series
"""

file = [body_x, body_y, body_z, gyro_x, gyro_y, gyro_z]
X_train = list()
for df in file:
    X_train.append(df.values[:, :, np.newaxis])
X_train = np.concatenate(X_train, axis=2)

X_train = np.array(X_train)

X_train.shape

pd.DataFrame(X_train[1])

from pyts.classification import KNeighborsClassifier
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix

X_train.shape

y_train

body_x

dict_dfs['body_x'].values[:,:-2].shape

"""#Approximation"""

from pyts.approximation import DiscreteFourierTransform

"""#Clustering"""

!pip install tslearn

from tslearn.clustering import TimeSeriesKMeans, silhouette_score
from tslearn.generators import random_walks

df_train=dict_dfs['body_x']

df_train = df_train.iloc[:, :-2]
X_train_64=df_train.values

X_train_64.shape

plt.plot(X_train_64.T)
plt.show()

km = TimeSeriesKMeans(n_clusters=9, metric="euclidean", max_iter=5, random_state=0)
km.fit(X_train_64)

km.cluster_centers_.shape

plt.plot(np.squeeze(km.cluster_centers_).T)
plt.show()

sil_array=[]

for i in range(3,100):
  km = TimeSeriesKMeans(n_clusters=i, metric="euclidean", max_iter=5, random_state=0)
  km.fit(X_train_64)
  labels=km.labels_
  sil=silhouette_score(X_train_64, labels, metric="euclidean")  # doctest: +ELLIPSIS
  sil_array.append(sil)
  print(i,sil)

plt.plot(sil_array)

km_dtw = TimeSeriesKMeans(n_clusters=6, metric="dtw", max_iter=5, random_state=0)
km_dtw.fit(X_train_64)

labels=km_dtw.labels_
print(silhouette_score(X_train_64, labels, metric="dtw"))

plt.plot(np.squeeze(km_dtw.cluster_centers_).T)
plt.show()

from tslearn.piecewise import PiecewiseAggregateApproximation
from tslearn.piecewise import SymbolicAggregateApproximation
from tslearn.piecewise import OneD_SymbolicAggregateApproximation

n_paa_segments = 10
paa = PiecewiseAggregateApproximation(n_segments=n_paa_segments)
X_paa = paa.fit_transform(X_train_64)

plt.plot(X_paa.reshape(X_paa.shape[1], X_paa.shape[0]))
plt.show()

km = TimeSeriesKMeans(n_clusters=9, metric="euclidean", max_iter=5, random_state=0)
km.fit(X_paa)

plt.plot(km.cluster_centers_.reshape(X_paa.shape[1], 9))
plt.show()





















dict_dfs['gyro_y'].values[:-1,:-2].shape





clf = KNeighborsClassifier(p=2, weights= 'distance')#metric='dtw_sakoechiba'
clf.fit(dict_dfs['gyro_y'].values[:-1,:-2], y_train.values)

y_pred = clf.predict(dict_dfs_test['gyro_y'].values[:-1,:-2])

print(classification_report(y_test.values, y_pred))

import seaborn as sns

sns.heatmap(confusion_matrix(y_test, y_pred), annot = True, fmt='.2g')

confusion_matrix(y_test, y_pred)

clf = KNeighborsClassifier(n_neighbors=100, p=2, n_jobs=-1)#metric='dtw_sakoechiba'
clf.fit(body_x.values, y_train.values)

y_pred = clf.predict(body_x_test.values)

print(classification_report(y_test.values, y_pred))

clf = KNeighborsClassifier(n_neighbors=3, metric='dtw_sakoechiba', metric_params = {'window_size':0.01},  n_jobs=-1)#metric='dtw_sakoechiba'
clf.fit(body_x.values, y_train.values)

y_pred = clf.predict(body_x_test.values)

print(classification_report(y_test.values, y_pred))

dict_dfs['body_x']

clf = KNeighborsClassifier(metric='dtw_sakoechiba', n_jobs = -1)
clf.fit(body_x.values, y_train.values)

y_pred = clf.predict(body_x_test.values)

print(classification_report(y_test.values, y_pred))





y_train_ts = np.array(dict_dfs_ts['activity'], dtype=object)
y_test_ts = np.array(dict_dfs_ts_test['activity'], dtype=object)
X_train_ts = np.array(dict_dfs_ts['body_x'], dtype=object)
X_test_ts = np.array(dict_dfs_ts_test['body_x'], dtype=object)

clf = KNeighborsClassifier(n_neighbors=100, p=2, n_jobs=-1)#metric='dtw_sakoechiba'
clf.fit(X_train_ts, y_train_ts)

y_pred = clf.predict(X_test_ts)

print(classification_report(y_test_ts, y_pred))

