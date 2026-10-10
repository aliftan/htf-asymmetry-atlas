#!/usr/bin/env python3
"""Reproducible XAUUSD HTF asymmetry atlas.
Usage: python xau_htf_full_statistics.py --csv 'xauusd_d.csv' --start 2001-01-01 --end 2025-12-31 --out output
Requires pandas numpy matplotlib. CSV columns Date,Open,High,Low,Close.
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates

def main():
 p=argparse.ArgumentParser();p.add_argument('--csv',required=True);p.add_argument('--start',default='2001-01-01');p.add_argument('--end',default='2025-12-31');p.add_argument('--out',default='output');a=p.parse_args()
 out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 d=pd.read_csv(a.csv,parse_dates=['Date']);d=d.sort_values('Date').drop_duplicates('Date',keep='last').set_index('Date')
 d=d.loc[a.start:a.end,['Open','High','Low','Close']].apply(pd.to_numeric,errors='coerce').dropna()
 if d.empty:raise ValueError('No daily OHLC data in chosen range')
 specs=[('Quarterly','QS',3),('Semiannual','2QS-JAN',6),('Yearly','YS',12)]
 rows=[];bars=[];transitions=[];annual=[]
 fig,axs=plt.subplots(1,3,figsize=(17,5.1));fig.patch.set_facecolor('#fff')
 for ax,(name,freq,months) in zip(axs,specs):
  g=d.resample(freq).agg({'Open':'first','High':'max','Low':'min','Close':'last'}).dropna();g['Start']=g.index;g['End']=g.index+pd.DateOffset(months=months)-pd.Timedelta(days=1)
  # Exclude incomplete calendar periods, even if the dataset ends mid-period
  g=g[(g['Start']>=pd.Timestamp(a.start))&(g['End']<=pd.Timestamp(a.end))].copy()
  if g.empty:continue
  g['ReturnPct']=(g.Close/g.Open-1)*100;g['Direction']=np.where(g.ReturnPct>0,'UP',np.where(g.ReturnPct<0,'DOWN','FLAT'))
  g['BodyUSD']=g.Close-g.Open;g['RangePct']=(g.High-g.Low)/g.Open*100;g['UpperWickPct']=(g.High-g[['Open','Close']].max(axis=1))/g.Open*100;g['LowerWickPct']=(g[['Open','Close']].min(axis=1)-g.Low)/g.Open*100
  g['Year']=g.Start.dt.year;g['Timeframe']=name;bars.append(g.reset_index(drop=True))
  r=g.ReturnPct;u=r[r>0];dn=r[r<0];n=len(r);pos=len(u);neg=len(dn);flat=n-pos-neg
  # Calendar Open/Close return is a candle-body measure, NOT total holding return across gaps.
  row={'timeframe':name,'n':n,'bullish':pos,'bearish':neg,'flat':flat,'bullish_pct':100*pos/n,'bearish_pct':100*neg/n,'bull_bear_count_ratio':pos/neg if neg else np.nan,
       'mean_return_pct':r.mean(),'median_return_pct':r.median(),'std_return_pct':r.std(ddof=1),'min_return_pct':r.min(),'max_return_pct':r.max(),
       'mean_positive_pct':u.mean(),'median_positive_pct':u.median(),'mean_negative_pct':dn.mean(),'median_negative_pct':dn.median(),
       'upside_downside_magnitude_ratio':u.mean()/abs(dn.mean()) if len(dn) else np.nan,
       'sum_positive_pct':u.sum(),'sum_negative_abs_pct':-dn.sum(),'upside_share_of_abs_returns_pct':100*u.sum()/r.abs().sum(),
       'positive_return_contribution_pct':u.sum()/n,'negative_return_contribution_pct':dn.sum()/n,
       'mean_range_pct':g.RangePct.mean(),'median_range_pct':g.RangePct.median(),'mean_body_usd':g.BodyUSD.mean(),
       'max_up_streak':max_streak(g.Direction,'UP'),'max_down_streak':max_streak(g.Direction,'DOWN'),
       'first_period':str(g.Start.iloc[0].date()),'last_period':str(g.End.iloc[-1].date())}
  # exact binomial 95% Wilson CI for proportion, descriptive only
  z=1.95996398454;ph=pos/n;den=1+z*z/n;ctr=(ph+z*z/(2*n))/den;hw=z*np.sqrt(ph*(1-ph)/n+z*z/(4*n*n))/den
  row['bullish_wilson95_low_pct']=100*(ctr-hw);row['bullish_wilson95_high_pct']=100*(ctr+hw)
  rows.append(row)
  directions=g.Direction.tolist()
  for i in range(len(directions)-1):transitions.append({'timeframe':name,'from':directions[i],'to':directions[i+1],'next_return_pct':r.iloc[i+1]})
  yr=g.groupby('Year').agg(n=('ReturnPct','size'),bullish=('ReturnPct',lambda x:(x>0).sum()),bearish=('ReturnPct',lambda x:(x<0).sum()),mean_return_pct=('ReturnPct','mean'),median_return_pct=('ReturnPct','median'));yr['Timeframe']=name;annual.append(yr.reset_index())
  for _,v in g.iterrows():
   x=mdates.date2num(v.Start+(v.End-v.Start)/2);width=max(10,(v.End-v.Start).days*.65);c='#17855b' if v.Close>=v.Open else '#ce4a4a'
   ax.vlines(x,v.Low,v.High,color=c,lw=.75);ax.add_patch(Rectangle((x-width/2,min(v.Open,v.Close)),width,max(abs(v.Close-v.Open),2),color=c,alpha=.92))
  ax.xaxis_date();ax.xaxis.set_major_locator(mdates.YearLocator(5));ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'));ax.tick_params(axis='x',rotation=40);ax.grid(alpha=.13);ax.set_title(f'{name} | {pos}/{n} up ({100*pos/n:.1f}%)',loc='left',fontsize=12,fontweight='bold');ax.set_ylabel('USD/oz')
  # Individual chart
  f,aa=plt.subplots(figsize=(16,6));aa.set_facecolor('#fafbfc')
  for _,v in g.iterrows():
   x=mdates.date2num(v.Start+(v.End-v.Start)/2);width=max(10,(v.End-v.Start).days*.7);c='#17855b' if v.Close>=v.Open else '#ce4a4a';aa.vlines(x,v.Low,v.High,color=c,lw=1);aa.add_patch(Rectangle((x-width/2,min(v.Open,v.Close)),width,max(abs(v.Close-v.Open),2),color=c,alpha=.9))
  aa.xaxis_date();aa.xaxis.set_major_locator(mdates.YearLocator(2 if months<=6 else 1));aa.xaxis.set_major_formatter(mdates.DateFormatter('%Y'));aa.tick_params(axis='x',rotation=40);aa.grid(alpha=.12);aa.set_title(f'XAUUSD {name} | {g.Start.iloc[0].year}–{g.End.iloc[-1].year} | {pos}/{n} bullish',loc='left',fontsize=16);aa.set_ylabel('USD/oz');f.tight_layout();f.savefig(out/f'{name.lower()}_candles.png',dpi=160);plt.close(f)
 fig.suptitle('XAUUSD higher-timeframe candles | Asymmetry Atlas',fontsize=18,fontweight='bold');fig.tight_layout();fig.savefig(out/'all_three_htf_candles.png',dpi=150);plt.close(fig)
 summary=pd.DataFrame(rows);summary.to_csv(out/'htf_full_statistics.csv',index=False);allbars=pd.concat(bars,ignore_index=True);allbars.to_csv(out/'htf_all_candles.csv',index=False);pd.concat(annual).to_csv(out/'htf_by_year.csv',index=False)
 t=pd.DataFrame(transitions);tr=t.groupby(['timeframe','from','to']).agg(n=('next_return_pct','size'),mean_next_return_pct=('next_return_pct','mean')).reset_index();tr.to_csv(out/'htf_transitions.csv',index=False)
 # descriptive bootstrap: resample entire calendar years to keep within-year quarter/semester dependencies
 rng=np.random.default_rng(42);ci=[]
 for name in summary.timeframe:
  g=allbars[allbars.Timeframe==name];years=np.sort(g.Year.unique());ys={y:g[g.Year==y].ReturnPct.to_numpy() for y in years};vals=[]
  for _ in range(3000):
   sample=np.concatenate([ys[y] for y in rng.choice(years,len(years),replace=True)]);vals.append([np.mean(sample>0),np.mean(sample)])
  v=np.array(vals);ci.append({'timeframe':name,'year_block_bootstrap_bullish_low_pct':100*np.quantile(v[:,0],.025),'year_block_bootstrap_bullish_high_pct':100*np.quantile(v[:,0],.975),'year_block_bootstrap_mean_low_pct':np.quantile(v[:,1],.025),'year_block_bootstrap_mean_high_pct':np.quantile(v[:,1],.975)})
 pd.DataFrame(ci).to_csv(out/'htf_year_block_bootstrap.csv',index=False)
 # Dashboard
 fig,axs=plt.subplots(2,2,figsize=(14,9));fig.patch.set_facecolor('white');names=summary.timeframe.tolist();x=np.arange(len(names));colors=['#147d5a','#dc5c5c']
 ax=axs[0,0];ax.bar(x,summary.bullish_pct,color=colors[0],label='Up');ax.bar(x,summary.bearish_pct,bottom=summary.bullish_pct,color=colors[1],label='Down');ax.set_xticks(x,names);ax.set_ylim(0,108);ax.set_ylabel('% of candles');ax.set_title('Direction frequency');ax.legend(loc='lower right')
 for i,v in enumerate(summary.bullish_pct):ax.text(i,v/2,f'{v:.1f}% up',ha='center',va='center',color='white',weight='bold')
 ax=axs[0,1];ax.bar(x-.17,summary.mean_positive_pct,.34,color=colors[0],label='Mean up');ax.bar(x+.17,summary.mean_negative_pct,.34,color=colors[1],label='Mean down');ax.axhline(0,color='#333',lw=.7);ax.set_xticks(x,names);ax.set_ylabel('% return');ax.set_title('Magnitude conditional on direction');ax.legend()
 ax=axs[1,0];ax.bar(x,summary.mean_return_pct,color=colors[0]);ax.set_xticks(x,names);ax.set_ylabel('% return');ax.set_title('Unconditional mean candle return')
 ax=axs[1,1];ax.bar(x-.17,summary.sum_positive_pct,.34,color=colors[0],label='Sum of positive returns');ax.bar(x+.17,-summary.sum_negative_abs_pct,.34,color=colors[1],label='Sum of negative returns');ax.axhline(0,color='#333',lw=.7);ax.set_xticks(x,names);ax.set_ylabel('Sum of candle returns, percentage points');ax.set_title('Positive vs negative return contributions');ax.legend(fontsize=8)
 for ax in axs.flat:ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
 fig.suptitle('XAUUSD | Upside–downside asymmetry, 2001–2025',fontsize=18,fontweight='bold');fig.tight_layout();fig.savefig(out/'htf_asymmetry_dashboard.png',dpi=170);plt.close(fig)
 # Export presentation-ready statistical report images into the SAME output folder.
 make_report_images(out, summary, allbars, t, pd.DataFrame(ci), pd.concat(annual,ignore_index=True), a.start, a.end)
 print(summary.round(3).to_string(index=False));print('\nBootstrap\n',pd.DataFrame(ci).round(3).to_string(index=False));print('\nTransitions\n',tr.to_string(index=False))

def make_report_images(out, stats, bars, transition_events, bootstrap, by_year, start, end):
 """Generate readable report pages; every chart and CSV stays in --out."""
 from matplotlib.colors import TwoSlopeNorm
 names=['Quarterly','Semiannual','Yearly']
 s=stats.set_index('timeframe').loc[names]
 green='#127e5b';red='#bd4b50';ink='#18212d';muted='#5d6979'
 def page(title,subtitle,rows,filename,footnote=None,figsize=(15,8.5)):
  fig,ax=plt.subplots(figsize=figsize);fig.patch.set_facecolor('#f9fafb');ax.axis('off')
  ax.text(.045,.945,title,transform=ax.transAxes,fontsize=25,fontweight='bold',color=ink,va='top')
  ax.text(.045,.878,subtitle,transform=ax.transAxes,fontsize=12,color=muted,va='top')
  cols=['METRIC','QUARTERLY','SEMIANNUAL','YEARLY'];xs=[.05,.50,.69,.87]
  ax.add_patch(Rectangle((.035,.775),.93,.062,transform=ax.transAxes,color='#e8edf1',lw=0))
  for x,c in zip(xs,cols):ax.text(x,.806,c,transform=ax.transAxes,fontsize=11,fontweight='bold',color=ink,va='center',ha='left' if x==.05 else 'center')
  top=.745;bottom=.14 if footnote else .075;step=(top-bottom)/max(len(rows),1)
  for j,(label,values) in enumerate(rows):
   y=top-j*step
   if j%2==0:ax.add_patch(Rectangle((.035,y-step*.58),.93,step*.95,transform=ax.transAxes,color='#eff3f5',alpha=.7,lw=0))
   ax.text(.05,y,label,transform=ax.transAxes,fontsize=11.3,color=ink,va='center')
   for x,v in zip(xs[1:],values):
    color=green if isinstance(v,str) and v.startswith('+') else red if isinstance(v,str) and v.startswith('−') else ink
    ax.text(x,y,str(v),transform=ax.transAxes,fontsize=12.3,fontweight='semibold',color=color,va='center',ha='center')
  if footnote:ax.text(.045,.085,footnote,transform=ax.transAxes,fontsize=10,color=muted,va='center',wrap=True)
  fig.savefig(out/filename,dpi=170,bbox_inches='tight',facecolor=fig.get_facecolor());plt.close(fig)
 def row(label,field,fmt='{:.2f}'):
  return (label,[fmt.format(s.loc[n,field]) for n in names])
 page('01  |  Direction & baseline','XAUUSD · Completed calendar candles · '+start+' to '+end,[
  row('Completed candles','n','{:,.0f}'),row('Bullish candles','bullish','{:,.0f}'),row('Bearish candles','bearish','{:,.0f}'),
  row('Bullish frequency','bullish_pct','{:.1f}%'),row('Bearish frequency','bearish_pct','{:.1f}%'),
  row('Bull / bear count ratio','bull_bear_count_ratio','{:.2f}×'),
  row('Mean candle return','mean_return_pct','{:+.2f}%'),row('Median candle return','median_return_pct','{:+.2f}%'),
  row('Return standard deviation','std_return_pct','{:.2f}%')],
  '01_direction_and_baseline.png','Returns are (period Close / period Open − 1) × 100; this is not a trade backtest.')
 page('02  |  Upside vs downside magnitude','The positive and negative tails are measured separately.',[
  row('Mean positive candle','mean_positive_pct','{:+.2f}%'),row('Median positive candle','median_positive_pct','{:+.2f}%'),
  row('Mean negative candle','mean_negative_pct','{:+.2f}%'),row('Median negative candle','median_negative_pct','{:+.2f}%'),
  row('Average up / down magnitude','upside_downside_magnitude_ratio','{:.2f}×'),
  row('Largest positive candle','max_return_pct','{:+.2f}%'),row('Largest negative candle','min_return_pct','{:+.2f}%'),
  row('Upside share of absolute returns','upside_share_of_abs_returns_pct','{:.1f}%'),
  row('Sum of positive returns','sum_positive_pct','{:+.1f} pp'),row('Sum of negative returns','sum_negative_abs_pct','{:.1f} pp')],
  '02_upside_downside_magnitude.png','pp = percentage points. Sums are arithmetic contributions, not compounded returns.')
 page('03  |  Candle risk & persistence','Directional advantage does not remove adverse intraperiod price movement.',[
  row('Mean high-low range / open','mean_range_pct','{:.2f}%'),row('Median high-low range / open','median_range_pct','{:.2f}%'),
  row('Longest consecutive bullish run','max_up_streak','{:,.0f}'),row('Longest consecutive bearish run','max_down_streak','{:,.0f}'),
  row('Mean candle body (USD/oz)','mean_body_usd','{:+.2f}'),
  row('95% Wilson bullish lower','bullish_wilson95_low_pct','{:.1f}%'),row('95% Wilson bullish upper','bullish_wilson95_high_pct','{:.1f}%')],
  '03_range_and_streaks.png','Wilson intervals assume independent trials; see the separate year-block bootstrap for dependence-aware sensitivity.')
 b=bootstrap.set_index('timeframe').loc[names]
 page('04  |  Uncertainty & evidence','Year-block bootstrap (3,000 resamples, fixed seed 42).',[
  row('Observed bullish share','bullish_pct','{:.1f}%'),
  ('Bootstrap bullish 95% lower',[f'{b.loc[n,"year_block_bootstrap_bullish_low_pct"]:.1f}%' for n in names]),
  ('Bootstrap bullish 95% upper',[f'{b.loc[n,"year_block_bootstrap_bullish_high_pct"]:.1f}%' for n in names]),
  row('Observed mean return','mean_return_pct','{:+.2f}%'),
  ('Bootstrap mean 95% lower',[f'{b.loc[n,"year_block_bootstrap_mean_low_pct"]:+.2f}%' for n in names]),
  ('Bootstrap mean 95% upper',[f'{b.loc[n,"year_block_bootstrap_mean_high_pct"]:+.2f}%' for n in names])],
  '04_uncertainty.png','Bootstrap resamples whole calendar years; historical sampling uncertainty does not establish a future forecast.')
 # Transition counts and conditional next-candle up probabilities
 trrows=[]
 for prev in ['UP','DOWN']:
  values=[];counts=[]
  for name in names:
   v=transition_events[(transition_events.timeframe==name)&(transition_events['from']==prev)]
   successes=(v['to']=='UP').sum();n=len(v)
   values.append(f'{100*successes/n:.1f}%' if n else 'N/A');counts.append(f'{successes} / {n}')
  trrows.append(('Next candle UP | after '+('bullish' if prev=='UP' else 'bearish'),values))
  trrows.append(('Observations (up / all)',counts))
 page('05  |  Direction transitions','Conditional next-candle direction; not an independent prediction model.',trrows,
  '05_direction_transitions.png','Transitions within a timeframe are serially dependent; yearly transitions have especially small samples.')
 # Yearly heatmap of candle returns for each horizon
 fig,axs=plt.subplots(3,1,figsize=(17,10),constrained_layout=True);fig.patch.set_facecolor('white')
 for ax,name in zip(axs,names):
  g=bars[bars.Timeframe==name].copy();g['slot']=g.Start.dt.month.map({1:1,4:2,7:3,10:4} if name=='Quarterly' else {1:1,7:2} if name=='Semiannual' else {1:1})
  piv=g.pivot(index='Year',columns='slot',values='ReturnPct');arr=piv.to_numpy(dtype=float)
  vmax=max(10,np.nanmax(abs(arr)));im=ax.imshow(arr.T,aspect='auto',cmap='RdYlGn',vmin=-vmax,vmax=vmax,interpolation='nearest')
  ax.set_yticks(np.arange(len(piv.columns)),[f'Q{x}' if name=='Quarterly' else f'H{x}' if name=='Semiannual' else 'Y' for x in piv.columns]);ax.set_xticks(np.arange(len(piv.index)),piv.index,rotation=90,fontsize=8);ax.set_title(f'{name} · % candle return',loc='left',fontweight='bold')
  for j in range(arr.shape[1]):
   for i in range(arr.shape[0]):
    if np.isfinite(arr[i,j]):ax.text(i,j,f'{arr[i,j]:+.0f}',ha='center',va='center',fontsize=7,color='#17212b')
  fig.colorbar(im,ax=ax,fraction=.012,pad=.012)
 fig.suptitle('06  |  Historical direction heatmap · XAUUSD',fontsize=21,fontweight='bold');fig.savefig(out/'06_historical_return_heatmap.png',dpi=160,bbox_inches='tight');plt.close(fig)
 # Annual share of positive quarterly/semester candles and yearly return
 fig,axs=plt.subplots(2,1,figsize=(16,9),sharex=True);fig.patch.set_facecolor('white')
 years=sorted(bars.Year.unique());x=np.arange(len(years));w=.34
 for name,dx,c in [('Quarterly',-.18,'#257f9a'),('Semiannual',.18,'#147d5a')]:
  g=by_year[by_year.Timeframe==name].set_index('Year').reindex(years)
  axs[0].bar(x+dx,100*g.bullish/g.n,width=w,label=name,color=c)
 axs[0].axhline(50,color=red,ls='--',lw=1);axs[0].set_ylabel('Bullish share (%)');axs[0].set_ylim(0,105);axs[0].set_title('Fraction of positive quarters / half-years within each year',loc='left');axs[0].legend()
 yearly=bars[bars.Timeframe=='Yearly'].set_index('Year').reindex(years);v=yearly.ReturnPct.to_numpy();axs[1].bar(x,v,color=[green if z>0 else red for z in v]);axs[1].axhline(0,color=ink,lw=.8);axs[1].set_ylabel('Yearly candle return (%)');axs[1].set_title('Annual direction and return',loc='left')
 axs[1].set_xticks(x,years,rotation=65);[ax.grid(axis='y',alpha=.15) for ax in axs];fig.suptitle('07  |  Asymmetry through time',fontsize=21,fontweight='bold');fig.tight_layout();fig.savefig(out/'07_year_by_year_regimes.png',dpi=165);plt.close(fig)
 # Interpretive executive summary visual
 fig,ax=plt.subplots(figsize=(15,8));fig.patch.set_facecolor('#f9fafb');ax.axis('off')
 ax.text(.05,.92,'08  |  Market classification',transform=ax.transAxes,fontsize=26,fontweight='bold',color=ink)
 ax.text(.05,.83,'HISTORICAL UPSIDE DOMINANCE',transform=ax.transAxes,fontsize=22,fontweight='bold',color=green)
 ax.text(.05,.75,'All three horizons show >50% bullish candles, positive mean return, and larger mean up moves than down moves.',transform=ax.transAxes,fontsize=12,color=ink)
 for i,name in enumerate(names):
  y=.62-i*.16;v=s.loc[name];ax.add_patch(Rectangle((.05,y-.06),.90,.125,transform=ax.transAxes,color='#e8f3ee',lw=0))
  ax.text(.075,y+.015,name,transform=ax.transAxes,fontsize=16,fontweight='bold',color=ink)
  ax.text(.40,y+.015,f'{v.bullish_pct:.0f}% bullish',transform=ax.transAxes,fontsize=16,color=green,fontweight='bold')
  ax.text(.66,y+.015,f'{v.upside_downside_magnitude_ratio:.2f}× up/down',transform=ax.transAxes,fontsize=14,color=ink)
 ax.text(.05,.11,'LIMITS  |  Historical classification, not a timing signal. HTF candles overlap across scales; no causal claim.',transform=ax.transAxes,fontsize=11,color=muted)
 ax.text(.05,.065,'Do not use an unfinished higher-timeframe candle to label an earlier trading decision.',transform=ax.transAxes,fontsize=11,color=muted)
 fig.savefig(out/'08_executive_conclusion.png',dpi=175,bbox_inches='tight');plt.close(fig)

def max_streak(series,target):
 m=0;c=0
 for v in series:
  c=c+1 if v==target else 0;m=max(m,c)
 return m
if __name__=='__main__':main()
