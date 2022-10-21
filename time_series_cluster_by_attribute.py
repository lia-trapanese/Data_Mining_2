import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# import pickle

!pip install tslearn

!pip install pyts

from tslearn.metrics import dtw, dtw_path, cdist_dtw, subsequence_cost_matrix

from tslearn.clustering import TimeSeriesKMeans, silhouette_score
from tslearn.generators import random_walks

from tslearn.piecewise import PiecewiseAggregateApproximation
from tslearn.piecewise import SymbolicAggregateApproximation
from tslearn.piecewise import OneD_SymbolicAggregateApproximation

from pyts.approximation import DiscreteFourierTransform

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

#acc_x = pd.read_fwf("total_acc_x_train.txt", header = None)
#acc_y = pd.read_fwf("total_acc_y_train.txt", header = None)
#acc_z = pd.read_fwf("total_acc_z_train.txt", header = None)

gyro_x = pd.read_fwf("body_gyro_x_train.txt", header = None)
gyro_y = pd.read_fwf("body_gyro_y_train.txt", header = None)
gyro_z = pd.read_fwf("body_gyro_z_train.txt", header = None)

body_x_test = pd.read_fwf("body_acc_x_test.txt", header = None)
body_y_test = pd.read_fwf("body_acc_y_test.txt", header = None)
body_z_test = pd.read_fwf("body_acc_z_test.txt", header = None)

#acc_x_test = pd.read_fwf("total_acc_x_test.txt", header = None)
#acc_y_test = pd.read_fwf("total_acc_y_test.txt", header = None)
#acc_z_test = pd.read_fwf("total_acc_z_test.txt", header = None)

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

# code derived from https://pyts.readthedocs.io/en/stable/auto_examples/approximation/plot_dft.html
def dft_inverse_trasform(X_dft, n_coefs, n_timestamps):
    # Compute the inverse transformation
    n_samples = X_dft.shape[0]
    if n_coefs % 2 == 0:
        real_idx = np.arange(1, n_coefs, 2)
        imag_idx = np.arange(2, n_coefs, 2)
        X_dft_new = np.c_[
            X_dft[:, :1],
            X_dft[:, real_idx] + 1j * np.c_[X_dft[:, imag_idx],
                                            np.zeros((n_samples, ))]
        ]
    else:
        real_idx = np.arange(1, n_coefs, 2)
        imag_idx = np.arange(2, n_coefs + 1, 2)
        X_dft_new = np.c_[
            X_dft[:, :1],
            X_dft[:, real_idx] + 1j * X_dft[:, imag_idx]
        ]
    X_irfft = np.fft.irfft(X_dft_new, n_timestamps)
    return X_irfft

def clean_dataset(df):
    assert isinstance(df, pd.DataFrame), "df needs to be a pd.DataFrame"
    df.dropna(inplace=True)
    indices_to_keep = ~df.isin([np.nan, np.inf, -np.inf]).any(1)
    return df[indices_to_keep].astype(np.float64)

"""#Classic TS Cluster
##concatenate a 64
###KMeans
"""

file = [body_x, body_y, body_z, gyro_x, gyro_y, gyro_z]
X_train = list()
for df in file:
    X_train.append(df.values[:, :, np.newaxis])
X_train = np.concatenate(X_train, axis=2)
X_train = np.array(X_train)
df_train=dict_dfs['body_x']
df_train = df_train.iloc[:, :-2]
X_train_64=df_train.values

plt.plot(X_train_64.T)

plt.xlabel('Timestamp')
plt.ylabel('body_x [g]')
plt.savefig('X_64.pdf', bbox_inches = 'tight')

plt.show()

sil_array=[]
for i in range(3,70):
  km = TimeSeriesKMeans(n_clusters=i, metric="euclidean", max_iter=1, random_state=0)
  km.fit(X_train_64)
  labels=km.labels_
  sil=silhouette_score(X_train_64, labels, metric="euclidean")  # doctest: +ELLIPSIS
  sil_array.append(sil)
  print(i,sil)

