import re
AI_SIGNALS={'retrieval_or_vector_search':(r'\brag\b|retrieval[ -]augmented|vector (?:database|search|store)|embeddings?|semantic search|chromadb|faiss|pinecone|weaviate',8),'agent_or_tool_workflow':(r'tool[ -]calling|function calling|multi[ -]agent|agentic workflow|langgraph|google adk|agent orchestrat',8),'state_or_orchestration':(r'stateful|state management|orchestrat|workflow|graph execution|checkpoint',5),'evaluation_or_quality':(r'evaluation|benchmark|precision|recall|accuracy|hallucination|test set|quality measurement',5),'data_processing_or_ingestion':(r'chunking|document processing|data pipeline|ingest(?:ion)?|preprocess|parsing|indexing',5),'product_or_business_logic':(r'users? can|automated|business logic|production|deployed|customer|workflow automation|api endpoint',5),'concrete_implementation_detail':(r'built|implemented|designed|developed|integrated|reduced|improv(?:ed|ing)|latency|throughput|pydantic|async',4)}
PY_SIGNALS={'python_project_or_work':(r'python.{0,70}(?:built|developed|implemented|api|backend|project|pipeline|service)|(?:built|developed|implemented).{0,70}python',9),'python_backend_framework':(r'fastapi|django|flask',6),'api_and_backend':(r'rest(?:ful)? api|backend service|api endpoint|microservice',4),'database':(r'postgres(?:ql)?|\bredis\b|\bsql\b|database schema|orm',4),'async_or_reliability':(r'async|concurren|retry|timeout|rate limit|error handling|exception handling',3),'python_skill':(r'\bpython\b',4)}
CLOUD={'containerization':(r'docker|containeri[sz]ation',4),'cloud_platform':(r'\bgcp\b|google cloud|\baws\b|amazon web services|\bazure\b',4),'deployment_or_ci':(r'deploy(?:ed|ment)?|ci/cd|github actions|jenkins|vercel|render\.com|railway',4),'end_to_end_full_stack':(r'react|next\.js|frontend.{0,50}backend|full[ -]stack|end[ -]to[ -]end',3)}
ENG={'testing':(r'pytest|unit tests?|integration tests?|test coverage|automated tests?',1),'architecture_or_modularity':(r'modular|architecture|design pattern|separation of concerns|schema-driven',1),'caching_or_performance':(r'cach(?:e|ing)|optimized|performance|latency|lru|batching',1),'reliability_or_observability':(r'retry|failure handling|logging|monitoring|observability|tracing|rate limit',1),'concurrency_or_queues':(r'async|concurren|queue|kafka|rabbitmq|celery',1)}
def _score(text,signals,cap):
    ev=[]; points=0
    for label,(pattern,value) in signals.items():
        if re.search(pattern,text,re.I|re.S):ev.append(label);points+=value
    return min(cap,points),ev
def score_candidate(c,github=None):
    full=c.get('text',''); project=c.get('project_evidence_text',full)
    ai,ae=_score(project,AI_SIGNALS,40)
    if ai<12: ai,ae2=_score(full,AI_SIGNALS,40); ae=ae2
    py,pe=_score(project,PY_SIGNALS,30)
    if py<8:py,pe=_score(full,PY_SIGNALS,30)
    cloud,ce=_score(full,CLOUD,15); eng,ee=_score(full,ENG,5); gh=min(10,max(0,int((github or {}).get('score',0))))
    penalties=[]; low=project.lower()
    if re.search(r'(?:chatbot|chat bot|ai assistant).{0,100}(?:openai api|llm api|api call)|(?:openai api|llm api).{0,100}(?:chatbot|chat bot|ai assistant)',low,re.S) and not re.search(r'rag|retrieval|embeddings|tool.call|evaluation|workflow|database|state management|document processing',low):penalties.append({'reason':'AI project appears to be a thin LLM/API wrapper without supporting workflow evidence','points':10})
    elif re.search(r'tutorial|youtube tutorial',low) and not re.search(r'implemented|modified|extended|deployed|evaluation|benchmark',low):penalties.append({'reason':'Tutorial-style project has limited evidence of independent implementation','points':5})
    penalty=min(15,sum(p['points'] for p in penalties)); total=max(0,min(100,ai+py+cloud+gh+eng-penalty))
    lines=[re.sub(r'\s+',' ',x).strip(' •-–') for x in project.splitlines() if x.strip()]; useful=[x for x in lines if re.search(r'built|developed|implemented|designed|pipeline|agent|rag|llm|retrieval|model|api',x,re.I) and len(x)>35]
    summary=' '.join(useful[:2])[:420] if useful else 'AI-related terms were detected, but the resume provides limited project-specific detail.'
    strengths=[]
    if ai>=28:strengths.append('Strong AI/agentic project evidence')
    elif ai>=18:strengths.append('Relevant AI project signals')
    if py>=20:strengths.append('Practical Python/backend evidence')
    if cloud>=10:strengths.append('Deployment or end-to-end engineering evidence')
    if eng>=3:strengths.append('Non-trivial engineering practices mentioned')
    concerns=[]
    if ai<18:concerns.append('Limited evidence of AI project depth')
    if py<15:concerns.append('Limited Python/backend implementation detail')
    if not c.get('github_url'):concerns.append('No GitHub profile found in resume; no penalty applied')
    if penalties:concerns.extend(p['reason'] for p in penalties)
    c.update({'total_score':total,'score_breakdown':{'ai_project_depth':ai,'python_backend':py,'cloud_fullstack':cloud,'github':gh,'engineering_depth':eng},'score_evidence':{'ai_project_depth':ae,'python_backend':pe,'cloud_fullstack':ce,'engineering_depth':ee},'project_summary':summary,'github_summary':(github or {}).get('summary','No GitHub profile found; enrichment not applicable.'),'github_enrichment':github or {'status':'not_applicable','score':0,'summary':'No GitHub profile found; enrichment not applicable.'},'strengths':strengths,'concerns':concerns,'project_quality_penalties':penalties,'scoring_method':'deterministic_evidence_heuristics'})
    return c
