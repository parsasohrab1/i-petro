import sys, json, numpy as np, pandas as pd
from sklearn.linear_model import RidgeCV
f=sys.argv[1]
df=pd.read_csv(f,skiprows=4,header=0); df.columns=['d','v']
df['d']=pd.to_datetime(df['d'],format='%m/%d/%Y'); df=df.sort_values('d').reset_index(drop=True)
y=df.v.values.astype(float); print('weeks',len(y),df.d.min().date(),df.d.max().date())
L=8; out={'weeks':len(y),'start':str(df.d.min().date()),'end':str(df.d.max().date())}
for h in (1,2,3,4):
    X=[];T=[];P=[]
    for t in range(L, len(y)-h):
        X.append(np.r_[y[t-L+1:t+1]-y[t], np.sin(2*np.pi*t/52.18), np.cos(2*np.pi*t/52.18)]); T.append(y[t+h]-y[t])
    X=np.array(X);T=np.array(T); n=len(T)
    a,b=int(.6*n),int(.8*n)
    m=RidgeCV(alphas=np.logspace(-2,6,30)).fit(X[:a],T[:a])
    r_cal=np.abs(T[a:b]-m.predict(X[a:b])); k=int(np.ceil((len(r_cal)+1)*.9)); q=np.sort(r_cal)[min(k,len(r_cal))-1]
    pt=m.predict(X[b:]); e_m=np.abs(T[b:]-pt); e_p=np.abs(T[b:])
    rm=float(np.sqrt((e_m**2).mean())); rp=float(np.sqrt((e_p**2).mean()))
    out[f'h{h}']={'rmse_ridge':rm,'rmse_persist':rp,'rmse_red_%':100*(1-rm/rp),'mae_red_%':100*(1-e_m.mean()/e_p.mean()),'cov':float((e_m<=q).mean()),'width':float(2*q),'n_test':int(n-b)}
    print(h,out[f'h{h}'])
json.dump(out,open('/home/user/rd/repro/eia_results.json','w'),indent=1)