plt.plot(np.linspace(3,69,67),sil_array)
plt.xlabel('Number of clusters')
plt.ylabel('Silhouette Score')
plt.axvline(x = 51, color='r', label = 'maximum')
plt.savefig('X_64_silhouette_euc.pdf', bbox_inches = 'tight')

km = TimeSeriesKMeans(n_clusters=51, metric="euclidean", max_iter=5, random_state=0)
km.fit(X_train_64)

plt.plot(np.squeeze(km.cluster_centers_).T)
plt.xlabel('Timestamp')
plt.ylabel('body_x [g]')
plt.savefig('X_64_51_cluster.pdf', bbox_inches = 'tight')
plt.show()

sil_array=[]
for i in range(3,50):
  km = TimeSeriesKMeans(n_clusters=i, metric="dtw", max_iter=1, random_state=0)
  km.fit(X_train_64)
  labels=km.labels_
  sil=silhouette_score(X_train_64, labels, metric="euclidean")  # doctest: +ELLIPSIS
  sil_array.append(sil)
  print(i,sil)

plt.plot(np.linspace(3,30,28),sil_array)
plt.xlabel('Number of clusters')
plt.ylabel('Silhouette Score')
plt.axvline(x = 19, color='r', label = 'maximum')

km = TimeSeriesKMeans(n_clusters=18, metric="dtw", max_iter=5, random_state=0)
km.fit(X_train_64)

plt.plot(np.squeeze(km.cluster_centers_).T)
plt.xlabel('Timestamp')
plt.ylabel('body_x [g]')
plt.savefig('X_64_18_cluster_dtw.pdf', bbox_inches = 'tight')
plt.show()

km_dtw = TimeSeriesKMeans(n_clusters=6, metric="dtw", max_iter=5, random_state=0)
km_dtw.fit(X_train_64)

labels=km_dtw.labels_
print(silhouette_score(X_train_64, labels, metric="euclidean"))

"""##Approximated KMeans"""

#PIECEWISE


n_paa_segments =10
paa = PiecewiseAggregateApproximation(n_segments=n_paa_segments)
X_paa = paa.fit_transform(X_train_64)

#plt.plot(X_paa.reshape(X_paa.shape[1], X_paa.shape[0]))
#plt.show()

#km = TimeSeriesKMeans(n_clusters=9, metric="euclidean", max_iter=5, random_state=0)
#km.fit(X_paa)
#
#plt.plot(km.cluster_centers_.reshape(X_paa.shape[1], 9))
#plt.show()

sil_array=[]
for i in range(3,36):
  km = TimeSeriesKMeans(n_clusters=i, metric="dtw", max_iter=1, random_state=0)
  km.fit(X_paa)
  labels=km.labels_
  sil=silhouette_score(X_paa, labels, metric="euclidean")  # doctest: +ELLIPSIS
  sil_array.append(sil)
  print(i,sil)

plt.plot(np.linspace(3,36,34),sil_array)
plt.xlabel('Number of clusters')
plt.ylabel('Silhouette Score')
plt.axvline(x = 21, color='r', label = 'maximum')

plt.plot(X_paa.reshape(X_paa.shape[1], X_paa.shape[0]))
plt.xlabel('Timestamp')
plt.ylabel('body_x [g]')
plt.savefig('X_PAA.pdf', bbox_inches = 'tight')
plt.show()

km = TimeSeriesKMeans(n_clusters=21, metric="dtw", max_iter=1, random_state=0)
km.fit(X_paa)

plt.plot(km.cluster_centers_.reshape(X_paa.shape[1], 21))
plt.xlabel('Timestamp')
plt.ylabel('body_x [g]')
plt.savefig('X_PAA_21_cluster.pdf', bbox_inches = 'tight')
plt.show()

# SAX transform
n_sax_symbols = 8
sax = SymbolicAggregateApproximation(n_segments=n_paa_segments, alphabet_size_avg=n_sax_symbols)
ts_sax = sax.fit_transform(X_train_64)

