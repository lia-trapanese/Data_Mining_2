

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import random

from collections import defaultdict

!pip install tslearn

from tslearn.piecewise import SymbolicAggregateApproximation
from tslearn.preprocessing import TimeSeriesScalerMeanVariance

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

file = [body_x, body_y, body_z,  gyro_x, gyro_y, gyro_z]
X_train = list()
for df in file:
    X_train.append(df.values[:, :, np.newaxis])
X_train = np.concatenate(X_train, axis=2)
X_train = np.array(X_train)


file = [body_x, body_y, body_z, gyro_x, gyro_y, gyro_z]
X_train = list()
for df in file:
    X_train.append(df.values[:, :, np.newaxis])
X_train = np.concatenate(X_train, axis=2)
X_train = np.array(X_train)

def clean_dataset(df):
    assert isinstance(df, pd.DataFrame), "df needs to be a pd.DataFrame"
    df.dropna(inplace=True)
    indices_to_keep = ~df.isin([np.nan, np.inf, -np.inf]).any(1)
    return df[indices_to_keep].astype(np.float64)

"""#Transforamtion"""

!pip install prefixspan

from prefixspan import PrefixSpan

scaler = TimeSeriesScalerMeanVariance(mu=0., std=1.)  # Rescale time series
n_paa_segments = 20
n_sax_symbols = 10
sax = SymbolicAggregateApproximation(n_segments=n_paa_segments, alphabet_size_avg=n_sax_symbols)


X_train=[] #dimensioni: (105,max(TS),6)
X_test=[]
X_prova=[]

for act in [activities[k] for k in range(1,7)]:
  X_train_feat=[] #qua dentro ci vanno una cosa (105,max(TS))
  X_test_feat=[]

  for name_df,df in dict_dfs.items(): 

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
      ts = scaler.fit_transform(ts.reshape(1,-1))     
      ts = sax.fit_transform(ts)
      ts=ts.ravel()
      ts=[str(x)+'_'+name_df for x in ts]
      ts=np.array(ts)
      X_train_act.append(ts)

    for subject in subject_test.unique():
      temp2=temp1_test.loc[temp1_test['subject']==subject]
      temp2=temp2.iloc[:,:-2]
      temp2=clean_dataset(temp2)
      ts=temp2.values.ravel()
      ts = scaler.fit_transform(ts.reshape(1,-1))      
      ts = sax.fit_transform(ts)
      ts=ts.ravel()
      ts=[str(x)+'_'+name_df for x in ts]
      ts=np.array(ts)
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

X_prova.shape

X_walking=X_prova[0]
X_walking_up=X_prova[1]
X_walking_down=X_prova[2]
X_sitting=X_prova[3]
X_standing=X_prova[4]
X_laying=X_prova[5]

X_walking.shape

df = pd.DataFrame(X_walking)

df_stamp=df.head()

df_stamp2=df.tail()

print(df_stamp.to_latex())

print(df_stamp2.to_latex())



"""#WALKING"""

ps = PrefixSpan(X_walking)

for i in range(0,180):
  plt.plot(X_walking[i])
plt.xlabel('Time slot')
#plt.ylabel('TS')
frame1 = plt.gca()
#frame1.axes.xaxis.set_ticklabels([])
frame1.axes.yaxis.set_ticklabels([])
#plt.savefig('X_walking_TS.pdf', bbox_inches = 'tight')
plt.show()

ps.topk(10,filter=lambda patt, matches: len(patt) > 10)

len_pat_clo=[]
len_pat_gen=[]
len_pat=[]
for i in range(1,20):
  len_pat.append(len(ps.frequent(5, filter=lambda patt, matches: len(patt) > i)))
  len_pat_clo.append(len(ps.frequent(5, closed=True,filter=lambda patt, matches: len(patt) > i)))
  len_pat_gen.append(len(ps.frequent(5, generator=True,filter=lambda patt, matches: len(patt) > i)))

