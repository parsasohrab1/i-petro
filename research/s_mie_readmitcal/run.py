import numpy as np, pandas as pd, json, sys
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import roc_auc_score, brier_score_loss
from scipy.optimize import minimize_scalar
d=pd.read_csv(sys.argv[1],na_values='?')
d=d[~d.discharge_disposition_id.isin([11,13,14,19,20,21])]          # expired / hospice: cannot be readmitted
d=d.sort_values('encounter_id').drop_duplicates('patient_nbr',keep='first').reset_index(drop=True)   # one (first) encounter per patient
y=(d.readmitted=='<30').astype(int).to_numpy(); N=len(d)
num=['time_in_hospital','num_lab_procedures','num_procedures','num_medications','number_outpatient','number_emergency','number_inpatient','number_diagnoses']
cat=['race','gender','age','admission_type_id','discharge_disposition_id','admission_source_id','A1Cresult','change','diabetesMed','max_glu_serum']
d['dx1']=d.diag_1.astype(str).str[:3]; d['spec']=d.medical_specialty.fillna('NA'); 
for c in ['dx1','spec']:
    top=d[c].value_counts().index[:25]; d[c]=d[c].where(d[c].isin(top),'other')
X=pd.concat([d[num].astype(float),pd.get_dummies(d[cat+['dx1','spec']].astype(str))],axis=1).astype(float).to_numpy()
age=d.age.map(lambda a: 0 if a in('[0-10)','[10-20)','[20-30)','[30-40)','[40-50)','[50-60)') else (1 if a in('[60-70)','[70-80)') else 2)).to_numpy()
def ece(p,t,bins=15):
    b=np.minimum((p*bins).astype(int),bins-1); e=0
    for i in range(bins):
        m=b==i
        if m.any(): e+=m.mean()*abs(p[m].mean()-t[m].mean())
    return float(e)
lg=lambda p: np.log(np.clip(p,1e-6,1-1e-6)/(1-np.clip(p,1e-6,1-1e-6)))
sg=lambda z: 1/(1+np.exp(-z))
def temp(pv,yv):
    f=lambda T: -np.mean(yv*np.log(sg(lg(pv)/T)+1e-12)+(1-yv)*np.log(1-sg(lg(pv)/T)+1e-12)); T=minimize_scalar(f,bounds=(.3,5),method='bounded').x; return lambda p: sg(lg(p)/T)
def platt(pv,yv):
    m=LogisticRegression(C=1e6).fit(lg(pv)[:,None],yv); return lambda p: m.predict_proba(lg(p)[:,None])[:,1]
def iso(pv,yv):
    m=IsotonicRegression(out_of_bounds='clip',y_min=0,y_max=1).fit(pv,yv); return lambda p: m.predict(p)
res={'n_patients':int(N),'positive_rate':round(float(y.mean()),4),'seeds':10}
for mname,mk in (('logreg',lambda s: LogisticRegression(max_iter=300,C=0.1)),('hgb',lambda s: HistGradientBoostingClassifier(max_iter=150,learning_rate=0.05,max_leaf_nodes=15,random_state=s))):
    rows=[]
    for s in range(10):
        rng=np.random.default_rng(s); idx=rng.permutation(N); a,b=int(.6*N),int(.8*N); tr,va,te=idx[:a],idx[a:b],idx[b:]
        mu,sd=X[tr].mean(0),X[tr].std(0)+1e-9; Z=(X-mu)/sd
        m=mk(s).fit(Z[tr],y[tr]); pv,pt=m.predict_proba(Z[va])[:,1],m.predict_proba(Z[te])[:,1]
        r={'auroc':roc_auc_score(y[te],pt),'brier_raw':brier_score_loss(y[te],pt),'ece_raw':ece(pt,y[te])}
        for nm,fn in (('platt',platt),('isotonic',iso),('temperature',temp)):
            c=fn(pv,y[va]); q=c(pt); r['ece_'+nm]=ece(q,y[te]); r['brier_'+nm]=brier_score_loss(y[te],q)
            # subgroup recalibration (per age group), compared with global recalibration, evaluated per subgroup
            es_sub=[];es_glob=[];es_raw=[]
            for g in (0,1,2):
                vg,tg=va[age[va]==g],te[age[te]==g]
                if len(vg)<300 or len(tg)<300: continue
                cg=fn(m.predict_proba(Z[vg])[:,1],y[vg]); pg=m.predict_proba(Z[tg])[:,1]
                es_sub.append(ece(cg(pg),y[tg])); es_glob.append(ece(c(pg),y[tg])); es_raw.append(ece(pg,y[tg]))
            r['sub_ece_raw_'+nm]=np.mean(es_raw); r['sub_ece_global_'+nm]=np.mean(es_glob); r['sub_ece_subgroup_'+nm]=np.mean(es_sub)
        rows.append(r)
    df=pd.DataFrame(rows); res[mname]={k:{'mean':round(float(df[k].mean()),4),'ci95':round(float(1.96*df[k].std(ddof=1)/np.sqrt(len(df))),4)} for k in df.columns}
    print(mname,{k:res[mname][k]['mean'] for k in ('auroc','ece_raw','ece_platt','ece_isotonic','ece_temperature','brier_raw','brier_platt')})
json.dump(res,open('readmit_results.json','w'),indent=1)