sil_array=[]
for i in range(2,20):
  km = TimeSeriesKMeans(n_clusters=i, metric="dtw", max_iter=1, random_state=0)
  km.fit(ts_sax)
  labels=km.labels_
  sil=silhouette_score(ts_sax, labels, metric="euclidean")  # doctest: +ELLIPSIS
  sil_array.append(sil)
  print(i,sil)

plt.plot(np.linspace(2,20,18),sil_array)
plt.xlabel('Number of clusters')
plt.ylabel('Silhouette Score')
plt.axvline(x = 3, color='r', label = 'maximum')

plt.plot(ts_sax.reshape(ts_sax.shape[1], ts_sax.shape[0]))
plt.xlabel('Timestamp')
plt.ylabel('body_x [g]')
plt.savefig('X_SAX.pdf', bbox_inches = 'tight')
plt.show()

km = TimeSeriesKMeans(n_clusters=3, metric="euclidean", max_iter=1, random_state=0)
km.fit(ts_sax)

plt.plot(km.cluster_centers_.reshape(ts_sax.shape[1], 3))
plt.xlabel('Timestamp')
plt.ylabel('body_x [g]')
plt.savefig('X_SAX_3_cluster.pdf', bbox_inches = 'tight')
plt.show()

"""#64 non concatenate, multidimensionali"""

file = [body_x, body_y, body_z,  gyro_x, gyro_y, gyro_z]
X_train = list()
for df in file:
    X_train.append(df.values[:, :, np.newaxis])
X_train = np.concatenate(X_train, axis=2)
X_train = np.array(X_train)

X_train.shape

km_dtw = TimeSeriesKMeans(n_clusters=6, metric="dtw", max_iter=5, random_state=0)
km_dtw.fit(X_train)
clus_test=np.squeeze(km_dtw.cluster_centers_)
labels=km_dtw.labels_

silhouette_score(X_train, labels, metric="euclidean")  # doctest: +ELLIPSIS

"""#DTW fra train e test per singoli cluster"""

#act='WALKING'
windows = 10

n_coefs = 500

dft = DiscreteFourierTransform(n_coefs=n_coefs)

dtw_arr_tot=[]

for act in [activities[k] for k in range(1,7)]: 
  dtw_array=[]
  for name_df,df in dict_dfs.items():
    X_train=[]
    X_test=[]
    temp_train=df
    temp_test=dict_dfs_test[name_df+'_test']
    #temp_train=clean_dataset(temp_train)
    #temp_test=clean_dataset(temp_test)
    temp1_train=temp_train.loc[temp_train['activity']==act]
    temp1_test=temp_test.loc[temp_test['activity']==act]

    for subject in subject_train.unique():
      temp2 = temp1_train.loc[temp1_train['subject']==subject]
      temp2 = temp2.iloc[:,:-2]
      temp2 = clean_dataset(temp2)
      ts1 = temp2.values.ravel()
      ts = dft.fit_transform(ts1.reshape(1, -1))
      #ts = dft_inverse_trasform(ts_dft, n_coefs=n_coefs, n_timestamps=len(ts))
      ts=ts.ravel()
      ts=pd.Series(ts - ts.mean()/ts.std()).rolling(windows).mean()[windows-1:]
      ts=np.array(ts.ravel())
      X_train.append(ts)

    for subject in subject_test.unique():
      temp2=temp1_test.loc[temp1_test['subject']==subject]
      temp2=temp2.iloc[:,:-2]
      temp2=clean_dataset(temp2)
      ts=temp2.values.ravel()
      ts = dft.fit_transform(ts.reshape(1, -1))
      #ts = dft_inverse_trasform(ts_dft, n_coefs=n_coefs, n_timestamps=len(ts))
      ts=ts.ravel()
      ts=pd.Series(ts - ts.mean()/ts.std()).rolling(windows).mean()[windows-1:]
      ts=np.array(ts.ravel())
      X_test.append(ts)



    df_X_train = pd.DataFrame(X_train)
    cluster_train=df_X_train.values

    df_X_test = pd.DataFrame(X_test)
    cluster_test=df_X_test.values

    km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=50, random_state=0)
    km_dtw.fit(cluster_train)

    clus_train=np.squeeze(km_dtw.cluster_centers_)


    km_dtw = TimeSeriesKMeans(n_clusters=1, metric="dtw", max_iter=50, random_state=0)
    km_dtw.fit(cluster_test)

    clus_test=np.squeeze(km_dtw.cluster_centers_)

    plt.plot(clus_train.T,label='train')
    plt.plot(clus_test.T,label='test')
    plt.xlabel('frequency [Hz]')
    plt.ylabel('TS Fourier')
    plt.legend()
    #plt.savefig('confront/'+name_df+'_'+act+'.pdf', bbox_inches='tight')

    #plt.title(name_df+' '+act)

    plt.show()

    temp_dtw=dtw(clus_train,clus_test)
    dtw_array.append(temp_dtw)
  dtw_arr_tot.append(dtw_array)