plt.plot(np.linspace(1,20,19),len_pat,label='No Constraints')
plt.plot(np.linspace(1,20,19),len_pat_clo, label='Closed')
plt.plot(np.linspace(1,20,19),len_pat_gen, label='Generator')
plt.xlabel('MinLen')
#plt.yscale('log')
plt.legend()
plt.ylabel('Frequent Patterns')
plt.savefig('MinLen_walking_up.pdf', bbox_inches = 'tight')

sup_pat_clo=[]
sup_pat_gen=[]
sup_pat=[]
for i in range(2,20):
  sup_pat_clo.append(len(ps.frequent(i, closed=True,filter=lambda patt, matches: len(patt) > 5)))
  sup_pat.append(len(ps.frequent(i,filter=lambda patt, matches: len(patt) > 5)))
  sup_pat_gen.append(len(ps.frequent(i,generator=True,filter=lambda patt, matches: len(patt) > 5)))

plt.plot(np.linspace(2,20,20-2),sup_pat,label='No Constraints')
plt.plot(np.linspace(2,20,20-2),sup_pat_clo, label='Closed')
plt.plot(np.linspace(2,20,20-2),sup_pat_gen, label='Generator')
plt.xlabel('MinSup')
#plt.yscale('log')
plt.legend()
plt.ylabel('Frequent Patterns')

"""#WALKING"""

np.random.shuffle(X_walking)
ps = PrefixSpan(X_walking)
act='walking'

print('I 10 pattern più frequenti sono:\n')

ao=ps.topk(10,filter=lambda patt, matches: len(patt) > 10)

print(*ao, sep="\n")

len_pat_clo=[]
len_pat_gen=[]
len_pat=[]
for i in range(1,20):
  len_pat.append(len(ps.frequent(5, filter=lambda patt, matches: len(patt) > i)))
  len_pat_clo.append(len(ps.frequent(5, closed=True,filter=lambda patt, matches: len(patt) > i)))
  len_pat_gen.append(len(ps.frequent(5, generator=True,filter=lambda patt, matches: len(patt) > i)))

plt.plot(np.linspace(1,20,19),len_pat,label='No Constraints')
plt.plot(np.linspace(1,20,19),len_pat_clo, label='Closed')
plt.plot(np.linspace(1,20,19),len_pat_gen, label='Generator')
plt.xlabel('MinLen')
plt.yscale('log')
plt.legend()
plt.ylabel('Frequent Patterns')
plt.show()
plt.savefig('MinLen_'+act+'.pdf', bbox_inches = 'tight')


sup_pat_clo=[]
sup_pat_gen=[]
sup_pat=[]
for i in range(2,30):
  sup_pat_clo.append(len(ps.frequent(i, closed=True,filter=lambda patt, matches: len(patt) > 5)))
  sup_pat.append(len(ps.frequent(i,filter=lambda patt, matches: len(patt) > 5)))
  sup_pat_gen.append(len(ps.frequent(i,generator=True,filter=lambda patt, matches: len(patt) > 5)))

plt.plot(np.linspace(2,30,30-2),sup_pat,label='No Constraints')
plt.plot(np.linspace(2,30,30-2),sup_pat_clo, label='Closed')
plt.plot(np.linspace(2,30,30-2),sup_pat_gen, label='Generator')
plt.xlabel('MinSup')
plt.yscale('log')
plt.legend()
plt.ylabel('Frequent Patterns')
plt.show()
plt.savefig('MinSup_'+act+'.pdf', bbox_inches = 'tight')

"""#WALKING UPSTAIRS"""

np.random.shuffle(X_walking_up)

ps = PrefixSpan(X_walking_up)
act='walking_up'

print('I 10 pattern più frequenti sono:\n')

ao=ps.topk(10,filter=lambda patt, matches: len(patt) > 10)

print(*ao, sep="\n")

len_pat_clo=[]
len_pat_gen=[]
len_pat=[]
for i in range(1,20):
  len_pat.append(len(ps.frequent(5, filter=lambda patt, matches: len(patt) > i)))
  len_pat_clo.append(len(ps.frequent(5, closed=True,filter=lambda patt, matches: len(patt) > i)))
  len_pat_gen.append(len(ps.frequent(5, generator=True,filter=lambda patt, matches: len(patt) > i)))

