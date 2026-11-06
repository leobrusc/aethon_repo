"""Opaque storage contracts with synthetic fixtures only; no OS/native claim."""
import ast
import copy
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

import pytest

from aethon.pilot_governance import canonical, digest
from aethon.pilot_storage import PrivateRunStore
from aethon.pilot_storage_backend import (CorruptCheckpoint, InvalidCapability, InvalidIdentifier,
    MissingObject, OperationId, ResourceBudget, ResourceLimit, RunCapability, StaleHead,
    StorageCollision, StorageInterrupted, StorageKey, WriterBusy, bounded_json)
from pilot_memory_backend import MemoryBackend
from test_pilot_collector import collector, deny_network, setup_run, SyntheticDriver

__all__ = ["deny_network", "setup_run"]


def test_full_120_slot_collection_reopen_and_independent_review_pending(setup_run):
    d=SyntheticDriver();run=collector(setup_run, d, judge=None);summary=run.run()
    assert summary['states']=={'evaluation_pending':96,'reused':24}
    run.store.close();resumed=collector(setup_run,d,judge=None)
    assert resumed.run()==summary and d.calls==96
    assert not hasattr(resumed.store,'path') and not hasattr(resumed.store,'objects')


def test_backend_and_facade_never_use_filesystem(setup_run, monkeypatch):
    import builtins
    import os
    def forbidden(*a,**k):pytest.fail('Persistence pathname I/O escaped backend contract')
    with monkeypatch.context() as m:
        m.setattr(builtins,'open',forbidden);m.setattr(os,'open',forbidden)
        for name in ['open','read_bytes','write_bytes','mkdir','unlink','glob','lstat','stat']:
            m.setattr(Path,name,forbidden)
        store=setup_run['store']()
        with store.writer():
            key=store.put({'synthetic':True});assert store.get(key)=={'synthetic':True}
            slot=next(iter(store.slots));store.pointer(slot+'.response',{'reference':key})
            store.transition(slot,'started',attempted=True)
        store.close();other=setup_run['store']();assert other.sequence==1;other.close()


@pytest.mark.parametrize('bad',['../escape','C:\\private','/absolute','a'*64+'.request/..','CON', 'x\x00y','x:y','A'*64])
def test_unstructured_identifiers_rejected(setup_run,bad):
    s=setup_run['store']()
    with pytest.raises(CorruptCheckpoint):s.pointer(bad)
    with pytest.raises(InvalidIdentifier):StorageKey('object',bad)


def test_unknown_well_formed_checkpoint_cannot_expand_inventory(setup_run):
    s=setup_run['store']()
    with pytest.raises(InvalidIdentifier):s.pointer('f'*64+'.response',{'x':1})
    with pytest.raises(InvalidIdentifier):s.pointer(next(iter(s.slots))+'.request')


@pytest.mark.parametrize('forged',[None,True,'approved',{},RunCapability()])
def test_capabilities_cannot_be_issued_by_flags(setup_run,forged):
    with pytest.raises(InvalidCapability):setup_run['backend'].read_head(forged)


def test_foreign_backend_and_copied_capabilities_rejected(setup_run):
    s=setup_run['store']()
    with pytest.raises(InvalidCapability):MemoryBackend().read_head(s.run_capability)
    with pytest.raises(InvalidCapability):s.backend.read_head(copy.copy(s.run_capability))
    s.close();s.close()
    with pytest.raises(InvalidCapability):s.backend.read_head(s.run_capability)
    with pytest.raises(PermissionError):s.get('a'*64)


def test_manifest_reads_are_defensive_and_complete_binding_enforced(setup_run):
    s=setup_run['store']();m=s.manifest;m['config']['generation']['seed']+=1
    assert s.manifest!=m
    with pytest.raises(CorruptCheckpoint):PrivateRunStore(manifest=m,authorization=s.authorization,backend=s.backend)
    with pytest.raises(StorageCollision):PrivateRunStore(manifest=setup_run['manifest'],authorization=s.authorization,backend=s.backend,budget=ResourceBudget(events=3000))


def test_idempotent_bytes_and_checkpoint_overwrite_rejection(setup_run):
    s=setup_run['store']();key=s.put({'synthetic':True});assert key==s.put({'synthetic':True})
    checkpoint=next(iter(s.slots))+'.response';s.pointer(checkpoint,{'reference':key})
    s.pointer(checkpoint,{'reference':key})
    with pytest.raises(StorageCollision):s.pointer(checkpoint,{'reference':'a'*64})


