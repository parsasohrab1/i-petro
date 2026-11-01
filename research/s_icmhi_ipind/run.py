import numpy as np, pandas as pd, json, re
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem
from sklearn.ensemble import RandomForestRegressor
RDLogger.DisableLog('rdApp.*')
d=pd.read_csv(''+__import__('sys').argv[1]+'')
def fp(s):
    m=Chem.MolFromSmiles(s)
    if m is None: return None
    v=AllChem.GetHashedMorganFingerprint(m,2,nBits=1024); a=np.zeros(1024)
    for k,c in v.GetNonzeroElements().items(): a[k]=c
    return a
X=[fp(s) for s in d.combined_mol_SMILES]; ok=[x is not None for x in X]
d=d[ok].reset_index(drop=True); X=np.array([x for x in X if x is not None]); y=d.expt_Hela.to_numpy()
lab=d.label.str.extract(r'A(\d+)B(\d+)C(\d+)').astype(int); 
def conf(split_groups, seed, alpha=0.1):
    rng=np.random.default_rng(seed); n=len(y)
    if split_groups is None:
        idx=rng.permutation(n); a,b=int(.6*n),int(.8*n); tr,ca,te=idx[:a],idx[a:b],idx[b:]
    else:
        ug=np.unique(split_groups); rng.shuffle(ug); tr=[];ca=[];te=[]
        # assign whole groups: ~60/20/20 by group count
        k=len(ug); g_tr,g_ca,g_te=ug[:int(.6*k)],ug[int(.6*k):int(.8*k)],ug[int(.8*k):]
        tr=np.where(np.isin(split_groups,g_tr))[0]; ca=np.where(np.isin(split_groups,g_ca))[0]; te=np.where(np.isin(split_groups,g_te))[0]
    m=RandomForestRegressor(200,random_state=seed,n_jobs=-1,min_samples_leaf=2).fit(X[tr],y[tr])
    r=np.sort(np.abs(y[ca]-m.predict(X[ca]))); q=r[min(int(np.ceil((len(ca)+1)*(1-alpha))),len(ca))-1]
    e=np.abs(y[te]-m.predict(X[te])); return float((e<=q).mean()), float(2*q), float(np.sqrt(np.mean((y[te]-m.predict(X[te]))**2))), len(te)
out={'n':int(len(y)),'target':'HeLa transfection (log scale)','nominal':0.9}
for name,g in (('random',None),('group_by_A_component',lab[0].to_numpy()),('group_by_B_component',lab[1].to_numpy()),('group_by_C_component',lab[2].to_numpy())):
    r=np.array([conf(g,s) for s in range(10)]); 
    out[name]={'coverage_mean':round(float(r[:,0].mean()),3),'coverage_min':round(float(r[:,0].min()),3),'coverage_max':round(float(r[:,0].max()),3),'coverage_ci95':round(float(1.96*r[:,0].std(ddof=1)/np.sqrt(10)),3),'width':round(float(r[:,1].mean()),2),'rmse':round(float(r[:,2].mean()),2),'test_n_mean':round(float(r[:,3].mean()))}
    print(name,out[name])
json.dump(out,open('agile_shift_results.json','w'),indent=1)