!zip -r /content/conf.zip /content/confront

from google.colab import files
files.download("/content/conf.zip")

to_df=np.array(dtw_arr_tot)

df_ao=pd.DataFrame(dtw_arr_tot,index=[activities[k] for k in range(1,7)],columns=['body_x','body_y','body_z','gyro_x','gyro_y','gyro_z'])

ax = df_ao.plot.barh()
ax.set_xlabel('DTW (train vs test)', fontweight ='bold', fontsize = 15)
ax.grid(True,axis='x')
ax.figure.savefig('histo_act_dtw.pdf', bbox_inches = 'tight')

#fig = plt.subplots(figsize =(12, 8))
df_ao.plot.barh(stacked=True)
#plt.style.use('ggplot')
#plt.ylabel('Feature', fontweight ='bold', fontsize = 15)
plt.xlabel('DTW (train vs test)', fontweight ='bold', fontsize = 15)
#plt.yticks([r + 2*barWidth for r in range(len(dtw_arr_tot[0]))],
#		['body_x','body_y','body_z','acc_x','acc_y','acc_z','gyro_x','gyro_y','gyro_z'])
plt.grid(axis = 'x')
plt.legend()

plt.savefig('histo_act.pdf', bbox_inches = 'tight')

plt.show()

# set width of bar
barWidth = 0.09
fig = plt.subplots(figsize =(12, 6))


# Set position of bar on X axis
br1 = np.arange(len(dtw_arr_tot[0]))
br2 = [x + barWidth for x in br1]
br3 = [x + barWidth for x in br2]
br4 = [x + barWidth for x in br3]
br5 = [x + barWidth for x in br4]
br6 = [x + barWidth for x in br5]
#br7 = [x + barWidth for x in br6]
#br8 = [x + barWidth for x in br7]
#br9 = [x + barWidth for x in br8]

# Make the plot
plt.bar(br1, dtw_arr_tot[0], color ='tab:blue', width = barWidth,
		edgecolor ='grey', label ='WALKING')

plt.bar(br2, dtw_arr_tot[1], color ='tab:orange', width = barWidth,
		edgecolor ='grey', label ='WALKING_UPSTAIRS')

plt.bar(br3, dtw_arr_tot[2], color ='tab:green', width =barWidth,
		edgecolor ='grey', label ='WALKING_DOWNSTAIRS')

plt.bar(br4, dtw_arr_tot[3], color ='tab:red', width = barWidth,
		edgecolor ='grey', label ='SITTING')

plt.bar(br5, dtw_arr_tot[4], color ='tab:pink', width = barWidth,
		edgecolor ='grey', label ='STANDING')

plt.bar(br6, dtw_arr_tot[5], color ='tab:brown', width = barWidth,
		edgecolor ='grey', label ='LAYING')

# Adding Xticks
plt.xlabel('Feature', fontweight ='bold', fontsize = 15)
plt.ylabel('DTW (train vs test)', fontweight ='bold', fontsize = 15)
plt.xticks([r + 2*barWidth for r in range(len(dtw_arr_tot[0]))],
		['body_x','body_y','body_z','gyro_x','gyro_y','gyro_z'])
