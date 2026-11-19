"""Full B0 source/candidate resource preflight; read-only assets, fail closed."""
import hashlib
import json
import os
import re
import subprocess
import sys
import uuid
import zipfile
from collections import Counter
from pathlib import Path

MANDATORY=(
 'ProjectSettings/ResourceGovernance.json','Tools/ResourceGovernance/resource_governance.py',
 'Tools/ResourceGovernance/README.md','Tools/ResourceGovernance/ResourceGovernance.lock.json','Assets/Editor/ResourceGovernance/ResourceGovernanceGate.cs',
 'Assets/Editor/ResourceGovernance/ResourceGovernanceGate.cs.meta',
 'Assets/Editor/TexturePackerTool.cs','Assets/Editor/TexturePackerTool.cs.meta',
 'Assets/Editor/addressable/AddressablesAutoBuilder.cs','Assets/Editor/addressable/AddressablesAutoBuilder.cs.meta')
OPTIONAL_REVIEW='Assets/Editor/ResourceGovernance/ResourceGovernanceReview.cs'

class GateError(ValueError):
    def __init__(self,message,code=3):
        self.code=code
        super().__init__(message)

def load(path):
    try:return json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except (OSError,ValueError) as e:raise GateError('Missing/invalid governance evidence: '+str(path)) from e

def ensure(value,message):
    if not value:raise GateError(message)

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def config_path():
    explicit=os.environ.get('GAME_BUILD_RELEASE_MACHINE_CONFIG')
    return Path(explicit) if explicit else Path(os.environ.get('LOCALAPPDATA',Path.home()/'.local/share'))/'GameBuildTools/game-build-release/machine.json'

def settings(project):
    project=Path(project).resolve();path=config_path()
    marker=any((project/x).exists() for x in MANDATORY[:2])
    if not path.exists():
        ensure(not marker,'B0 present but machine source/journal binding is missing')
        return None
    local=load(path);ensure(local.get('schemaVersion')==1,'Unsupported release machine configuration')
    platform_path=project/'ProjectSettings/FrameworkPlatform.json'
    platform=load(platform_path) if platform_path.exists() else {}
    identity=platform.get('buildRelease',{}).get('releaseTransaction',{})
    bindings=local.get('resourceGovernance',[])
    ensure(isinstance(bindings,list) and all(isinstance(b,dict) and b.get('sourceProject') for b in bindings),'Invalid governance bindings')
    matches=[b for b in bindings if (all(b.get(k) for k in ('projectId','environment','bootstrapUrl')) and (b.get('projectId'),b.get('environment'),b.get('bootstrapUrl'))==(identity.get('projectId'),identity.get('environment'),platform.get('bootstrapUrl'))) or Path(b['sourceProject']).resolve()==project]
    ensure(len(matches)<=1,'Ambiguous governance source binding')
    if not matches:
        ensure(not marker,'B0 project is not bound to an approved real source/journal root')
        return None
    b=matches[0]
    if b.get('machineSettingsFile'):
        machine=load(b['machineSettingsFile'])
        ensure(str(machine.get('schemaVersion'))=='1','Invalid resource machine settings')
        ensure(all(machine.get(k) for k in ('pythonExecutable','journalRoot','sourceProject')),'Incomplete resource machine settings')
        ensure(Path(machine.get('sourceProject','')).resolve()==Path(b['sourceProject']).resolve(),'Resource machine source mismatch')
        b={**b,'journalRoot':machine.get('journalRoot'),'python':machine.get('pythonExecutable')}
    for name in ('sourceProject','journalRoot','evidenceRoot'):
        ensure(b.get(name) and Path(b[name]).is_absolute(),'Missing absolute machine binding: '+name)
    source=Path(b['sourceProject']).resolve();journal=Path(b['journalRoot']).resolve()
    ensure(source.is_dir() and journal.is_dir(),'Approved source/journal directory missing')
    ensure(not journal.is_relative_to(source) and not journal.is_relative_to(project),'Resource journal must be durable outside source and candidate')
    b=dict(b);b['python']=b.get('python') or os.environ.get('RESOURCE_GOVERNANCE_PYTHON') or sys.executable
    ensure(Path(b['python']).is_file(),'Governance Python interpreter missing')
    return b

