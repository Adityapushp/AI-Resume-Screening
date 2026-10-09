import re,requests
from datetime import datetime,timezone,timedelta
def enrich_github(url,token=None,timeout=.5):
    if not url:return {'status':'not_applicable','score':0,'summary':'No GitHub profile found; enrichment not applicable.'}
    m=re.search(r'github\.com/([A-Za-z0-9-]+)',url,re.I)
    if not m:return {'status':'invalid_url','score':0,'summary':'Could not parse GitHub URL; screening continued.'}
    username=m.group(1); headers={'Accept':'application/vnd.github+json','User-Agent':'AI-Resume-Screening-Assignment'}
    if token:headers['Authorization']='Bearer '+token
    try:
        r=requests.get(f'https://api.github.com/users/{username}/repos',params={'sort':'updated','per_page':100,'type':'owner'},headers=headers,timeout=(timeout,timeout))
        if r.status_code==404:return {'status':'not_found','score':0,'summary':'GitHub profile/repositories not found; screening continued.','username':username}
        if r.status_code==403:return {'status':'rate_limited','score':0,'summary':'GitHub API returned 403/rate limit; screening continued.','username':username}
        r.raise_for_status(); repos=r.json() if isinstance(r.json(),list) else []; cutoff=datetime.now(timezone.utc)-timedelta(days=90); active=[]; relevant=[]
        for repo in repos:
            if repo.get('fork',False):continue
            try:
                if datetime.fromisoformat(repo.get('pushed_at','').replace('Z','+00:00'))>=cutoff:active.append(repo)
            except Exception:pass
            desc=f"{repo.get('name','')} {repo.get('description') or ''} {repo.get('language') or ''}".lower()
            if re.search(r'python|langchain|langgraph|llm|agent|rag|machine learning|artificial intelligence|fastapi',desc):relevant.append(repo)
        a=5 if len(active)>=5 else 4 if len(active)>=3 else 3 if len(active)==2 else 1 if active else 0
        b=min(5,min(3,len(active))+(2 if relevant else 0)); score=min(10,a+b)
        return {'status':'ok','score':score,'username':username,'public_repositories':len(repos),'recently_pushed_nonfork_repositories':len(active),'relevant_repositories':len(relevant),'activity_window_days':90,'summary':f'{len(active)} non-fork public repositories pushed in the last 90 days; {len(relevant)} appear Python/AI-relevant by name, description, or language.','activity_measure':'recent public repository pushes'}
    except requests.RequestException as e:return {'status':'unavailable','score':0,'username':username,'summary':f'GitHub enrichment failed ({type(e).__name__}); no points awarded and screening continued.'}
    except (ValueError,TypeError,KeyError) as e:return {'status':'invalid_response','score':0,'username':username,'summary':f'GitHub response could not be interpreted ({type(e).__name__}); screening continued.'}