plt.plot(np.linspace(1,20,19),len_pat,label='No Constraints')
plt.plot(np.linspace(1,20,19),len_pat_clo, label='Closed')
plt.plot(np.linspace(1,20,19),len_pat_gen, label='Generator')
plt.xlabel('MinLen')
#plt.yscale('log')
plt.legend()
plt.ylabel('Frequent Patterns')
plt.savefig('MinLen_'+act+'.pdf', bbox_inches = 'tight')
plt.show()


sup_pat_clo=[]
sup_pat_gen=[]
sup_pat=[]
for i in range(2,30):
  sup_pat_clo.append(len(ps.frequent(i, closed=True,filter=lambda patt, matches: len(patt) > 5)))
  sup_pat.append(len(ps.frequent(i,filter=lambda patt, matches: len(patt) > 5)))
  sup_pat_gen.append(len(ps.frequent(i,generator=True,filter=lambda patt, matches: len(patt) > 5)))

plt.plot(np.linspace(2,30,30-2),sup_pat,label='No Constraints')
plt.plot(np.linspace(2,30,30-2),sup_pat_clo, label='Closed')
plt.plot(np.linspace(2,30,30-2),sup_pat_gen, label='Generator')
plt.xlabel('MinSup')
plt.yscale('log')
plt.legend()
plt.ylabel('Frequent Patterns')
plt.savefig('MinSup_'+act+'.pdf', bbox_inches = 'tight')

plt.show()



"""#WALKING DOWNSTAIRS"""

np.random.shuffle(X_walking_down)

ps = PrefixSpan(X_walking_down)
act='walking_down'

print('I 10 pattern più frequenti sono:\n')

ao=ps.topk(10,filter=lambda patt, matches: len(patt) > 10)

print(*ao, sep="\n")

len_pat_clo=[]
len_pat_gen=[]
len_pat=[]
for i in range(1,20):
  len_pat.append(len(ps.frequent(5, filter=lambda patt, matches: len(patt) > i)))
  len_pat_clo.append(len(ps.frequent(5, closed=True,filter=lambda patt, matches: len(patt) > i)))
  len_pat_gen.append(len(ps.frequent(5, generator=True,filter=lambda patt, matches: len(patt) > i)))

plt.plot(np.linspace(1,20,19),len_pat,label='No Constraints')
plt.plot(np.linspace(1,20,19),len_pat_clo, label='Closed')
plt.plot(np.linspace(1,20,19),len_pat_gen, label='Generator')
plt.xlabel('MinLen')
#plt.yscale('log')
plt.legend()
plt.ylabel('Frequent Patterns')
plt.show()
plt.savefig('MinLen_'+act+'.pdf', bbox_inches = 'tight')


sup_pat_clo=[]
sup_pat_gen=[]
sup_pat=[]
for i in range(2,30):
  sup_pat_clo.append(len(ps.frequent(i, closed=True,filter=lambda patt, matches: len(patt) > 5)))
  sup_pat.append(len(ps.frequent(i,filter=lambda patt, matches: len(patt) > 5)))
  sup_pat_gen.append(len(ps.frequent(i,generator=True,filter=lambda patt, matches: len(patt) > 5)))

plt.plot(np.linspace(2,30,30-2),sup_pat,label='No Constraints')
plt.plot(np.linspace(2,30,30-2),sup_pat_clo, label='Closed')
plt.plot(np.linspace(2,30,30-2),sup_pat_gen, label='Generator')
plt.xlabel('MinSup')
plt.yscale('log')
plt.legend()
plt.ylabel('Frequent Patterns')
plt.show()
plt.savefig('MinSup_'+act+'.pdf', bbox_inches = 'tight')



"""#SITTING"""

np.random.shuffle(X_sitting)

ps = PrefixSpan(X_sitting)
act='sitting'

print('I 10 pattern più frequenti sono:\n')

ao=ps.topk(10,filter=lambda patt, matches: len(patt) > 10)

print(*ao, sep="\n")


