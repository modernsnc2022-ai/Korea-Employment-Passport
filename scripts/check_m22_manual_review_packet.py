#!/usr/bin/env python3
"""Read-only validation of an unsigned M22 manual review packet."""
from pathlib import Path
import json
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'research/source_reviews/indonesia_m22_manual_review_queue_2026-10-17.json'

def validate(d):
    def need(v,msg):
        if not v: raise ValueError('M22_REVIEW_PACKET_BLOCKED '+msg)
    need(d.get('evidenceDate')=='2026-10-17','date')
    w=d.get('originalWatch',{})
    need((w.get('configured'),w.get('checked'),w.get('sourceShaDifferencesVsLastAcceptedBaseline'))==(84,84,12),'source counts')
    need((w.get('koreaShared'),w.get('multiCountryHRD'),w.get('otherCountry'))==(5,2,5),'scope counts')
    a=d.get('sourceAlerts',[])
    need(len(a)==12 and len({x['id'] for x in a})==12,'source IDs')
    need({k:sum(x['scope']==k for x in a) for k in ['korea_shared','multi_country_eps_schedule','other_country']}=={'korea_shared':5,'multi_country_eps_schedule':2,'other_country':5},'scope distribution')
    need(all(x['manualDecision']=='pending' and x['reviewer'] is None for x in a),'unsigned sources')
    h=d.get('pdfLinkCheck',{})
    need((h.get('total'),h.get('headMetadataPdfResponses'),h.get('headConnectionResetInconclusive'))==(24,10,14) and h.get('bodyReadAndApprovedByHuman') is False,'PDF limits')
    tasks=d.get('pdfTasks',[])
    need(len(tasks)==14 and len({x['officialUrl'] for x in tasks})==14,'PDF unique')
    counts={date:sum(x['noticeDate']==date for x in tasks) for date in ['2026-09-17','2026-01-27','2026-03-27']}
    need(counts=={'2026-09-17':4,'2026-01-27':3,'2026-03-27':7},'PDF scopes')
    for x in tasks:
        url=urlparse(x['officialUrl'])
        need(url.scheme=='https' and url.hostname=='kp2mi.go.id' and url.path.startswith('/uploads/gtgkorea/') and url.path.lower().endswith('.pdf'),'official PDF URL')
        need(x['lastHeadResult']=='inconclusive_remote_connection_reset_WinError10054' and x['bodyReviewedOnM22'] is False and x['humanDecision']=='pending' and x['humanReviewer'] is None and x['qualifiesAsFinalManufacturingJobDocs'] is False,'PDF no signoff')
    g=d.get('gates',{})
    need(g.get('officialSignoff')=='pending' and g.get('reviewer') is None and g.get('reviewedAt') is None and g.get('sourceHashesAccepted') is False and g.get('finalManufacturingJobDocs')=='hold' and g.get('publicBetaAccess')=='hold' and g.get('productionDeployAuthorized') is False and g.get('releaseAuthorized') is False,'release guards')
    return True

def self_test():
    d=json.loads(p.read_text(encoding='utf-8'))
    validate(d)
    from copy import deepcopy
    def mutations():
        a=deepcopy(d);a['gates']['releaseAuthorized']=True;yield a
        a=deepcopy(d);a['pdfTasks'][0]['humanDecision']='approved';yield a
        a=deepcopy(d);a['pdfTasks'][0]['officialUrl']='https://evil.example/test.pdf';yield a
        a=deepcopy(d);a['pdfTasks'].pop();yield a
        a=deepcopy(d);a['sourceAlerts'][0]['manualDecision']='approved';yield a
        a=deepcopy(d);a['originalWatch']['checked']=83;yield a
        a=deepcopy(d);a['pdfLinkCheck']['headMetadataPdfResponses']=24;yield a
        a=deepcopy(d);a['gates']['finalManufacturingJobDocs']='verified';yield a
        a=deepcopy(d);a['gates']['publicBetaAccess']='open';yield a
    count=0
    for a in mutations():
        try:validate(a)
        except ValueError:count+=1
        else:raise AssertionError('unsafe mutant allowed')
    print(f'M22_REVIEW_PACKET_SELF_TEST_PASS 14_pdf_pending 12_source_pending {count}_negative_mutations')
if __name__=='__main__':self_test()
