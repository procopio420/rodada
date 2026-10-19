import test from 'node:test';
import assert from 'node:assert/strict';
import { currentTaskTarget } from '../lib/client/dispatch-target.ts';
const tables = [{id:'table-a',active_occupancy:{id:'occupancy-a',generation:4}}];
const target = {kind:'TAB',tab_id:'tab-b',table_id:'table-a',occupancy_id:'occupancy-a',generation:4};
const task = {id:'task-a',task_type:'SERVICE_REQUEST',state:'OPEN',destination_label:'Mesa 99',target_version:1,target,claimed_by_id:null};
test('canonical target survives unrelated destination label; label never resolves identity',()=>{
  assert.deepEqual(currentTaskTarget(task,tables),target);
  assert.equal(currentTaskTarget({...task,target:undefined},tables),null);
});
test('stale occupancy, generation, released table and unsupported target version fail safely',()=>{
  for(const changed of [{...target,generation:3},{...target,occupancy_id:'old'}, {...target,tab_id:null}]) assert.equal(currentTaskTarget({...task,target:changed},tables),null);
  assert.equal(currentTaskTarget(task,[]),null);
  assert.equal(currentTaskTarget({...task,target_version:2},tables),null);
});
test('TABLE fallback stays explicit and never chooses a tab; no-table TAB supported',()=>{
  const tableTarget={...target,kind:'TABLE',tab_id:null};
  assert.deepEqual(currentTaskTarget({...task,target:tableTarget},tables),tableTarget);
  const counter={...target,table_id:null,occupancy_id:null,generation:null};
  assert.deepEqual(currentTaskTarget({...task,target:counter},[]),counter);
  assert.equal(currentTaskTarget({...task,target:{...counter,kind:'TABLE'}},[]),null);
});