def test_logical_concurrency_and_owned_lease_cleanup(setup_run):
    a=setup_run['store']();b=setup_run['store']()
    with a.writer():
        with ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(b.put,{'cannot':'race'})
            with pytest.raises(WriterBusy):future.result()
        b.close();assert a.backend.writer_owned(a.run_capability)
    a.close();c=setup_run['store']()
    with c.writer():assert c.backend.writer_owned(c.run_capability)


def test_same_operation_different_bytes_and_stale_head(setup_run):
    s=setup_run['store']();backend=s.backend;op=OperationId('a'*64)
    raw=canonical({'kind':'suspend','reason':'synthetic'})
    first=backend.append_event(s.run_capability,0,None,raw,op)
    assert backend.append_event(s.run_capability,0,None,raw,op)==first
    with pytest.raises(StorageCollision):backend.append_event(s.run_capability,0,None,canonical({'kind':'suspend','reason':'different'}),op)
    with pytest.raises(StaleHead):backend.append_event(s.run_capability,0,None,raw,OperationId('b'*64))
    s.load();assert s.suspended=='synthetic' and s.sequence==1


@pytest.mark.parametrize('kind',['put','append'])
@pytest.mark.parametrize('phase',['before_commit','after_commit'])
def test_fault_boundaries_and_idempotent_retry(setup_run,kind,phase):
    s=setup_run['store']();s.backend.fail_next(kind,phase)
    if kind=='put':
        with pytest.raises(StorageInterrupted):s.put({'fixture':'synthetic'})
        key=s.put({'fixture':'synthetic'});assert s.get(key)=={'fixture':'synthetic'}
        assert len(s.backend.inspect(s.run_capability)['objects'])==1
    else:
        with pytest.raises(StorageInterrupted):s.suspend('synthetic')
        s.suspend('synthetic');assert s.sequence==1
    resumed=setup_run['store']();assert resumed.sequence==(1 if kind=='append' else 0)


def test_missing_object_and_checkpoint_corruption_are_explicit(setup_run):
    s=setup_run['store']()
    with pytest.raises(MissingObject):s.get('b'*64)
    name=next(iter(s.slots))+'.response';s.pointer(name,{'synthetic':True})
    state=s.backend.inspect(s.run_capability);k=next(iter(state['objects']))
    state['objects'][k]=(b'corruption',state['objects'][k][1])
    with pytest.raises(CorruptCheckpoint):s.pointer(name)
    with pytest.raises(CorruptCheckpoint):setup_run['store']()


@pytest.mark.parametrize('change',['gap','truncate','foreign','partial-bytes'])
def test_conservative_recovery_rejects_inconsistent_journal(setup_run,change):
    s=setup_run['store']();s.suspend('first');s.suspend('second');state=s.backend.inspect(s.run_capability)
    if change=='gap':state['journal'].pop(0)
    if change=='truncate':state['journal'].pop()
    if change=='foreign':
        from aethon.pilot_storage_backend import sealed,unseal
        value=unseal(state['journal'][0]);value['binding_sha256']='a'*64;state['journal'][0]=canonical(sealed(value))
    if change=='partial-bytes':state['journal'][0]=state['journal'][0][:-1]
    with pytest.raises(CorruptCheckpoint):setup_run['store']()


@pytest.mark.parametrize('field,value',[('objects',0),('events',True),('event_bytes',-1),('total_bytes',10**15)])
def test_invalid_resource_budgets_rejected(field,value):
    with pytest.raises(ResourceLimit):ResourceBudget(**{field:value})


def test_object_event_total_and_structure_quotas(setup_run):
    b=MemoryBackend();s=PrivateRunStore(manifest=setup_run['manifest'],authorization=setup_run['permission'],backend=b,
                                      budget=ResourceBudget(objects=1,events=1,object_bytes=1024))
    s.put({'first':True})
    with pytest.raises(ResourceLimit):s.put({'second':True})
    with pytest.raises(ResourceLimit):s.put({'oversized':'x'*2048})
    s.suspend('first')
    with pytest.raises(ResourceLimit):s.suspend('second')
    assert b.read_head(s.run_capability).sequence==1
    value={}
    for _ in range(50):value={'nested':value}
    with pytest.raises(ResourceLimit):s.put(value)
    with pytest.raises(CorruptCheckpoint):bounded_json({'nan':float('nan')},1024)
    with pytest.raises(ResourceLimit):bounded_json([None]*100001,2*1024*1024)


def test_cli_never_selects_memory_or_invokes_native_bootstrap(monkeypatch):
    import aethon.pilot_runtime as runtime
    monkeypatch.setattr(runtime,'inspect_runtime',lambda *a,**k:pytest.fail('No productive bootstrap'))
    with pytest.raises(PermissionError):runtime.collect_runtime('.',launch_path='synthetic',backend='memory')
    assert 'pilot_memory_backend' not in Path(runtime.__file__).read_text(encoding='utf8')