plt.grid(axis = 'y')
plt.legend()
plt.savefig('histo_feat.pdf', bbox_inches = 'tight')
plt.show()

"""#K means multidimensionale"""

dict_dfs_ts = {name_df: [] for name_df in dict_dfs}
dict_dfs_ts['subject'] = []
dict_dfs_ts['activity'] = []
for name_df, df in dict_dfs.items():
    for subject in subject_train.unique():
        for activity in [activities[k] for k in range(1,7)]: 
            mask = (df['activity'] == activity) & (df['subject'] == subject)
            time_series = df.iloc[mask.values, :-2].values.ravel()
            dict_dfs_ts[name_df].append(time_series)
            # all'ultima iterazione del lool più esterno ci salviamo anche
            # gli ID dei soggetti e le attività nell'ordine di comparizione
            if name_df == 'gyro_z':
                dict_dfs_ts['subject'].append(subject) 
                dict_dfs_ts['activity'].append(activity)

df_ts = pd.DataFrame(dict_dfs_ts)

windows = 10

n_coefs = 500

dft = DiscreteFourierTransform(n_coefs=n_coefs)

X_train=[] #dimensioni: (105,max(TS),6)
X_test=[]
X_prova=[]

for name_df,df in dict_dfs.items():
  X_train_feat=[] #qua dentro ci vanno una cosa (105,max(TS))
  X_test_feat=[]

  for act in [activities[k] for k in range(1,7)]: 

    X_train_act=[] #qua ci va (21,max(TS)), devo concatenarli uno dopo l'altro
    X_test_act=[]
    temp_train=df
    temp_test=dict_dfs_test[name_df+'_test']

    temp1_train=temp_train.loc[temp_train['activity']==act]
    temp1_test=temp_test.loc[temp_test['activity']==act]

    for subject in subject_train.unique():
      temp2=temp1_train.loc[temp1_train['subject']==subject]
      temp2=temp2.iloc[:,:-2]
      temp2=clean_dataset(temp2)
      ts=temp2.values.ravel()
      ts=ts.ravel()
      #ts=pd.Series(ts - ts.mean()/ts.std()).rolling(windows).mean()[windows-1:]
      #ts=ts.ravel()
      ts = dft.fit_transform(ts.reshape(1, -1))
      #ts = dft_inverse_trasform(ts_dft, n_coefs=n_coefs, n_timestamps=len(ts))
      ts=ts.ravel()
      ts=pd.Series(ts - ts.mean()/ts.std()).rolling(windows).mean()[windows-1:]
      ts=np.array(ts.ravel())
      X_train_act.append(ts)

    for subject in subject_test.unique():
      temp2=temp1_test.loc[temp1_test['subject']==subject]
      temp2=temp2.iloc[:,:-2]
      temp2=clean_dataset(temp2)
      ts=temp2.values.ravel()
      ts=ts.ravel()
      #ts=pd.Series(ts - ts.mean()/ts.std()).rolling(windows).mean()[windows-1:]
      #ts=ts.ravel()
      ts = dft.fit_transform(ts.reshape(1, -1))
      ts=ts.ravel()
      ts=pd.Series(ts - ts.mean()/ts.std()).rolling(windows).mean()[windows-1:]
      #ts = dft_inverse_trasform(ts_dft, n_coefs=n_coefs, n_timestamps=len(ts))
      ts=np.array(ts.ravel())
      X_test_act.append(ts)
    X_train_feat.append(X_train_act)
    X_test_feat.append(X_test_act)
  X_train_feat=[j for sub in X_train_feat for j in sub]
  X_test_feat=[j for sub in X_test_feat for j in sub]
  X_prova_feat=np.append(X_train_feat,X_test_feat,axis=0)
  X_train.append(X_train_feat)
  X_test.append(X_test_feat)
  X_prova.append(X_prova_feat)

