import argparse,json,os
from pathlib import Path
from dotenv import load_dotenv
from src.parser import SUPPORTED,clean_text,extract_text,file_digest
from src.extract import extract_candidate
from src.eligibility import check_eligibility
from src.github_enrichment import enrich_github
from src.scoring import score_candidate
from src.llm_adapter import assess

def screen(input_dir:Path,output_path:Path,github_enabled=True,llm_enabled=False):
 token=os.getenv('GITHUB_TOKEN'); timeout=float(os.getenv('GITHUB_TIMEOUT_SECONDS','0.5')); api_key=os.getenv('OPENAI_API_KEY'); model=os.getenv('OPENAI_MODEL','gpt-4o-mini')
 files=sorted(p for p in input_dir.rglob('*') if p.is_file() and p.suffix.lower() in SUPPORTED); records=[]; seen={}; ghcache={}; parsed=failed=duplicates=0; errors=[]
 for path in files:
  rel=str(path.relative_to(input_dir))
  try:
   digest=file_digest(path)
   if digest in seen:
    duplicates+=1;records.append({'source_file':rel,'candidate_name':path.stem.replace('_',' ').title(),'eligible':False,'status':'duplicate','duplicate_of':seen[digest],'rejection_reasons':[f'Duplicate file content; duplicate of {seen[digest]}'],'matched_skills':[]});continue
   seen[digest]=rel; text=clean_text(extract_text(path))
   if len(text)<25:raise ValueError('No usable text extracted (possibly a scanned/image-only PDF)')
   parsed+=1;c=extract_candidate(text,path.name);c.update({'source_file':rel,'status':'parsed'});check_eligibility(c)
   if c['eligible']:
    gh=None
    if c.get('github_url') and github_enabled:
     u=c['github_url'].rstrip('/').split('/')[-1].casefold()
     if u not in ghcache:ghcache[u]=enrich_github(c['github_url'],token,timeout)
     gh=ghcache[u]
    elif c.get('github_url'):gh={'status':'skipped','score':0,'summary':'GitHub enrichment skipped by --no-github; no points awarded.'}
    c=score_candidate(c,gh)
    if llm_enabled and api_key:
     try:
      a=assess(c.get('project_evidence_text') or text,api_key,model);b=c['score_breakdown'];b.update({'ai_project_depth':a['ai_project_depth'],'python_backend':a['python_backend'],'cloud_fullstack':a['cloud_fullstack'],'engineering_depth':a['engineering_depth']});pen=a['shallow_project_penalty'];c['total_score']=max(0,min(100,sum(b.values())-pen));c['project_summary']=a['project_summary'];c['strengths']=a['strengths'];c['concerns']=a['concerns'];c['llm_assessment']={'status':'ok','model':model,'penalty_points':pen,'evidence':a['evidence']};c['scoring_method']='llm_structured_assessment_plus_github'
     except Exception as e:c['llm_assessment']={'status':'fallback','error':f'{type(e).__name__}: {str(e)[:180]}','note':'Deterministic score retained.'}
   else:c['status']='rejected'
   for k in ('text','project_evidence_text','source_sections'):c.pop(k,None)
   records.append(c)
  except Exception as e:
   failed+=1;msg=f'{type(e).__name__}: {str(e)[:250]}';errors.append({'source_file':rel,'error':msg});records.append({'source_file':rel,'candidate_name':path.stem.replace('_',' ').title(),'eligible':False,'status':'failed','rejection_reasons':['Resume could not be parsed; manual review may be needed'],'matched_skills':[],'error':msg})
 eligible=[r for r in records if r.get('eligible') is True and r.get('status')!='duplicate'];eligible.sort(key=lambda r:(-r.get('total_score',0),r.get('candidate_name','').casefold(),r.get('source_file','')))
 for i,c in enumerate(eligible,1):c['rank']=i
 rejected=[r for r in records if r.get('eligible') is False or r.get('status') in {'failed','duplicate'}]
 result={'metadata':{'system':'AI Resume Screening & Ranking System','version':'1.0.0','scoring_weights':{'ai_project_depth':40,'python_backend':30,'cloud_fullstack':15,'github':10,'engineering_depth':5},'github_enrichment_enabled':github_enabled,'llm_scoring_enabled':bool(llm_enabled and api_key),'note':'Eligibility remains deterministic. LLM scoring is optional; failed calls fall back to deterministic scoring.'},'batch_summary':{'total_files_discovered':len(files),'successfully_parsed':parsed,'eligible':len(eligible),'rejected':sum(r.get('status')=='rejected' for r in records),'failed_or_unreadable':failed,'duplicates':duplicates,'supported_files':len(files)},'ranked_candidates':eligible,'rejected_candidates':rejected,'all_candidates':sorted(records,key=lambda r:(0 if r.get('eligible') else 1,r.get('rank',10**6),r.get('source_file',''))),'processing_errors':errors}
 output_path.parent.mkdir(parents=True,exist_ok=True);output_path.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8');return result

def main():
 load_dotenv();p=argparse.ArgumentParser(description='Explainable AI resume screening CLI');p.add_argument('--input',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--no-github',action='store_true');p.add_argument('--use-llm',action='store_true');a=p.parse_args()
 if not a.input.is_dir():p.error(f'Input directory does not exist: {a.input}')
 d=screen(a.input,a.output,not a.no_github,a.use_llm);print(json.dumps(d['batch_summary'],indent=2));print(f'Results written to: {a.output}')
if __name__=='__main__':main()
