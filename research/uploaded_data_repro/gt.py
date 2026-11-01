import sys, json, numpy as np, pandas as pd
sys.path.insert(0,'/home/user/prod/digital-twine-gas-turbine')
from research.gt_drift.aci import fixed_interval_coverage, aci_coverage
from sklearn.ensemble import HistGradientBoostingRegressor
D='/home/user/rd/gt/'
df=pd.concat([pd.read_csv(f'{D}gt_{y}.csv').assign(year=y) for y in range(2011,2016)],ignore_index=True)
print(len(df)); F=['AT','AP','AH','AFDP','GTEP','TIT','TAT','TEY','CDP']
out={'rows':len(df)}
tr=df[df.year<=2012]; cal=df[df.year==2013]; te=df[df.year>=2014]
for tgt in ('NOX','CO'):
    m=HistGradientBoostingRegressor(random_state=0).fit(tr[F],tr[tgt])
    rows=pd.concat([cal,te]); pred=m.predict(rows[F]); y=rows[tgt].values
    rmse_cal=float(np.sqrt(((y[:len(cal)]-pred[:len(cal)])**2).mean())); rmse_te=float(np.sqrt(((y[len(cal):]-pred[len(cal):])**2).mean()))
    n=len(cal); fc,fw=fixed_interval_coverage(y,pred,n); ac,aw=aci_coverage(y,pred,n)
    out[tgt]={'rmse_cal_2013':rmse_cal,'rmse_test_2014_15':rmse_te,'fixed_cov':fc,'fixed_width':fw,'aci_cov':ac,'aci_width':aw}
    print(tgt,out[tgt])
json.dump(out,open('/home/user/rd/repro/gt_results.json','w'),indent=1)
