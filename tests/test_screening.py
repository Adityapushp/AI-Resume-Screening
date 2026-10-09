from src.eligibility import check_eligibility
from src.scoring import score_candidate
from src.github_enrichment import enrich_github

def cand(text,project=None):return {'candidate_name':'Test Candidate','text':text,'project_evidence_text':project or text,'matched_skills':[],'github_url':None}
def test_rejects_without_python():
    c = check_eligibility(cand('JavaScript React Next.js LangChain chatbot'))
    assert not c['eligible']
    assert 'No Python evidence in resume' in c['rejection_reasons']
def test_rejects_without_ai():
    c = check_eligibility(cand('Python Django PostgreSQL REST APIs'))
    assert not c['eligible']
    assert 'No AI/LLM/RAG evidence in project/work section' in c['rejection_reasons']
def test_accepts_python_ai_and_javascript():assert check_eligibility(cand('Python FastAPI React; built a RAG pipeline with embeddings and vector search'))['eligible']
def test_ai_skills_only_do_not_pass_if_project_has_no_ai():assert not check_eligibility(cand('Python LangChain LLM React','Built REST APIs in Python and React UI.'))['eligible']
def test_score_is_bounded():
 c=cand('Python FastAPI PostgreSQL Docker GCP pytest caching','Built a LangGraph agent workflow with RAG, embeddings, tool calling, evaluation, document ingestion, and FastAPI backend.');check_eligibility(c);o=score_candidate(c,{'score':8,'summary':'active'});assert 0<=o['total_score']<=100;assert o['score_breakdown']['ai_project_depth']<=40;assert o['score_breakdown']['github']<=10
def test_missing_github_is_nonfatal():assert enrich_github(None)['status']=='not_applicable'
def test_batch_bad_pdf_and_duplicate(tmp_path):
 from main import screen
 d=tmp_path/'resumes';d.mkdir();p=d/'one.txt';p.write_text('Alex Candidate\nPython FastAPI\nBuilt a RAG pipeline with embeddings and vector search in Python.');(d/'duplicate.txt').write_text(p.read_text());(d/'broken.pdf').write_bytes(b'not a PDF')
 r=screen(d,tmp_path/'out.json',False);assert r['batch_summary']['total_files_discovered']==3;assert r['batch_summary']['duplicates']==1;assert r['batch_summary']['failed_or_unreadable']==1;assert len(r['ranked_candidates'])==1