X_train=np.array(X_train)
X_test=np.array(X_test)
X_prova=np.array(X_prova)
#df_X_train = pd.DataFrame(X_train_act)
#cluster_train=df_X_train.values
#df_X_test = pd.DataFrame(X_test_act)
#cluster_test=df_X_test.values

X_prova=X_prova.transpose(1,2,0)

X_prova.shape

X_test=X_test.transpose(1,2,0)

X_train=X_train.transpose(1,2,0)

km_dtw = TimeSeriesKMeans(n_clusters=6, metric="dtw", max_iter=50, random_state=0)
km_dtw.fit(X_prova)
clus_test=np.squeeze(km_dtw.cluster_centers_)
labels=km_dtw.labels_

silhouette_score(X_prova, labels, metric="dtw")  # doctest: +ELLIPSIS

w=labels[0::6]
wu=labels[1::6]
wd=labels[2::6]
st=labels[3::6]
si=labels[4::6]
l=labels[5::6]

unique, counts = np.unique(w, return_counts=True)
wal=dict(zip(unique, counts))
wal_name = list(wal.keys())
wal_value = list(wal.values())


unique, counts = np.unique(wu, return_counts=True)
walup=dict(zip(unique, counts))
walup_name = list(wal.keys())
walup_value = list(wal.values())


unique, counts = np.unique(wd, return_counts=True)
waldo=dict(zip(unique, counts))
waldo_name = list(wal.keys())
waldo_value = list(wal.values())

unique, counts = np.unique(st, return_counts=True)
sta=dict(zip(unique, counts))
sta_name = list(wal.keys())
sta_value = list(wal.values())


unique, counts = np.unique(si, return_counts=True)
sit=dict(zip(unique, counts))
sit_name = list(wal.keys())
sit_value = list(wal.values())


unique, counts = np.unique(l, return_counts=True)
lay=dict(zip(unique, counts))
lay_name = list(wal.keys())
lay_value = list(wal.values())

waldo

sit

sta

lay

d = {'WALKING': [2,21,1,0,6,0], 
     'WALKING UPSTAIRS': [1,22,0,0,5,2],
     'WALKING_DOWNSTAIRS': [20,0,1,0,8,1],
     'SITTING': [1,20,0,1,8,0],
     'STANDING': [1,22,0,0,7,0],
     'LAYING': [1,20,1,0,7,1]
     }

df_vert = pd.DataFrame(data=d)
df_tra=df_vert.T

#fig = plt.subplots(figsize =(12, 8))
df_tra.plot.barh(stacked=True)
#plt.style.use('ggplot')
#plt.ylabel('Activities', fontweight ='bold', fontsize = 15)
plt.xlabel('Activities in cluster', fontweight ='bold', fontsize = 15)
#plt.yticks([r + 2*barWidth for r in range(len(dtw_arr_tot[0]))],
#		['body_x','body_y','body_z','acc_x','acc_y','acc_z','gyro_x','gyro_y','gyro_z'])

plt.legend(bbox_to_anchor=(0,1.02,1,0.2), loc="lower left",
                mode="expand", borderaxespad=0, ncol=6)
plt.grid(axis='x')
plt.savefig('histo_activity_cluster.pdf', bbox_inches = 'tight')
plt.show()

nomi_var=['body_x','body_y','body_z','gyro_x','gyro_y','gyro_z']

for index,name_df in enumerate(nomi_var):

  plt.plot(clus_test[0,:,index],label='1',linewidth=1)
  plt.plot(clus_test[1,:,index],label='2',linewidth=1)
  plt.plot(clus_test[2,:,index],label='3',linewidth=1)
  plt.plot(clus_test[3,:,index],label='4',linewidth=1)
  plt.plot(clus_test[4,:,index],label='5',linewidth=1)
  plt.plot(clus_test[5,:,index],label='6',linewidth=1)
  plt.legend(ncol=2)
  plt.xlabel('frequency [Hz]')
  plt.ylabel('TS Fourier')
  
  plt.savefig('cluster_'+name_df+'.pdf', bbox_inches = 'tight')
  plt.show()
