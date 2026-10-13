/* Commonstead — original browser client. No external scripts or telemetry. */
'use strict';
const $ = (selector, root = document) => root.querySelector(selector);
const app = $('#app');
const modal = $('#modal');
const state = { session: null, page: 'overview', query: '', offset: 0, limit: 25, members: [], accounts: [], opportunities: [] };
const stages = ['prospecting', 'qualification', 'proposal', 'negotiation', 'closed_won', 'closed_lost'];
const titles = {overview:'Overview',accounts:'Accounts',contacts:'Contacts',leads:'Leads',opportunities:'Opportunities',activities:'Activities',team:'Team & access',audit:'Audit history'};
const singular = {accounts:'account',contacts:'contact',leads:'lead',opportunities:'opportunity',activities:'activity'};
const symbols = {overview:'◫',accounts:'▥',contacts:'♧',leads:'↗',opportunities:'◇',activities:'☷',team:'⊕',audit:'≡'};
let noticeTimer;
let renderNumber = 0;
let invitationToken = new URLSearchParams(location.search).get('invite');
if (invitationToken) history.replaceState(null, '', location.pathname);

// Values from the API are always added as text nodes, never parsed as HTML.
function h(tag, props = {}, ...children) {
  const element = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (key === 'value') continue;
    if (key.startsWith('on')) element.addEventListener(key.slice(2).toLowerCase(), value);
    else if (key === 'className') element.className = value;
    else if (value !== false && value !== null && value !== undefined) element.setAttribute(key, value === true ? '' : String(value));
  }
  for (const child of children.flat(Infinity)) {
    if (child !== null && child !== undefined && child !== false) element.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  if ('value' in props) element.value = props.value ?? '';
  return element;
}
function button(text, onClick, style = '', props = {}) { return h('button', {type:'button',className:`button ${style}`,onClick,...props}, text); }
function pretty(value) { return String(value ?? '').replaceAll('_',' ').replace(/\b\w/g, c => c.toUpperCase()); }
function money(cents) { return new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format((cents || 0)/100); }
function fullMoney(cents) { return new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format((cents || 0)/100); }
function person(id) { return state.members.find(member => member.id === id)?.name || 'Unassigned'; }
function accountName(id) { return state.accounts.find(account => account.id === id)?.name || '—'; }
function canWrite() { return state.session?.user.role !== 'viewer'; }
function canAdmin() { return ['owner','admin'].includes(state.session?.user.role); }
function badge(value) { return h('span',{className:`badge ${['closed_won','qualified','done','owner'].includes(value)?'green':['closed_lost','disqualified'].includes(value)?'red':''}`},pretty(value)); }
function toast(message, error = false) {
  clearTimeout(noticeTimer);
  const notice = $('#notice');
  notice.textContent = message;
  notice.className = `visible${error?' error':''}`;
  notice.setAttribute('role', error ? 'alert' : 'status');
  noticeTimer = setTimeout(() => { notice.className = ''; }, 7000);
}
async function api(path, method = 'GET', body = undefined) {
  const headers = {Accept:'application/json'};
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (method !== 'GET' && state.session?.csrf_token) headers['X-CSRF-Token'] = state.session.csrf_token;
  let response;
  try { response = await fetch(path,{method,headers,credentials:'same-origin',body:body === undefined?undefined:JSON.stringify(body)}); }
  catch { throw new Error('Cannot reach Commonstead. Check that the local server is running, then try again.'); }
  let data;
  try { data = await response.json(); } catch { throw new Error('The server returned an unreadable response.'); }
  if (!response.ok) {
    if (response.status === 401 && state.session) {
      state.session = null;
      modal.close();
      renderAuth('login');
    }
    const problem = new Error(data.error?.message || `Request failed (${response.status}).`);
    problem.status = response.status;
    problem.details = data.error?.details;
    throw problem;
  }
  return data;
}
function showFormError(form, error) {
  let box = $('.error-box', form);
  if (!box) { box = h('div',{className:'error-box',role:'alert',tabindex:'-1'}); form.prepend(box); }
  box.textContent = error.message;
  box.focus();
}
async function submitting(form, task) {
  const submit = $('button[type="submit"]', form);
  if (submit?.disabled) return;
  if (submit) submit.disabled = true;
  $('.error-box',form)?.remove();
  try { await task(); } catch (error) { showFormError(form,error); }
  finally { if (submit) submit.disabled = false; }
}
function inputField(label, name, type = 'text', value = '', options = {}) {
  const id = `field-${name}`;
  const {hint,choices,wide,...props} = options;
  let control;
  if (type === 'select') control = h('select',{id,name,value,...props},choices.map(choice => h('option',{value:choice.value},choice.label)));
  else if (type === 'textarea') control = h('textarea',{id,name,value,...props});
  else control = h('input',{id,name,type,value,...props});
  if (hint) control.setAttribute('aria-describedby',`${id}-hint`);
  return h('div',{className:`field${wide?' span-2':''}`},h('label',{for:id},label, props.required ? ' *' : ''),control,hint?h('span',{id:`${id}-hint`,className:'field-hint'},hint):null);
}
function organizationStory() {
  return h('aside',{className:'auth-story'},
    h('div',{className:'logo'},h('span',{className:'brand-mark','aria-hidden':true},'c'), 'Commonstead'),
    h('div',{},h('div',{className:'eyebrow'},'A place for your customer relationships'),h('h1',{},'Good work starts\nwith common ground.'),
      h('p',{},'Bring your contacts, conversations, and opportunities together. A calm workspace, hosted on your own terms.'),
      h('div',{className:'auth-facts'},h('div',{},h('strong',{},'Open'),h('span',{},'MIT licensed')),h('div',{},h('strong',{},'Local'),h('span',{},'Your data, your host')),h('div',{},h('strong',{},'Together'),h('span',{},'Shared customer context')))),
    h('div',{className:'auth-foot'},'Independent software · CRM release 0.1.0 · Local development use'));
}
function renderAuth(mode = 'login', preview = null) {
  document.title = 'Commonstead · Welcome';
  const invite = mode === 'invite';
  const register = mode === 'register';
  const form = h('form',{className:'auth-form'});
  if (invite) {
    form.append(h('div',{className:'info-box'},`Join ${preview.organization.name} as ${pretty(preview.role)}. Invitation for ${preview.email}.`));
    form.append(inputField('Your name','name','text','',{required:true,autocomplete:'name',maxlength:150}));
  } else {
    if (register) {
      form.append(inputField('Organization name','organization','text','',{required:true,autocomplete:'organization',placeholder:'e.g. Northstar Workshop',maxlength:120}));
      form.append(inputField('Your name','name','text','',{required:true,autocomplete:'name',maxlength:120}));
    } else form.append(inputField('Organization sign-in ID','organization','text','',{required:true,placeholder:'e.g. northstar-workshop',autocapitalize:'none',spellcheck:'false',hint:'The ID shown in your workspace sidebar. Each organization has its own user accounts.'}));
    form.append(inputField('Email address','email','email','',{required:true,autocomplete:'username',maxlength:254}));
  }
  form.append(inputField('Password','password','password','',{required:true,minlength:register||invite?12:1,maxlength:128,autocomplete:register||invite?'new-password':'current-password',hint:register||invite?'Use 12–128 characters.':'',}));
  form.append(h('button',{className:'button primary',type:'submit'},invite?'Accept invitation':register?'Create workspace':'Sign in'));
  form.addEventListener('submit', event => {
    event.preventDefault();
    submitting(form,async() => {
      const values = Object.fromEntries(new FormData(form));
      if (invite) values.token = invitationToken;
      state.session = await api(invite?'/api/invitations/accept':register?'/api/register':'/api/login','POST',values);
      invitationToken = null;
      state.page = 'overview';
      await renderWorkspace();
      toast(register?`Workspace created. Your sign-in ID is ${state.session.organization.slug}.`:invite?'You have joined the workspace.':'Welcome back.');
    });
  });
  const tabs = invite?null:h('div',{className:'auth-tabs'},
    h('button',{type:'button',className:register?'':'active',onClick:()=>renderAuth('login')},'Sign in'),
    h('button',{type:'button',className:register?'active':'',onClick:()=>renderAuth('register')},'Create workspace'));
  app.replaceChildren(h('div',{className:'auth-layout'},organizationStory(),h('main',{id:'main',className:'auth-main'},h('section',{className:'auth-card'},tabs,
    h('h2',{},invite?'You’re invited.':register?'Make room for good work.':'Welcome to your workspace.'),
    h('p',{},invite?'Set up your account to start working with your team.':register?'Create an organization and become its first owner.':'Sign in to pick up where you left off.'),form,
    h('p',{className:'auth-note'},'No external service is required. Account and customer records are saved in the database on this host. This release is intended for local evaluation.')))));
}
async function logout() {
  try { await api('/api/logout','POST',{}); state.session=null; renderAuth('login'); toast('Signed out.'); }
  catch(error) { toast(error.message,true); }
}
function navigate(page) { state.page=page; state.query=''; state.offset=0; renderWorkspace(); }
function shell() {
  const {user,organization} = state.session;
  const nav = h('nav',{className:'nav','aria-label':'Workspace navigation'});
  for (const page of Object.keys(titles)) {
    if (page==='audit' && !canAdmin()) continue;
    nav.append(h('button',{type:'button',className:state.page===page?'active':'','aria-current':state.page===page?'page':null,onClick:()=>navigate(page)},h('span',{className:'nav-symbol','aria-hidden':true},symbols[page]),titles[page]));
  }
  const sidebar = h('aside',{className:'sidebar'},h('div',{className:'logo'},h('span',{className:'brand-mark','aria-hidden':true},'c'),'Commonstead'),
    h('div',{className:'workspace-chip'},h('strong',{},organization.name),h('span',{},`Sign-in ID: ${organization.slug}`)),h('div',{className:'nav-label'},'YOUR WORKSPACE'),nav,
    h('div',{className:'sidebar-foot'},h('div',{className:'identity'},h('div',{className:'avatar','aria-hidden':true},user.name.split(/\s+/).map(part=>part[0]).slice(0,2).join('').toUpperCase()),h('div',{},h('strong',{},user.name),h('small',{},user.role))),h('span',{className:'version'},'v0.1.0 · local')));
  const content = h('main',{id:'main',className:'content',tabindex:'-1'});
  app.replaceChildren(h('div',{className:'layout'},sidebar,h('div',{className:'workspace'},h('header',{className:'topbar'},h('div',{},h('span',{className:'status-dot','aria-hidden':true}),h('strong',{},organization.name),' / ',titles[state.page]),h('div',{className:'actions'},h('span',{},`${user.name} · ${pretty(user.role)}`),button('Sign out',logout,'small'))),content)));
  document.title=`${titles[state.page]} · Commonstead`;
  return content;
}
async function allRecords(entity) {
  let items=[],offset=0;
  while (true) {
    const result=await api(`/api/records/${entity}?limit=200&offset=${offset}`);
    items=items.concat(result.items);
    if (items.length>=result.total || result.items.length===0) return items;
    offset+=result.items.length;
  }
}
async function refreshLookups() {
  const [members,accounts,opportunities]=await Promise.all([api('/api/members'),allRecords('accounts'),allRecords('opportunities')]);
  state.members=members.items;
  state.accounts=accounts;
  state.opportunities=opportunities;
}
async function renderWorkspace() {
  if(!state.session)return;
  const renderId=++renderNumber;
  const main=shell();
  main.append(h('p',{className:'muted',role:'status'},'Loading workspace…'));
  main.setAttribute('aria-busy','true');
  try {
    await refreshLookups();
    if(renderId!==renderNumber)return;
    const page=state.page;
    let body;
    if(page==='overview')body=await dashboard();
    else if(page==='team')body=teamPage();
    else if(page==='audit')body=await auditPage();
    else body=await recordsPage(page);
    if(renderId===renderNumber){main.replaceChildren(...body);main.removeAttribute('aria-busy');}
  }catch(error){
    if(renderId===renderNumber&&state.session){main.removeAttribute('aria-busy');main.replaceChildren(h('div',{className:'error-box',role:'alert'},error.message),button('Try again',renderWorkspace));}
  }
}
function pageHeader(title,description,actions=[]) {return h('div',{className:'page-header'},h('div',{},h('div',{className:'eyebrow'},'CUSTOMER WORKSPACE'),h('h1',{},title),h('p',{},description)),h('div',{className:'actions'},actions));}
function metric(label,value,note){return h('div',{className:'metric'},h('div',{className:'metric-label'},label),h('div',{className:'metric-value'},value),h('div',{className:'metric-note'},note));}
async function dashboard() {
  const [report,activities]=await Promise.all([api('/api/reports/pipeline'),api('/api/records/activities?limit=6')]);
  const totals=report.totals;
  const pipeline=report.stages.filter(row=>!row.stage.startsWith('closed_'));
  const largest=Math.max(1,...pipeline.map(row=>row.amount_cents));
  const chart=h('div',{className:'panel-body'});
  for(const row of pipeline){const bar=h('div',{className:'pipeline-bar'});bar.style.width=`${row.amount_cents/largest*100}%`;chart.append(h('div',{className:'pipeline-row'},h('span',{className:'pipeline-label'},pretty(row.stage)),h('div',{className:'pipeline-track','aria-hidden':true},bar),h('span',{className:'pipeline-amount',title:`${row.count} opportunities · ${fullMoney(row.amount_cents)}`},money(row.amount_cents))));}
  const pipelinePanel=h('section',{className:'panel'},h('div',{className:'panel-header'},h('div',{},h('h2',{},'Your pipeline'),h('p',{},'Open opportunity value by stage')),button('View opportunities',()=>navigate('opportunities'),'small')),chart,h('div',{className:'panel-footer'},`${totals.opportunity_count} total opportunities · USD · Unweighted values`));
  const activityBody=h('div',{className:'panel-body'});
  if(!activities.items.length)activityBody.append(h('div',{className:'empty'},h('h3',{},'Make the next move.'),h('p',{},'Assign a call, task, or meeting to keep your relationships moving.')));
  for(const item of activities.items)activityBody.append(h('div',{className:'activity-row'},h('span',{className:'activity-icon','aria-hidden':true},item.status==='done'?'✓':'◷'),h('div',{className:'activity-text'},h('strong',{},item.subject),h('small',{},`${person(item.assigned_to)} · ${item.due_date||'No due date'}`)),badge(item.status)));
  const activityPanel=h('section',{className:'panel'},h('div',{className:'panel-header'},h('div',{},h('h2',{},'Recent activities'),h('p',{},'The latest work across your team')),button('View all',()=>navigate('activities'),'small')),activityBody);
  return [pageHeader('Room to grow.','A clear view of your relationships and the work ahead.',[button('Export report',()=>downloadReport(report)),canWrite()?button('+ New opportunity',()=>editRecord('opportunities'),'primary'):null]),
    h('section',{className:'metrics','aria-label':'Workspace metrics'},metric('Open pipeline',money(totals.pipeline_cents),'Across all open stages'),metric('Won revenue',money(totals.won_cents),'Closed won opportunities · all time'),metric('People in your network',totals.contacts,`${totals.accounts} accounts · ${totals.leads} leads`),metric('Open activities',totals.open_activities,`${totals.overdue_activities} overdue · UTC dates`)),
    h('div',{className:'dashboard-grid'},pipelinePanel,activityPanel),
    h('div',{className:'overview-banner'},h('span',{className:'banner-symbol','aria-hidden':true},'❧'),h('div',{},h('h3',{},'One shared place. A little more clarity.'),h('p',{},'Start with an account, add your contacts, and connect an opportunity to the work that follows.'))),
    h('p',{className:'report-note'},`Live report from persisted records · ${new Date().toISOString()} · Amounts displayed rounded; exported report includes exact cents.`)];
}
function downloadText(filename,text,type='text/csv;charset=utf-8') {
  const url=URL.createObjectURL(new Blob([text],{type}));
  const link=h('a',{href:url,download:filename});document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function downloadReport(report) {
  const lines=['metric,value,unit',`generated_at,${new Date().toISOString()},UTC`];
  for(const [key,value]of Object.entries(report.totals))lines.push(`${key},${value},${key.endsWith('_cents')?'USD cents':'count'}`);
  for(const row of report.stages){lines.push(`${row.stage}_count,${row.count},count`);lines.push(`${row.stage}_amount,${row.amount_cents},USD cents`);}
  downloadText(`commonstead-pipeline-${new Date().toISOString().slice(0,10)}.csv`,lines.join('\r\n')+'\r\n');toast('Report exported.');
}
const columns={
  accounts:[['Account',item=>h('div',{},h('span',{className:'cell-primary'},item.name),h('span',{className:'cell-secondary'},item.website||''))],['Industry',item=>item.industry||'—'],['Owner',item=>person(item.owner_id)]],
  contacts:[['Contact',item=>h('div',{},h('span',{className:'cell-primary'},`${item.first_name||''} ${item.last_name}`.trim()),h('span',{className:'cell-secondary'},item.title||''))],['Email',item=>item.email||'—'],['Account',item=>accountName(item.account_id)],['Owner',item=>person(item.owner_id)]],
  leads:[['Lead',item=>h('div',{},h('span',{className:'cell-primary'},`${item.first_name||''} ${item.last_name}`.trim()),h('span',{className:'cell-secondary'},item.email||''))],['Company',item=>item.company||'—'],['Status',item=>badge(item.status)],['Owner',item=>person(item.owner_id)]],
  opportunities:[['Opportunity',item=>h('div',{},h('span',{className:'cell-primary'},item.name),h('span',{className:'cell-secondary'},accountName(item.account_id)))],['Stage',item=>badge(item.stage)],['Value',item=>fullMoney(item.amount_cents)],['Expected close',item=>item.expected_close||'—'],['Owner',item=>person(item.owner_id)]],
  activities:[['Activity',item=>h('div',{},h('span',{className:'cell-primary'},item.subject),h('span',{className:'cell-secondary'},pretty(item.kind)))],['Assigned to',item=>person(item.assigned_to)],['Due',item=>item.due_date||'—'],['Status',item=>badge(item.status)],['Account',item=>accountName(item.account_id)]]
};
async function recordsPage(entity) {
  const result=await api(`/api/records/${entity}?limit=${state.limit}&offset=${state.offset}&q=${encodeURIComponent(state.query)}`);
  const actions=[];
  if(entity==='contacts'){
    actions.push(button('Export CSV',exportContacts));
    if(canWrite())actions.push(button('Import contacts',importContacts));
  }
  if(canWrite())actions.push(button(`+ New ${singular[entity]}`,()=>editRecord(entity),'primary'));
  const descriptions={accounts:'The organizations behind your customer relationships.',contacts:'People, context, and the connections that matter.',leads:'Turn an introduction into the next conversation.',opportunities:'Move each opportunity forward, one stage at a time.',activities:'Clear ownership for every next step.'};
  const search=h('form',{className:'search-form'},h('label',{className:'sr-only',for:'record-search'},`Search ${entity}`),h('input',{id:'record-search',name:'q',type:'search',placeholder:`Search ${entity}…`,value:state.query}),h('button',{type:'submit',className:'button'},'Search'));
  search.addEventListener('submit',event=>{event.preventDefault();state.query=$('input',search).value;state.offset=0;renderWorkspace();});
  const toolbar=h('div',{className:'toolbar'},search,h('span',{className:'muted'},`${result.total} ${result.total===1?singular[entity]:entity}`));
  const table=h('table',{},h('thead',{},h('tr',{},columns[entity].map(([label])=>h('th',{scope:'col'},label)),canWrite()?h('th',{scope:'col',className:'text-right'},'Actions'):null)));
  const tbody=h('tbody');
  for(const item of result.items){
    const rowActions=[];
    if(canWrite()){
      if(entity==='activities'&&item.status==='open')rowActions.push(button('Done',async()=>{try{await api(`/api/records/activities/${item.id}`,'PATCH',{status:'done'});toast('Activity completed.');await renderWorkspace();}catch(error){toast(error.message,true);}},'small',{'aria-label':`Complete ${item.subject}`}));
      rowActions.push(button('Edit',()=>editRecord(entity,item),'small',{'aria-label':`Edit ${item.name||item.subject||item.last_name}`}));
      if(canAdmin())rowActions.push(button('Delete',()=>deleteRecord(entity,item),'small danger',{'aria-label':`Delete ${item.name||item.subject||item.last_name}`}));
    }
    tbody.append(h('tr',{},columns[entity].map(([,render])=>h('td',{},render(item))),canWrite()?h('td',{},h('div',{className:'row-actions'},rowActions)):null));
  }
  table.append(tbody);
  const panel=h('section',{className:'panel','aria-label':titles[entity]},toolbar,result.items.length?h('div',{className:'table-wrap'},table):h('div',{className:'empty'},h('span',{className:'empty-symbol','aria-hidden':true},symbols[entity]),h('h3',{},state.query?'No matches found.':`Your ${entity} belong here.`),h('p',{},state.query?'Try another search, or clear the search field.':`Add your first ${singular[entity]} to start building a shared view.`),canWrite()&&!state.query?button(`Create ${singular[entity]}`,()=>editRecord(entity),'primary'):null),
    h('div',{className:'table-footer'},h('span',{},result.total?`${state.offset+1}–${state.offset+result.items.length} of ${result.total}`:'No records'),h('div',{className:'actions'},button('Previous',()=>{state.offset=Math.max(0,state.offset-state.limit);renderWorkspace();},'small',{disabled:state.offset===0}),button('Next',()=>{state.offset+=state.limit;renderWorkspace();},'small',{disabled:state.offset+state.limit>=result.total}))));
  return [pageHeader(titles[entity],descriptions[entity],actions),panel];
}
function dialog(title,form,submitText='Save') {
  const heading=h('div',{className:'dialog-header'},h('h2',{id:'dialog-title'},title),h('button',{type:'button',className:'close-button','aria-label':'Close dialog',onClick:()=>modal.close()},'×'));
  const body=h('div',{className:'dialog-body'},...Array.from(form.childNodes));
  form.append(body,h('div',{className:'dialog-footer'},button('Cancel',()=>modal.close()),h('button',{type:'submit',className:'button primary'},submitText)));
  modal.replaceChildren(heading,form);
  modal.showModal();
}
function choices(values){return values.map(value=>({value,label:pretty(value)}));}
function editRecord(entity,item={}) {
  if(!canWrite())return;
  if(entity==='opportunities'&&!state.accounts.length){toast('Create an account before adding an opportunity.',true);navigate('accounts');return;}
  const fields=[];
  const add=(...args)=>fields.push(inputField(...args));
  const text=(label,name,required=false,wide=false)=>add(label,name,'text',item[name]||'',{required,wide,maxlength:name==='website'?2048:250});
  const select=(label,name,options,required=false,defaultValue='')=>add(label,name,'select',item[name]??defaultValue,{choices:options,required});
  const memberOptions=state.members.map(member=>({value:member.id,label:`${member.name} (${member.role})`}));
  const accountOptions=[{value:'',label:'No linked account'},...state.accounts.map(account=>({value:account.id,label:account.name}))];
  if(entity==='accounts'){text('Account name','name',true,true);text('Website','website');text('Industry','industry');}
  if(entity==='contacts'||entity==='leads'){
    text('First name','first_name');text('Last name','last_name',true);
    add('Email address','email','email',item.email||'',{maxlength:254});
    if(entity==='contacts'){text('Phone','phone');text('Job title','title');select('Account','account_id',accountOptions);}
    else{text('Company','company');select('Status','status',choices(['new','contacted','qualified','disqualified']),true,'new');}
  }
  if(entity==='opportunities'){
    text('Opportunity name','name',true,true);
    select('Account','account_id',accountOptions.map((option,index)=>index===0?{value:'',label:'Choose an account'}:option),true);
    add('Value (USD)','amount','number',((item.amount_cents||0)/100).toFixed(2),{required:true,min:0,max:90000000000,step:'0.01',hint:'One currency in this release: US dollars.'});
    select('Stage','stage',choices(stages),true,'prospecting');add('Expected close','expected_close','date',item.expected_close||'');
  }
  if(entity==='activities'){
    text('Subject','subject',true,true);select('Kind','kind',choices(['task','call','meeting']),true,'task');select('Status','status',choices(['open','done']),true,'open');
    add('Due date','due_date','date',item.due_date||'',{hint:'Overdue reports compare this date with UTC today.'});select('Assigned to','assigned_to',memberOptions,true,state.session.user.id);select('Account','account_id',accountOptions);
    select('Opportunity','opportunity_id',[{value:'',label:'No linked opportunity'},...state.opportunities.map(opportunity=>({value:opportunity.id,label:opportunity.name}))]);
  }else select('Owner','owner_id',memberOptions,true,state.session.user.id);
  add('Notes','notes','textarea',item.notes||'',{wide:true,maxlength:10000});
  const form=h('form',{},h('div',{className:'form-grid'},fields));
  form.addEventListener('submit',event=>{
    event.preventDefault();submitting(form,async()=>{
      const values=Object.fromEntries(new FormData(form));
      if(entity==='opportunities'){
        const match=/^(\d+)(?:\.(\d{1,2}))?$/.exec(values.amount);
        if(!match)throw new Error('Enter a nonnegative USD amount with at most two decimal places.');
        values.amount_cents=Number(match[1])*100+Number((match[2]||'').padEnd(2,'0'));delete values.amount;
        if(!Number.isSafeInteger(values.amount_cents))throw new Error('The amount is too large.');
      }
      for(const name of ['account_id','opportunity_id'])if(name in values&&values[name]==='')values[name]=null;
      await api(`/api/records/${entity}${item.id?`/${item.id}`:''}`,item.id?'PATCH':'POST',values);
      modal.close();toast(`${pretty(singular[entity])} ${item.id?'updated':'created'}.`);await renderWorkspace();
    });
  });
  dialog(`${item.id?'Edit':'New'} ${singular[entity]}`,form,item.id?'Save changes':`Create ${singular[entity]}`);
}
function deleteRecord(entity,item){
  const name=item.name||item.subject||`${item.first_name||''} ${item.last_name}`.trim();
  const form=h('form',{},h('p',{},`Delete “${name}”? This removes the record permanently. Referenced records must be unlinked first.`));
  form.addEventListener('submit',event=>{event.preventDefault();submitting(form,async()=>{await api(`/api/records/${entity}/${item.id}`,'DELETE',{});modal.close();toast('Record deleted.');state.offset=0;await renderWorkspace();});});
  dialog(`Delete ${singular[entity]}`,form,'Delete record');
}
function importContacts(){
  const textArea=inputField('CSV contents','csv','textarea','',{required:true,wide:true,rows:9,maxlength:900000,hint:'Up to 1,000 rows. The whole import succeeds or no records are saved.'});
  const file=h('input',{id:'csv-file',type:'file',accept:'.csv,text/csv'});
  const form=h('form',{},h('p',{},'Use these exact headers. Last name is required. Account names must already exist in this workspace. Duplicate nonblank emails are rejected.'),h('pre',{},'first_name,last_name,email,phone,title,account_name\nAvery,Stone,avery@example.test,,Buyer,Northstar Workshop'),h('div',{className:'field'},h('label',{for:'csv-file'},'Choose a CSV file'),file),textArea);
  file.addEventListener('change',async()=>{if(file.files[0]){if(file.files[0].size>900000){showFormError(form,new Error('Choose a file smaller than 900 KB.'));return;}try{$('textarea',form).value=await file.files[0].text();}catch{showFormError(form,new Error('Could not read that file.'));}}});
  form.addEventListener('submit',event=>{event.preventDefault();submitting(form,async()=>{const result=await api('/api/import/contacts','POST',{csv:$('textarea',form).value});modal.close();toast(`Imported ${result.imported} contacts.`);state.offset=0;await renderWorkspace();});});
  dialog('Import contacts',form,'Import contacts');
}
async function exportContacts(){
  try{const response=await fetch('/api/export/contacts',{credentials:'same-origin'});if(!response.ok){const data=await response.json();throw new Error(data.error?.message||'Export failed.');}downloadText('commonstead-contacts.csv',await response.text());toast('Contacts exported.');}catch(error){toast(error.message,true);}
}
function teamPage(){
  const body=h('tbody');
  for(const member of state.members){
    let role=badge(member.role);
    if(state.session.user.role==='owner'){
      role=h('select',{className:'role-select',value:member.role,'aria-label':`Role for ${member.name}`},choices(['owner','admin','member','viewer']).map(option=>h('option',{value:option.value},option.label)));
      role.addEventListener('change',()=>{
        const targetRole=role.value;role.value=member.role;
        const form=h('form',{},h('p',{},`Change ${member.name} from ${pretty(member.role)} to ${pretty(targetRole)}? Permissions take effect on the next API request, including for existing sessions.`));
        form.addEventListener('submit',event=>{event.preventDefault();submitting(form,async()=>{await api(`/api/members/${member.id}`,'PATCH',{role:targetRole});modal.close();state.session=await api('/api/session');toast('Role updated.');await renderWorkspace();});});
        dialog('Change workspace role',form,'Change role');
      });
    }
    body.append(h('tr',{},h('td',{},h('span',{className:'cell-primary'},member.name),member.id===state.session.user.id?h('span',{className:'cell-secondary'},'You'):null),h('td',{},member.email),h('td',{},role)));
  }
  return [pageHeader('Good work is shared.','Invite your team and give each person the access they need.',canAdmin()?[button('+ Invite a teammate',inviteMember,'primary')]:[]),
    h('div',{className:'info-box'},'Owner: full access and role management. Admin: CRM edits, deletes, and member/viewer invitations. Member: create and update CRM records. Viewer: read records and export reports. All CRM records are shared within the organization.'),
    h('section',{className:'panel'},h('div',{className:'table-wrap'},h('table',{},h('thead',{},h('tr',{},h('th',{scope:'col'},'Teammate'),h('th',{scope:'col'},'Email'),h('th',{scope:'col'},'Role'))),body))),
    h('p',{className:'report-note'},`Organization sign-in ID: ${state.session.organization.slug}. Invitation links are handed to recipients manually; this release does not send email.`)];
}
function inviteMember(){
  const allowed=state.session.user.role==='owner'?['member','viewer','admin']:['member','viewer'];
  const form=h('form',{},inputField('Email address','email','email','',{required:true,maxlength:254}),inputField('Role','role','select','member',{choices:choices(allowed),required:true}),h('p',{},'A single-use invitation link expires after seven days. Share it with the intended recipient using a trusted channel.'));
  form.addEventListener('submit',event=>{event.preventDefault();submitting(form,async()=>{
    const result=await api('/api/invitations','POST',Object.fromEntries(new FormData(form)));
    const url=new URL(location.origin);url.searchParams.set('invite',result.token);
    const link=h('input',{id:'invitation-link',type:'text',value:url.href,readonly:true,onFocus:event=>event.target.select()});
    modal.replaceChildren(h('div',{className:'dialog-header'},h('h2',{id:'dialog-title'},'Your invitation is ready'),h('button',{type:'button',className:'close-button','aria-label':'Close dialog',onClick:()=>modal.close()},'×')),h('div',{className:'dialog-body'},h('p',{},`Invite ${result.email} as ${pretty(result.role)}. Expires ${result.expires_at}.`),h('label',{for:'invitation-link'},'Single-use invitation link'),h('div',{className:'copy-row'},link,button('Copy',async()=>{try{await navigator.clipboard.writeText(url.href);toast('Invitation link copied.');}catch{link.select();toast('Select and copy the link manually.',true);}})),h('div',{className:'info-box'},'This local address works on the host running Commonstead. For local evaluation, the recipient can open it in a separate browser profile on this computer. Remote delivery and public hosting are not configured.')),h('div',{className:'dialog-footer'},button('Done',()=>modal.close(),'primary')));
  });});
  dialog('Invite a teammate',form,'Create invitation');
}
async function auditPage(){
  const result=await api(`/api/audit?limit=${state.limit}&offset=${state.offset}`);
  const body=h('tbody');
  for(const item of result.items)body.append(h('tr',{},h('td',{},item.created_at),h('td',{},item.actor_name||'System'),h('td',{},pretty(item.action)),h('td',{},item.entity||'—'),h('td',{},h('code',{},item.entity_id||''))));
  return [pageHeader('A record of the work.','Organization-scoped changes, recorded when they happen.'),h('section',{className:'panel'},h('div',{className:'table-wrap'},h('table',{},h('thead',{},h('tr',{},['Time (UTC)','Actor','Action','Entity','Record ID'].map(label=>h('th',{scope:'col'},label)))),body)),!result.items.length?h('div',{className:'empty'},'No audit events yet.'):null,h('div',{className:'table-footer'},h('span',{},'Newest events first'),h('div',{className:'actions'},button('Previous',()=>{state.offset=Math.max(0,state.offset-state.limit);renderWorkspace();},'small',{disabled:state.offset===0}),button('Next',()=>{state.offset+=state.limit;renderWorkspace();},'small',{disabled:result.items.length<state.limit})))),h('p',{className:'report-note'},'Application audit history is stored in the local database. It is not tamper-proof against the host administrator.')];
}
async function start(){
  try{
    const session=await api('/api/session');
    if(invitationToken){if(session.authenticated)state.session=session;const preview=await api(`/api/invitations/preview?token=${encodeURIComponent(invitationToken)}`);renderAuth('invite',preview);return;}
    if(session.authenticated){state.session=session;await renderWorkspace();}else renderAuth('login');
  }catch(error){renderAuth('login');toast(error.message,true);}
}
start();