def dependencies(source):
    result=set(MANDATORY)
    # Conservative Editor dependency closure, including asmdef/rsp and metadata.
    for root in ('Assets/Editor','Tools/ResourceGovernance'):
        folder=source/root;ensure(folder.is_dir(),'Missing governance dependency directory: '+root)
        for f in folder.rglob('*'):
            if not f.is_file() or '__pycache__' in f.parts:continue
            rel=f.relative_to(source).as_posix()
            if rel in (OPTIONAL_REVIEW,OPTIONAL_REVIEW+'.meta'):continue
            if root.startswith('Tools/') or f.suffix in ('.cs','.meta','.asmdef','.asmref','.rsp','.txt'):result.add(rel)
    for rel in ('Assets/Editor/ResourceGovernance/ResourceMoveTransaction.cs','Assets/Editor/ResourceGovernance/ResourceMoveTransaction.cs.meta'):
        # Move utility is coupled with the production Gate per delivery contract.
        result.add(rel)
    return sorted(result)

def unfinished(source,journal):
    for file in journal.glob('*/journal.json'):
        row=load(file)
        if Path(row.get('project','')).resolve()==source and row.get('state') not in ('committed','rolled-back'):
            raise GateError('Unfinished real-source resource transaction: '+str(file),2)

def transaction_exception(project,binding,transaction_id):
    reference=binding.get('transactionExceptions',{}).get(transaction_id)
    if not reference:return None
    ensure(digest(reference['path'])==reference['sha256'],'Temporary exception approval changed')
    permit=load(reference['path'])
    ensure(permit.get('status')=='active' and permit.get('transactionId')==transaction_id,'Temporary exception inactive or belongs to another transaction')
    ensure(Path(permit['candidateProject']).resolve()==project,'Temporary exception belongs to another candidate')
    platform=load(project/'ProjectSettings/FrameworkPlatform.json');bound=platform['buildRelease']['releaseTransaction']
    ledger=load(Path(bound['stateRoot'])/'transactions.json')
    ensure(ledger['identity']=={'projectId':bound['projectId'],'environment':bound['environment'],'bootstrapUrl':platform['bootstrapUrl']},'Temporary exception ledger identity mismatch')
    tx=next((t for t in ledger['transactions'] if t['id']==transaction_id),{})
    ensure(tx.get('state') in ('registered','frozen','running') and tx.get('buildKind')=='content' and tx.get('intent')=='build-publish','Temporary exception expired or transaction not content-only')
    ensure(any(r['messageId']==permit['requestMessageId'] for r in tx.get('requests',[])) and permit.get('approvalMessageId'),'Temporary exception lacks request/approval provenance')
    ensure(digest(permit['archivePath'])==permit['archiveSha256'],'Approved historical archive changed')
    # Only the approved runtime patch may differ from the exact previous delivery.
    roots=('Assets/Scripts/','Assets/Art/','Assets/Prefab/','Assets/ConfigBin/','Assets/Resources/','Assets/Plugins/','Packages/')
    patches=permit['runtimePatches'];seen=set()
    with zipfile.ZipFile(permit['archivePath']) as archive:
        for name in archive.namelist():
            if name.endswith('/') or not name.startswith(roots):continue
            seen.add(name);target=project/name
            ensure(target.is_file() and target.resolve().is_relative_to(project),'Missing/unsafe historical runtime input: '+name)
            expected=patches.get(name) or hashlib.sha256(archive.read(name)).hexdigest()
            ensure(digest(target)==expected,'Unapproved runtime delta under temporary exception: '+name)
        for root in roots:
            for target in (project/root).rglob('*'):
                if target.is_file():ensure(target.relative_to(project).as_posix() in seen,'Added runtime input under temporary exception')
    ensure(set(patches)<=seen and permit.get('items'),'Incomplete historical exception binding')
    return permit