#len_pat_clo=[]
#len_pat_gen=[]
#len_pat=[]
#for i in range(1,20):
#  len_pat.append(len(ps.frequent(5, filter=lambda patt, matches: len(patt) > i)))
#  len_pat_clo.append(len(ps.frequent(5, closed=True,filter=lambda patt, matches: len(patt) > i)))
#  len_pat_gen.append(len(ps.frequent(5, generator=True,filter=lambda patt, matches: len(patt) > i)))
#
#plt.plot(np.linspace(1,20,19),len_pat,label='No Constraints')
#plt.plot(np.linspace(1,20,19),len_pat_clo, label='Closed')
#plt.plot(np.linspace(1,20,19),len_pat_gen, label='Generator')
#plt.xlabel('MinLen')
##plt.yscale('log')
#plt.legend()
#plt.ylabel('Frequent Patterns')
#plt.show()
#plt.savefig('MinLen_'+act+'.pdf', bbox_inches = 'tight')
#
#
#sup_pat_clo=[]
#sup_pat_gen=[]
#sup_pat=[]
#for i in range(2,30):
#  sup_pat_clo.append(len(ps.frequent(i, closed=True,filter=lambda patt, matches: len(patt) > 5)))
#  sup_pat.append(len(ps.frequent(i,filter=lambda patt, matches: len(patt) > 5)))
#  sup_pat_gen.append(len(ps.frequent(i,generator=True,filter=lambda patt, matches: len(patt) > 5)))
#
#plt.plot(np.linspace(2,30,30-2),sup_pat,label='No Constraints')
#plt.plot(np.linspace(2,30,30-2),sup_pat_clo, label='Closed')
#plt.plot(np.linspace(2,30,30-2),sup_pat_gen, label='Generator')
#plt.xlabel('MinSup')
#plt.yscale('log')
#plt.legend()
#plt.ylabel('Frequent Patterns')
#plt.show()
#plt.savefig('MinSup_'+act+'.pdf', bbox_inches = 'tight')



"""#STANDING"""

np.random.shuffle(X_standing)

ps = PrefixSpan(X_standing)
act='standing'

print('I 10 pattern più frequenti sono:\n')

ao=ps.topk(10,filter=lambda patt, matches: len(patt) > 10)

print(*ao, sep="\n")

#len_pat_clo=[]
#len_pat_gen=[]
#len_pat=[]
#for i in range(1,20):
#  len_pat.append(len(ps.frequent(5, filter=lambda patt, matches: len(patt) > i)))
#  len_pat_clo.append(len(ps.frequent(5, closed=True,filter=lambda patt, matches: len(patt) > i)))
#  len_pat_gen.append(len(ps.frequent(5, generator=True,filter=lambda patt, matches: len(patt) > i)))
#
#plt.plot(np.linspace(1,20,19),len_pat,label='No Constraints')
#plt.plot(np.linspace(1,20,19),len_pat_clo, label='Closed')
#plt.plot(np.linspace(1,20,19),len_pat_gen, label='Generator')
#plt.xlabel('MinLen')
##plt.yscale('log')
#plt.legend()
#plt.ylabel('Frequent Patterns')
#plt.show()
#plt.savefig('MinLen_'+act+'.pdf', bbox_inches = 'tight')
#
#
#sup_pat_clo=[]
#sup_pat_gen=[]
#sup_pat=[]
#for i in range(2,30):
#  sup_pat_clo.append(len(ps.frequent(i, closed=True,filter=lambda patt, matches: len(patt) > 5)))
#  sup_pat.append(len(ps.frequent(i,filter=lambda patt, matches: len(patt) > 5)))
#  sup_pat_gen.append(len(ps.frequent(i,generator=True,filter=lambda patt, matches: len(patt) > 5)))
#
#plt.plot(np.linspace(2,30,30-2),sup_pat,label='No Constraints')
#plt.plot(np.linspace(2,30,30-2),sup_pat_clo, label='Closed')
#plt.plot(np.linspace(2,30,30-2),sup_pat_gen, label='Generator')
#plt.xlabel('MinSup')
#plt.yscale('log')
#plt.legend()
#plt.ylabel('Frequent Patterns')
#plt.show()
#plt.savefig('MinSup_'+act+'.pdf', bbox_inches = 'tight')