def test_facade_ast_has_no_path_persistence_and_history_is_preserved():
    import aethon.pilot_storage_facade as facade
    source=Path(facade.__file__).read_text(encoding='utf8');tree=ast.parse(source)
    assert not any(isinstance(n,ast.Import) and any(x.name in {'os','pathlib','shutil'} for x in n.names) for n in ast.walk(tree))
    assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='open' for n in ast.walk(tree))
    root=Path(__file__).resolve().parents[1];archive=root/'docs/science/storage-capabilities-v1/historical'
    for name,record in json.loads((archive/'index.json').read_text()).items():
        assert digest((archive/record['archive']).read_bytes())==record['sha256']


@pytest.mark.parametrize('change',['slot-id','arm','slot-fingerprint','schedule'])
def test_malformed_120_slot_manifest_never_opens(setup_run,change):
    m=copy.deepcopy(setup_run['manifest'])
    if change=='slot-id':m['slots'][0]['slot_id']='a'*64
    if change=='arm':m['slots'][0]['condition']='B5'
    if change=='slot-fingerprint':m['slots'][0]['fingerprint']='a'*64
    if change=='schedule':m['schedule'][0]=m['schedule'][1]
    with pytest.raises(CorruptCheckpoint):PrivateRunStore(manifest=m,authorization=setup_run['permission'],backend=MemoryBackend())


def test_fake_authorization_never_mints_backend_capability(setup_run):
    class Fake:
        def check(self,*a):pass
    with pytest.raises(InvalidCapability):MemoryBackend().open_run(Fake(),canonical(setup_run['manifest']))


def test_expired_authorization_still_allows_owned_cleanup(setup_run,monkeypatch):
    from aethon.pilot_governance import Authorization
    s=setup_run['store']();cap=s.run_capability
    def expired(*a):raise PermissionError('synthetic expired authorization')
    with s.backend.writer(cap):
        monkeypatch.setattr(Authorization,'check',expired)
        with pytest.raises(PermissionError):s.backend.read_head(cap)
        s.close();s.close()
    assert cap not in s.backend._handles


def test_failed_recovery_cannot_export_partial_accounting(setup_run):
    s=setup_run['store']();s.suspend('synthetic');s.backend.inspect(s.run_capability)['journal'].clear()
    with pytest.raises(CorruptCheckpoint):s.load()
    with pytest.raises(CorruptCheckpoint):s.summary()
    s.close()


def test_total_bytes_and_operation_count_are_bounded(setup_run):
    a=setup_run['store']();minimum=len(a._manifest_raw)
    b=PrivateRunStore(manifest=setup_run['manifest'],authorization=a.authorization,backend=MemoryBackend(),
                      budget=ResourceBudget(total_bytes=minimum+512))
    with pytest.raises(ResourceLimit):b.put({'value':'x'*1024})
    assert not b.backend.inspect(b.run_capability)['objects']
    c=PrivateRunStore(manifest=setup_run['manifest'],authorization=a.authorization,backend=MemoryBackend(),
                      budget=ResourceBudget(operations=1))
    key=c.put({'first':True});assert c.put({'first':True})==key
    with pytest.raises(ResourceLimit):c.put({'second':True})


def test_backend_rejects_unsupported_manifest_version(setup_run):
    m=copy.deepcopy(setup_run['manifest']);m['schema']='unsupported'
    with pytest.raises(CorruptCheckpoint):PrivateRunStore(manifest=m,authorization=setup_run['permission'],backend=MemoryBackend())


def test_legacy_path_hook_cannot_activate_even_with_synthetic_backend(setup_run):
    f=setup_run
    with pytest.raises(PermissionError):PrivateRunStore(f['private'],f['manifest'],f['permission'],[f['repo']],f['observation'],backend=f['backend'])
    assert not (f['private']/'synthetic-run').exists()


def test_object_cannot_be_replayed_under_different_capability_budget(setup_run):
    a=setup_run['store']();key=a.put({'same':'scientific bytes'})
    b=PrivateRunStore(manifest=setup_run['manifest'],authorization=a.authorization,backend=MemoryBackend(),
                      budget=ResourceBudget(events=3000))
    assert b.put({'same':'scientific bytes'}) != key
    # Trusted synthetic attacker copies a complete otherwise valid object record.
    stored=a.backend.inspect(a.run_capability)['objects'][StorageKey('object',key)]
    target=b.backend.inspect(b.run_capability);target['objects'][StorageKey('object',key)]=stored;target['used']+=len(stored[0])
    with pytest.raises(CorruptCheckpoint):b.get(key)
