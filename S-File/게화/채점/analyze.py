import os, sys, json, io
R=json.load(io.open('rubric.json',encoding='utf-8')); S={s['id']:s for s in json.load(io.open('samples.json',encoding='utf-8'))}
res=json.load(io.open(os.environ.get('IN','results.json'),encoding='utf-8'))
PRICE={'gpt-4o':(2.5,10.0),'gpt-4o-mini':(0.15,0.6),'gpt-4.1':(2.0,8.0),'gpt-4.1-mini':(0.4,1.6)}
def exp_total(s):
    t=0
    for q in R['questions']:
        if q['role']!=s['role']: continue
        qs=sum({l['id']:l['score'] for l in e['levels']}[s['expected'][e['id']]] for e in q['elements'])
        if s['expected_gates'].get(q['question_id']): qs=0
        t+=qs
    return t
for m in sys.argv[1].split(','):
    cost=0; ok=0; n=0; same=0; sn=0; maxd=0; tin=0; cnt=0; cached=0; bad=[]
    for sid,s in S.items():
        rs=[r for r in res if r['model']==m and r['sample']==sid]
        if not rs: continue
        e=exp_total(s)
        line=[]
        for r in rs:
            mm=[(k,v,s['expected'][k]) for k,v in r['per'].items() if v!=s['expected'][k]]
            ok+=len(r['per'])-len(mm); n+=len(r['per']); maxd=max(maxd,abs(r['total']-e))
            cost+=(r['tokens_in']*PRICE[m][0]+r['tokens_out']*PRICE[m][1])/1e6
            tin+=r['tokens_in']; cached+=r.get('cached',0); cnt+= r['tokens_in']>0
            line.append((r['total'],len(mm),r['notes']['quote_downgrades'],mm))
        if len(rs)>1:
            for k in rs[0]['per']:
                sn+=1; same+= rs[0]['per'][k]==rs[1]['per'][k]
        print(f"{sid:20s} 기대{e:4d} 실행 {[l[0] for l in line]} 불일치 {[l[1] for l in line]} 강등 {[l[2] for l in line]}")
        for k,v,x in line[0][3]: print(f"      {k}: AI={v} 기대={x}")
    print(f"== {m}: 요소 일치 {ok}/{n} = {ok/n:.1%}, 실행간 일치 {same}/{sn} = {same/max(sn,1):.1%}, 총점 최대 오차 {maxd}, 비용 ${cost:.3f}, 평균 입력 {tin//max(cnt,1)}토큰(캐시 {cached//max(cnt,1)})")
