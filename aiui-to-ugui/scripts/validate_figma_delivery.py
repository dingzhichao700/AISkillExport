"""Validate local Figma development-plugin packaging, not design correctness."""
from pathlib import Path
import argparse,json,hashlib
def validate(directory):
 root=Path(directory).resolve();entry=root/'manifest.json'
 if not entry.is_file():raise ValueError('Missing standard manifest.json entry')
 d=json.loads(entry.read_text('utf-8-sig'))
 for key in ['name','id','api','main','editorType']:
  if not d.get(key):raise ValueError('Missing manifest field: '+key)
 if not isinstance(d['editorType'],list):raise ValueError('editorType must be a list')
 refs=[d['main']];ui=d.get('ui')
 if isinstance(ui,dict):refs+=list(ui.values())
 elif ui is not None:refs.append(ui)
 files={}
 for ref in refs:
  if not isinstance(ref,str) or not ref:raise ValueError('Invalid dependency reference')
  raw=Path(ref);p=(root/raw).resolve()
  if raw.is_absolute() or not p.is_relative_to(root):raise ValueError('Dependency escapes plugin package: '+ref)
  if not p.is_file():raise ValueError('Missing dependency: '+ref)
  files[ref]=hashlib.sha256(p.read_bytes()).hexdigest()
 return {'packagingPassed':True,'pluginJsonPath':str(entry),'pluginDirectory':str(root),'pluginDependencies':files,'scope':'Manifest and declared main/ui only; separately check other assets, script syntax and complete reconstruction','actualImport':'not asserted','visualApproval':'not asserted'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--report');a=p.parse_args();r=validate(a.directory);s=json.dumps(r,ensure_ascii=False,indent=2)
 if a.report:Path(a.report).write_text(s,'utf-8')
 print(s)
