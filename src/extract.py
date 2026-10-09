import re
SKILLS={
'Python':r'\bpython\b','FastAPI':r'\bfastapi\b','Flask':r'\bflask\b','Django':r'\bdjango\b','PostgreSQL':r'\bpostgres(?:ql)?\b','Redis':r'\bredis\b','SQL':r'\bsql\b',
'LangChain':r'\blangchain\b','LangGraph':r'\blanggraph\b','LlamaIndex':r'\bllamaindex\b','RAG':r'\brag\b|retrieval[ -]augmented generation','LLM':r'\bllms?\b|large language models?',
'Embeddings':r'\bembeddings?\b','Vector search':r'vector (?:database|search|store)|\bchroma(?:db)?\b|\bfaiss\b|\bpinecone\b|\bweaviate\b','Agent/tool calling':r'tool[ -]calling|\bagents?\b|function calling|multi[ -]agent|google adk',
'Docker':r'\bdocker\b','GCP':r'\bgcp\b|google cloud','AWS':r'\baws\b|amazon web services','Azure':r'\bazure\b','React':r'\breact(?:\.js)?\b','Next.js':r'\bnext\.js\b','Node.js':r'\bnode\.js\b|\bnodejs\b',
'Testing':r'\bpytest\b|unit tests?|integration tests?','Caching':r'\bcach(?:e|ing|ed)\b','Async/concurrency':r'\basync(?:io)?\b|concurren(?:cy|t)|parallel processing|\bthreading\b'}
HEAD=re.compile(r'(?im)^\s*(?:projects?|work experience|experience|internships?|technical skills|skills|education|certifications|achievements|summary|professional summary|about me)\s*:?\s*$')
def extract_candidate(text,filename):
    lines=[re.sub(r'\s+',' ',x).strip(' |•\t') for x in text.splitlines() if x.strip()]
    emailm=re.search(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',text,re.I); emails=re.findall(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',text,re.I)
    name=None
    # Handle names fused to email in PDF extraction.
    if emailm:
        for line in text[:emailm.start()].splitlines()[:5]:
            line=re.sub(r'[|•—–:+]',' ',line).strip(); words=re.findall(r"[A-Za-z][A-Za-z'.-]*",line)
            if 2<=len(words)<=4 and not re.search(r'developer|engineer|student|summary|education|skills|experience|linkedin|github|hyderabad|bengaluru|india|phone',line,re.I): name=' '.join(words); break
    loc={'bengaluru','bangalore','hyderabad','ghaziabad','india','karnataka','delhi','mumbai','pune','chennai','up','telangana','maharashtra'}
    if not name:
        for i,line in enumerate(lines[:12]):
            if len(line)>65 or '@' in line or ',' in line or re.search(r'https?://|linkedin|github|phone|email',line,re.I): continue
            words=re.findall(r"[A-Za-z][A-Za-z'.-]*",line)
            if 2<=len(words)<=4 and not re.search(r'developer|engineer|student|summary|education|skills|experience|profile|objective',line,re.I): name=' '.join(words); break
            if len(words)==1 and i+1<len(lines) and re.fullmatch(r'[A-Za-z\'-]+',lines[i+1]): name=line+' '+lines[i+1]; break
    if name:
        ws=name.split()
        while len(ws)>2 and ws[-1].lower().strip('.,') in loc: ws.pop()
        name=' '.join(ws)
    if not name: name=filename.rsplit('.',1)[0].replace('_',' ').title()
    gh=re.findall(r'(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9-]+)',text,re.I); gh=[u for u in gh if u.lower() not in {'features','topics','settings','orgs','marketplace'}]
    matches=list(HEAD.finditer(text)); sections={}
    for i,m in enumerate(matches):
        end=matches[i+1].start() if i+1<len(matches) else len(text); key=m.group(0).strip().lower().replace(':',''); sections[key]=sections.get(key,'')+'\n'+text[m.end():end]
    project='\n'.join(v for k,v in sections.items() if any(x in k for x in ('project','experience','internship')))
    if len(project.strip())<100: project=text
    return {'candidate_name':name,'email':emails[0] if emails else None,'github_url':f'https://github.com/{gh[0]}' if gh else None,'matched_skills':[s for s,p in SKILLS.items() if re.search(p,text,re.I)],'text':text,'project_evidence_text':project,'source_sections':list(sections)}
