import { test } from 'node:test';
import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { dispatchPaidAlerts } from '../../workers/sos-paid-alerts.mjs';

const clock = new Date('2026-10-28T00:30:00Z');
function fixture(status='payment_confirmed', claimed=false) {
  const db = new DatabaseSync(':memory:');
  db.exec([
    'CREATE TABLE orders(id TEXT PRIMARY KEY,public_order_id TEXT,status TEXT,assigned_operator_id TEXT,payment_confirmed_at TEXT,total_minor INTEGER,currency TEXT);',
    'CREATE TABLE payment_verifications(order_id TEXT,provider TEXT,voided_at TEXT,amount_minor INTEGER,currency TEXT);',
    'CREATE TABLE notification_outbox(id INTEGER PRIMARY KEY AUTOINCREMENT,order_id TEXT,channel TEXT,destination_key TEXT,template_key TEXT,payload_json TEXT,priority INTEGER,status TEXT,attempt_count INTEGER DEFAULT 0,next_attempt_at TEXT,created_at TEXT,updated_at TEXT,last_error TEXT,sent_at TEXT);',
    "CREATE UNIQUE INDEX ux_paid_outbox_once ON notification_outbox(order_id,template_key,destination_key) WHERE template_key IN ('paid_order_priority','paid_order_unclaimed');"
  ].join('\n'));
  db.prepare('INSERT INTO orders VALUES(?,?,?,?,?,?,?)').run('order-1','SOS-SYN-1',status,claimed?'op-ripon':null,'2026-10-28T00:00:00Z',150000,'BDT');
  db.prepare('INSERT INTO payment_verifications VALUES(?,?,?,?,?)').run('order-1','bkash',null,150000,'BDT');
  db.prepare("INSERT INTO notification_outbox (order_id,channel,destination_key,template_key,payload_json,priority,status,next_attempt_at,created_at,updated_at) VALUES (?,?,?,?,?,0,'pending',?,?,?)").run('order-1','webhook','sos-ripon','paid_order_priority','{}','2026-10-28T00:01:00Z','2026-10-28T00:00:00Z','2026-10-28T00:00:00Z');
  return {
    prepare(sql) { return { bind(...args) { return {
      async run() { const r=db.prepare(sql).run(...args);return {meta:{changes:r.changes}}; },
      async all() { return {results:db.prepare(sql).all(...args)}; }
    }; } }; },
    rows(sql) { return db.prepare(sql).all(); }
  };
}

test('paid alert is not marked sent without a verified destination', async()=>{
  const DB=fixture();
  const result=await dispatchPaidAlerts({DB},clock,()=>{throw Error('must not fetch')});
  assert.equal(result.sent,0);
  assert.equal(DB.rows("SELECT status FROM notification_outbox WHERE destination_key='sos-ripon'")[0].status,'pending');
});

test('verified paid order alerts once to Ripon, then escalates unclaimed to EMON', async()=>{
  const DB=fixture();let calls=[];
  const env={DB,SOS_RIPON_ALERT_WEBHOOK:'https://hooks.example.test/r',SOS_EMON_ALERT_WEBHOOK:'https://hooks.example.test/e'};
  const send=async(_url,req)=>{calls.push(JSON.parse(req.body));return {ok:true}};
  assert.equal((await dispatchPaidAlerts(env,clock,send)).sent,2);
  assert.equal((await dispatchPaidAlerts(env,clock,send)).sent,0);
  assert.deepEqual(calls.map(x=>x.event).sort(),['saveonsub.paid_unclaimed','saveonsub.payment_verified']);
  for(const payload of calls) {
    assert.equal(payload.order_id,'SOS-SYN-1');
    assert.equal(payload.provider,'bkash');
    assert.ok(!JSON.stringify(payload).includes('customer_phone'));
    assert.ok(!JSON.stringify(payload).includes('transaction_id'));
  }
});

test('claimed order gets no escalation; refunded order gets no external alert', async()=>{
  const claimed=fixture('payment_confirmed',true);
  const refunded=fixture('refunded',false);
  const env=(DB)=>({DB,SOS_RIPON_ALERT_WEBHOOK:'https://hooks.example.test/r',SOS_EMON_ALERT_WEBHOOK:'https://hooks.example.test/e'});
  let calls=0;
  const send=async()=>{calls++;return {ok:true}};
  assert.equal((await dispatchPaidAlerts(env(claimed),clock,send)).sent,1);
  assert.equal(claimed.rows("SELECT count(*) AS n FROM notification_outbox WHERE destination_key='sos-emon'")[0].n,0);
  assert.equal((await dispatchPaidAlerts(env(refunded),clock,send)).sent,0);
  assert.equal(calls,1);
  assert.equal(refunded.rows("SELECT status FROM notification_outbox WHERE destination_key='sos-ripon'")[0].status,'dead');
});
