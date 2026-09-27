(function(){
  const cfg=window.SOS_ORDER_CONFIG||{};
  let turnstileToken='';
  let widgetId=null;

  function inject(){
    const paybox=document.getElementById('paybox');
    if(!paybox||document.getElementById('sos-order-contact')) return;

    const box=document.createElement('div');
    box.id='sos-order-contact';
    box.innerHTML=`
      <div style="margin-top:18px;border-top:1px solid var(--line);padding-top:16px">
        <h3 style="font-size:16px;margin-bottom:8px">Contact for delivery</h3>
        <label for="sos-name">Name</label>
        <input id="sos-name" autocomplete="name" placeholder="Your name">
        <label for="sos-phone">WhatsApp / phone *</label>
        <input id="sos-phone" autocomplete="tel" inputmode="tel" placeholder="01XXXXXXXXX">
        <label for="sos-email">Email (optional)</label>
        <input id="sos-email" autocomplete="email" inputmode="email" placeholder="you@example.com">
        <div id="sos-turnstile" style="margin-top:12px"></div>
        <p id="sos-order-mode" style="font-size:12.5px;color:var(--muted);margin-top:8px"></p>
      </div>`;
    const button=paybox.querySelector('button.btn-wa');
    if(button) paybox.insertBefore(box,button);
    else paybox.appendChild(box);

    const mode=document.getElementById('sos-order-mode');
    if(cfg.serverCheckoutEnabled&&cfg.turnstileSiteKey){
      mode.textContent='Secure server order mode enabled. Your order will enter the staff fulfillment queue.';
      loadTurnstile();
    }else{
      mode.textContent='Manual order mode: WhatsApp handoff only until the secure order backend is activated.';
    }
  }

  function loadTurnstile(){
    if(!cfg.turnstileSiteKey) return;
    if(window.turnstile){renderTurnstile();return;}
    const s=document.createElement('script');
    s.src='https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';
    s.defer=true;
    s.onload=renderTurnstile;
    document.head.appendChild(s);
  }

  function renderTurnstile(){
    if(!window.turnstile||widgetId!==null) return;
    widgetId=window.turnstile.render('#sos-turnstile',{
      sitekey:cfg.turnstileSiteKey,
      theme:'auto',
      appearance:'interaction-only',
      callback:function(token){turnstileToken=token;},
      'expired-callback':function(){turnstileToken='';},
      'error-callback':function(){turnstileToken='';}
    });
  }

  function contact(){
    return {
      name:(document.getElementById('sos-name')?.value||'').trim(),
      phone:(document.getElementById('sos-phone')?.value||'').trim(),
      email:(document.getElementById('sos-email')?.value||'').trim(),
      locale:document.documentElement.lang||'en'
    };
  }

  function validateContact(c){
    if(!c.phone||c.phone.replace(/\D/g,'').length<10){
      toast('Please enter your WhatsApp / phone number');
      document.getElementById('sos-phone')?.focus();
      return false;
    }
    return true;
  }

  function manualFallback(reason){
    const c=contact();
    const cart=cartGet();
    const lines=cart.map(i=>`• ${i.name} — ${i.plan} ×${i.qty} = ৳${i.bdt*i.qty}`).join('\n');
    const msg=`🛒 MANUAL ORDER REQUEST\n${lines}\nTOTAL DISPLAYED: ৳${cartTotal()}\nPayment: ${typeof PAY!=='undefined'?PAY:'not selected'}\nCustomer: ${c.name||'-'} · ${c.phone||'-'}\nReason: ${reason}\nPlease confirm price/access/payment before fulfillment.`;
    toast('Secure server order was not created. Opening manual WhatsApp handoff.');
    window.open(waLink(msg),'_blank');
  }

  async function createServerOrder(){
    const cart=cartGet();
    if(!cart.length){toast('Cart is empty');return null;}
    const c=contact();
    if(!validateContact(c)) return null;

    const unsupported=cart.find(i=>!i.plan_id);
    if(unsupported){
      manualFallback('This cart item has no governed plan identifier yet');
      return null;
    }
    if(!cfg.serverCheckoutEnabled||!cfg.turnstileSiteKey){
      manualFallback('Secure order backend is not activated yet');
      return null;
    }
    if(!turnstileToken){
      toast('Please complete the security check');
      return null;
    }

    const txn=(document.getElementById('txn')?.value||'').trim();
    const idempotencyKey=crypto.randomUUID()+crypto.randomUUID();
    const body={
      idempotency_key:idempotencyKey,
      turnstile_token:turnstileToken,
      payment_method:(typeof PAY!=='undefined'?PAY:'bKash'),
      payment_reference:txn,
      customer:c,
      items:cart.map(i=>({product_id:i.id,plan_id:i.plan_id,quantity:i.qty}))
    };

    let response;
    try{
      response=await fetch((cfg.apiBase||'')+'/api/orders',{
        method:'POST',
        headers:{'content-type':'application/json'},
        body:JSON.stringify(body)
      });
    }catch(e){
      manualFallback('Order API network error');
      return null;
    }

    let data={};
    try{data=await response.json();}catch(e){}
    if(!response.ok||!data.ok){
      if(widgetId!==null&&window.turnstile){window.turnstile.reset(widgetId);turnstileToken='';}
      manualFallback('Order API error: '+(data.error||response.status));
      return null;
    }

    const current=cartGet();
    saveOrder({
      oid:data.order_id,
      kind:'order',
      method:(typeof PAY!=='undefined'?PAY:'bKash'),
      txn:txn,
      total:Number(data.total_bdt||0),
      items:current.map(i=>({name:i.name,plan:i.plan,plan_id:i.plan_id,qty:i.qty,bdt:i.bdt})),
      tracking_token:data.tracking_token,
      staff_notification:data.staff_notification,
      at:new Date().toISOString()
    });
    cartSet([]);
    return data;
  }

  window.confirmWA=async function(){
    const data=await createServerOrder();
    if(!data) return;
    const c=contact();
    const msg=`🛒 ORDER ${data.order_id}\nServer order created and queued for staff.\nTotal: ৳${Number(data.total_bdt).toLocaleString()}\nCustomer: ${c.name||'-'} · ${c.phone}\nPlease verify payment and fulfill this order.`;
    window.open(waLink(msg),'_blank');
    location.href='order.html';
  };

  document.addEventListener('DOMContentLoaded',inject);
})();