np.random.shuffle(X_laying)

ps = PrefixSpan(X_laying)

for i in range(0,180):
  plt.plot(X_laying[i])
plt.xlabel('Time slot')
#plt.ylabel('TS')
frame1 = plt.gca()
#frame1.axes.xaxis.set_ticklabels([])
frame1.axes.yaxis.set_ticklabels([])
plt.savefig('X_laying_TS.pdf', bbox_inches = 'tight')
plt.show()

print('I 10 pattern più frequenti sono:\n')

ao=ps.topk(10,filter=lambda patt, matches: len(patt) > 10)

print(*ao, sep="\n")

#len_pat_clo=[]
#len_pat_gen=[]
#len_pat=[]
#for i in range(1,20):
#  len_pat.append(len(ps.frequent(5, filter=lambda patt, matches: len(patt) > i)))
#  len_pat_clo.append(len(ps.frequent(5, closed=True,filter=lambda patt, matches: len(patt) > i)))
#  len_pat_gen.append(len(ps.frequent(5, generator=True,filter=lambda patt, matches: len(patt) > i)))
#
#plt.plot(np.linspace(1,20,19),len_pat,label='No Constraints')
#plt.plot(np.linspace(1,20,19),len_pat_clo, label='Closed')
#plt.plot(np.linspace(1,20,19),len_pat_gen, label='Generator')
#plt.xlabel('MinLen')
##plt.yscale('log')
#plt.legend()
#plt.ylabel('Frequent Patterns')
#plt.show()
#plt.savefig('MinLen_laying.pdf', bbox_inches = 'tight')
#
#
#sup_pat_clo=[]
#sup_pat_gen=[]
#sup_pat=[]
#for i in range(2,30):
#  sup_pat_clo.append(len(ps.frequent(i, closed=True,filter=lambda patt, matches: len(patt) > 5)))
#  sup_pat.append(len(ps.frequent(i,filter=lambda patt, matches: len(patt) > 5)))
#  sup_pat_gen.append(len(ps.frequent(i,generator=True,filter=lambda patt, matches: len(patt) > 5)))
#
#plt.plot(np.linspace(2,30,30-2),sup_pat,label='No Constraints')
#plt.plot(np.linspace(2,30,30-2),sup_pat_clo, label='Closed')
#plt.plot(np.linspace(2,30,30-2),sup_pat_gen, label='Generator')
#plt.xlabel('MinSup')
#plt.yscale('log')
#plt.legend()
#plt.ylabel('Frequent Patterns')
#plt.show()
#plt.savefig('MinSup_laying.pdf', bbox_inches = 'tight')

plt.plot(np.linspace(2,30,30-2),sup_pat,label='No Constraints')
plt.plot(np.linspace(2,30,30-2),sup_pat_clo, label='Closed')
plt.plot(np.linspace(2,30,30-2),sup_pat_gen, label='Generator')
plt.xlabel('MinSup')
plt.yscale('log')
plt.legend()
plt.ylabel('Frequent Patterns')
plt.show()
plt.savefig('MinSup_walking_up.pdf', bbox_inches = 'tight')

"""#Istogrammi"""

fig, ax = plt.subplots(figsize =(6, 4))

df = pd.DataFrame([['Walking', 185, 0, 46, 0,0,0], 
                   ['Upstairs', 217, 0, 25, 0,0,0], 
                   ['Downstairs', 218, 0, 24, 0,0,0],
                   ['Sitting', 31,97,0,0,12,13],
                   ['Standing',18+16+13+12,13,0,13,17+16+14+13,0],
                   ['Laying',18+13,14*2+13,14+12*2,0,14+11,0]],
                  columns=['Activity', 'body_x', 'body_y', 'body_z', 'gyro_x','gyro_y','gyro_z'])
# view data
print(df)
  
# plot data in stack manner of bar type
df.plot(x='Activity', kind='bar', stacked=True,ax=ax)

ax.legend(ncol=2);
ax.figure.savefig('histo.pdf', bbox_inches = 'tight')