def approve_historical(project,report,permit):
    key=lambda row:(row['code'],row['path'],row.get('guid'),row.get('message'),tuple(sorted(row.get('relatedPaths',[]))))
    ensure(Counter(map(key,report['errors']))==Counter(map(key,permit['items'])),'New/changed/missing historical violation; temporary exception rejected')
    for row in permit['items']:
        target=project/row['path']
        ensure(target.is_file() and target.resolve().is_relative_to(project) and digest(target)==row['sha256'],'Historical exception file changed: '+row['path'])
    report=dict(report);report['approvedHistoricalErrors']=report['errors'];report['errors']=[]
    report['exceptionTransaction']=permit['transactionId']
    return report

def audit(project,binding,output,permit=None):
    cli=project/'Tools/ResourceGovernance/resource_governance.py'
    ensure(cli.is_file(),'Missing resource governance CLI: '+str(cli))
    command=[binding['python'],'-B',str(cli),'--project',str(project),'--output',str(output),'--journal-root',binding['journalRoot']]
    # No scope/active-journal/custom policy/preflight-plan options exist on this adapter.
    try:run=subprocess.run(command,capture_output=True,timeout=240)
    except (OSError,subprocess.TimeoutExpired) as e:raise GateError('Governance CLI failed to execute') from e
    if run.returncode not in (0,2,3):raise GateError('Unexpected governance CLI exit: '+str(run.returncode))
    if run.returncode==3 or (run.returncode==2 and permit is None):raise GateError('Resource governance rejected '+str(project)+' (exit '+str(run.returncode)+'); evidence '+str(output),run.returncode)
    report=load(output)
    ensure(report.get('toolVersion')=='1.0.0' and Path(report.get('project','')).resolve()==project and report.get('scope')==['Assets'],'Missing/incompatible/non-full governance report')
    ensure(all(isinstance(report.get(k),list) for k in ('errors','legacy','warnings')) and not report.get('error'),'Invalid governance evidence')
    if permit is not None:
        report=approve_historical(project,report,permit)
    ensure(not report['errors'],'Invalid successful governance evidence')
    return report

def reuse_key(project,source,binding,verified_input,permit):
    # Transaction already hashed/scanned declared inputs. Only excluded outputs remain.
    if source!=project or not verified_input or permit:return None
    roots={'Assets','Tools','ProjectSettings'}
    if (project/'Packages').exists():roots.add('Packages')
    if not roots<=set(verified_input.get('scopes',[])):return None
    excluded={}
    for rel in verified_input.get('excludes',[]):
        path=(project/rel).resolve()
        ensure(path.is_relative_to(project) and path!=project,'Unsafe excluded input path')
        files=[path] if path.is_file() else sorted(path.rglob('*')) if path.is_dir() else []
        excluded[rel]={str(f.relative_to(project)):digest(f) for f in files if f.is_file()}
    tools={f.name:digest(f) for f in Path(__file__).parent.glob('*.py')}
    value={'input':verified_input,'excluded':excluded,'binding':binding,'tools':tools}
    return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()


def reusable(previous,key):
    if not previous or not key:return None
    try:
        path=Path(previous['path'])
        if digest(path)!=previous['sha256']:return None
        receipt=load(path)
        if receipt.get('reuseKey')!=key or receipt.get('temporaryException'):return None
        for name in ('sourceReport','candidateReport'):
            if digest(receipt[name])!=receipt['reportHashes'][name]:return None
        return str(path)
    except (OSError,KeyError,GateError):return None


