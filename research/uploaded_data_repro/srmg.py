import json, numpy as np, pandas as pd
from sklearn.linear_model import RidgeCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.neighbors import KNeighborsRegressor
v=pd.read_excel('/home/user/rd/uploads/dr_srmg/mvwdlno4q5gk_The data set for an industrial SRMG proce.xls',header=None)
d=v.iloc[6:].reset_index(drop=True).astype(float)
X=d.iloc[:,1:33].drop(columns=[32]).values  # all inputs + MI1, MI2 (upstream labs) excluding MI3
X=d.iloc[:,[i for i in range(1,33) if i!=32]].values; y=d.iloc[:,32].values; g=d.iloc[:,33].values.astype(int)
n=len(y); print(n, sorted(set(g)), [int((g==k).sum()) for k in sorted(set(g))])
start=int(.5*n); res={k:[] for k in ('persist_grade','persist_any','ridge','rf','jitl')}; idx=[]
for t in range(start,n):
    tr=slice(0,t); idx.append(t)
    same=np.where(g[:t]==g[t])[0]
    res['persist_grade'].append(y[same[-1]] if len(same) else y[t-1])
    res['persist_any'].append(y[t-1])
    res['ridge'].append(RidgeCV(alphas=np.logspace(-3,3,13)).fit(X[tr],y[tr]).predict(X[t:t+1])[0])
    res['rf'].append(RandomForestRegressor(100,random_state=0,n_jobs=-1).fit(X[tr],y[tr]).predict(X[t:t+1])[0])
    k=min(10,t); res['jitl'].append(KNeighborsRegressor(k,weights='distance').fit(X[tr],y[tr]).predict(X[t:t+1])[0])
idx=np.array(idx); yt=y[idx]; trans=np.r_[g[idx][0]!=g[idx[0]-1], g[idx][1:]!=g[idx][:-1]]
def met(p,m):
    p=np.array(p)[m]; t=yt[m]; e=p-t
    return dict(n=int(m.sum()),rmse=float(np.sqrt((e**2).mean())),r2=float(1-(e**2).sum()/((t-t.mean())**2).sum()) if m.sum()>2 else None,mape=float(100*np.mean(np.abs(e)/np.abs(t))))
out={'n_samples':n,'n_test':int(len(idx)),'n_transition_test':int(trans.sum()),'grades':{str(k):int((g==k).sum()) for k in sorted(set(g))},'overall':{},'transition':{},'steady':{}}
for k,p in res.items():
    out['overall'][k]=met(p,np.ones(len(idx),bool)); out['transition'][k]=met(p,trans); out['steady'][k]=met(p,~trans)
for s in ('overall','transition','steady'):
    print(s,{k:(round(m['rmse'],4),round(m['r2'],3) if m['r2'] is not None else None,round(m['mape'],1)) for k,m in out[s].items()}, out[s]['ridge']['n'])
json.dump(out,open('/home/user/rd/repro/srmg_results.json','w'),indent=1)
