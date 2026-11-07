"""Exercise lazy and initialized Adam state across Gaussian duplication/culling."""
import ast
import json
from pathlib import Path
import torch

tree=ast.parse(Path('models/gaussians/basics.py').read_text())
helpers=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['remove_from_optim','dup_in_optim']]
scope={'torch':torch}
exec(compile(ast.Module(body=helpers,type_ignores=[]),'<optimizer_helpers>','exec'),scope)
cases=[]
for initialized in [False,True]:
    p=torch.nn.Parameter(torch.arange(6,dtype=torch.float32).reshape(3,2))
    opt=torch.optim.Adam([{'params':[p],'name':'test'}],lr=0.01)
    if initialized:
        p.square().sum().backward(); opt.step(); opt.zero_grad()
    old=opt.state.get(p,{}).get('exp_avg')
    old=old.clone() if old is not None else None
    mask=torch.tensor([True,False,False])
    q=torch.nn.Parameter(torch.cat([p.detach(),p.detach()[mask].repeat(2,1)]))
    scope['dup_in_optim'](opt,mask,{'test':[q]},2)
    assert opt.param_groups[0]['params'][0] is q
    if initialized:
        assert torch.equal(opt.state[q]['exp_avg'][:3],old)
        assert not opt.state[q]['exp_avg'][3:].any()
    q.square().sum().backward(); opt.step(); opt.zero_grad()
    assert torch.isfinite(q).all()
    deleted=torch.tensor([False,True,False,False,True])
    before=opt.state[q]['exp_avg'].clone()
    r=torch.nn.Parameter(q.detach()[~deleted])
    scope['remove_from_optim'](opt,deleted,{'test':[r]})
    assert torch.equal(opt.state[r]['exp_avg'],before[~deleted])
    r.square().sum().backward(); opt.step()
    assert torch.isfinite(r).all()
    cases.append({'initialized':initialized,'duplication_and_culling':True})
p=torch.nn.Parameter(torch.ones(3,2)); opt=torch.optim.Adam([{'params':[p],'name':'test'}])
deleted=torch.tensor([True,False,False]); q=torch.nn.Parameter(p.detach()[~deleted])
scope['remove_from_optim'](opt,deleted,{'test':[q]})
q.sum().backward(); opt.step()
assert torch.isfinite(q).all()
print(json.dumps({'passed':True,'cases':cases,'lazy_culling':True}))