def check(project,input_manifest=None,phase='release-input',transaction_id=None,verified_input=None,previous=None):
    project=Path(project).resolve();b=settings(project)
    if b is None:return None
    if transaction_id in b.get('archivedPublish', {}):
        from archived_release_gate import check_archived
        return check_archived(sys.modules[__name__],project,b,transaction_id,input_manifest,previous)
    if transaction_id in b.get('pinnedContent', {}):
        from pinned_content_gate import bind_content
        b=bind_content(sys.modules[__name__],project,b,transaction_id,input_manifest)
    permit=transaction_exception(project,b,transaction_id)
    source=Path(b['sourceProject']).resolve();journal=Path(b['journalRoot']).resolve()
    # Explicit precheck does not let candidate path scoping hide real-source transactions.
    unfinished(source,journal)
    key=reuse_key(project,source,b,verified_input,permit)
    reused=reusable(previous,key)
    if reused:return reused
    required=dependencies(source)
    files={}
    for rel in required:
        a=source/rel;c=project/rel
        ensure(a.is_file() and c.is_file(),'Missing complete governance dependency: '+rel)
        ensure(a.resolve().is_relative_to(source) and c.resolve().is_relative_to(project),'Dependency escapes source/candidate')
        files[rel]=digest(a);ensure(digest(c)==files[rel],'Candidate governance dependency differs from real source: '+rel)
    policy=load(source/'ProjectSettings/ResourceGovernance.json')
    ensure(policy.get('toolVersion')=='1.0.0' and policy.get('schemaVersion')==1,'Incompatible governance policy')
    gate=(source/'Assets/Editor/ResourceGovernance/ResourceGovernanceGate.cs').read_text(encoding='utf-8-sig')
    ensure(re.search(r'ApiVersion\s*=\s*"1\.0"',gate),'Incompatible governance Editor API')
    if input_manifest:
        declared={e['path']:e['sha256'] for e in load(input_manifest)['files']}
        ensure(all(declared.get(k)==v for k,v in files.items()),'Frozen manifest omits or excludes governance dependencies; include Tools and complete Editor closure')
    output=Path(b['evidenceRoot'])/(phase+'-'+uuid.uuid4().hex);output.mkdir(parents=True,exist_ok=False)
    source_report=audit(source,b,output/'source.json')
    unfinished(source,journal)
    candidate_path=output/'source.json' if source==project and permit is None else output/'candidate.json'
    candidate_report=source_report if candidate_path==output/'source.json' else audit(project,b,candidate_path,permit)
    unfinished(source,journal)
    ensure(all(digest(source/k)==v and digest(project/k)==v for k,v in files.items()),'Governance dependencies changed during preflight')
    receipt={'phase':phase,'sourceProject':str(source),'candidateProject':str(project),'journalRoot':str(journal),'apiVersion':'1.0','toolVersion':'1.0.0','dependencies':files,'sourceReport':str(output/'source.json'),'candidateReport':str(candidate_path),'sourceLegacy':len(source_report['legacy']),'candidateLegacy':len(candidate_report['legacy']),'warnings':len(source_report['warnings'])+len(candidate_report['warnings'])}
    ensure(key==reuse_key(project,source,b,verified_input,permit),'Excluded inputs or release tools changed during preflight')
    receipt['reuseKey']=key
    receipt['reportHashes']={name:digest(receipt[name]) for name in ('sourceReport','candidateReport')}
    if candidate_path==output/'source.json':receipt['warnings']=len(source_report['warnings'])
    if permit:receipt['temporaryException']={'transactionId':transaction_id,'approvalMessageId':permit['approvalMessageId'],'approvedHistoricalErrors':len(candidate_report['approvedHistoricalErrors']),'rawCandidateExitCode':2,'expiry':'transaction terminal or approval removed; no source audit exceptions'}
    path=output/'preflight.json';path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    return str(path)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',required=True);p.add_argument('--transaction');a=p.parse_args()
    try:print(json.dumps({'governanceEvidence':check(a.project,transaction_id=a.transaction)},ensure_ascii=False))
    except GateError as error:p.exit(error.code,str(error)+'\n')
