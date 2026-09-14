import { useEffect, useMemo, useState } from "react";
import { QRCodeCanvas } from "qrcode.react";
import { Activity, AlertTriangle, ArrowUpRight, Award, BarChart3, Bell, Check, ChevronRight, CircleHelp, Gauge, LayoutDashboard, LogOut, Map, Menu, MoreHorizontal, Plus, Search, Settings, ShieldCheck, Sparkles, Trophy, Users, WalletCards, X, Zap } from "lucide-react";
import { api, type Role, type SessionUser } from "./api";
import Stat from "./components/Stat";
import Login from "./components/Login";
import Modal from "./components/Modal";
import RotateIcon from "./components/RotateIcon";
import PointRequests from "./components/PointRequests";
import PublicView from "./components/PublicView";
import PlayerView from "./components/PlayerView";
import WheelModal from "./components/WheelModal";
import Players from "./components/Players";
import Points from "./components/Points";
import Challenges from "./components/Challenges";
import Groups from "./components/Groups";

type Toast = {id:number;text:string;tone?:"success"|"info"|"warning"};

import Overview from "./components/Overview";
const demoPlayers = [
  {id:1,gamertag:"PixelRanger",xp:24530,status:"Active",badge:"Silver",color:"lime"},
  {id:2,gamertag:"NovaSquad",xp:18740,status:"Active",badge:"Bronze",color:"purple"},
  {id:3,gamertag:"StormCrew",xp:15640,status:"Active",badge:"Bronze",color:"cyan"},
  {id:4,gamertag:"UrbanLegends",xp:12450,status:"At risk",badge:"Iron",color:"yellow"},
];

export default function App(){
  const [user,setUser]=useState<SessionUser|null>(null);
  const [loginOpen,setLoginOpen]=useState(true);
  const [checking,setChecking]=useState(true);
  const [error,setError]=useState("");
  const [publicMode,setPublicMode]=useState(false);
  const [section,setSection]=useState("Overview");
  const [mobileNav,setMobileNav]=useState(false);
  const [toasts,setToasts]=useState<Toast[]>([]);
  const [wheelOpen,setWheelOpen]=useState(false);
  const [awardOpen,setAwardOpen]=useState(false);
  const [selectedPlayer,setSelectedPlayer]=useState<any>(null);
  const [data,setData]=useState<any>(null);
  const [userManagerOpen,setUserManagerOpen]=useState(false);
  const [economyOpen,setEconomyOpen]=useState(false);
  const [rewardManagerOpen,setRewardManagerOpen]=useState(false);
  const [playerQrOpen,setPlayerQrOpen]=useState(false);
  const [pointRequestsOpen,setPointRequestsOpen]=useState(false);

  const role: Role | "public" = publicMode ? "public" : user?.role ?? "public";
  const isStaff = user?.role === "admin" || user?.role === "youth_worker";

  const pushToast=(text:string,tone:Toast["tone"]="success")=>{const id=Date.now();setToasts(v=>[...v,{id,text,tone}]);setTimeout(()=>setToasts(v=>v.filter(t=>t.id!==id)),3000)};

  useEffect(()=>{api.me().then(u=>{setUser(u);setLoginOpen(false)}).catch(()=>{}).finally(()=>setChecking(false))},[]);

  const refresh=async()=>{
    try{
      if(publicMode){setData(await api.publicDashboard()); return;}
      if(user?.role==="player") setData({player:await api.playerDashboard(), games:await api.rewardGames()});
      else if(isStaff) setData({overview:await api.adminOverview(), players:await api.adminPlayers(), leaderboard:await api.leaderboards(), users:user?.role==="admin"?await api.adminUsers():undefined, pointRequests:isStaff?await api.pointRequests("pending"):undefined});
    }catch(e:any){setError(e.message);}
  };
  useEffect(()=>{if(!checking) refresh()},[checking,user?.role,publicMode]);

  const nav=useMemo(()=>publicMode?["Home","Leaderboard","Map","Milestones"]:user?.role==="player"?["Home","Challenges","Rewards","Profile"]:user?.role==="admin"?["Dashboard","Users & Groups","Points & Rewards","Points Requests","Challenges","Phases & Themes","Community Nominations","Analytics","System Settings"]:["Overview","Players","Groups","Challenges","Map","Rewards & Points","Points Requests","Community Nominations","Resources","Reports"],[publicMode,user?.role]);

  const logout=async()=>{await api.logout().catch(()=>{});setUser(null);setPublicMode(true);setData(null);pushToast("Signed out","info")};

  const requestToken=new URLSearchParams(window.location.search).get("token");
  const requestMode=window.location.pathname==="/request-points"&&!!requestToken;
  if(requestMode) return <PointRequestPage token={requestToken!}/>;
  if(checking) return <div className="center-screen"><div className="loader-ring"/><p>Connecting to QuestHub…</p></div>;
  if(loginOpen && !publicMode) return <Login onLogin={async(u,p)=>{setError("");try{const x=await api.login(u,p);setUser(x);setLoginOpen(false);pushToast(`Signed in as ${x.role.replace("_"," ")}`)}catch(e:any){setError(e.message)}}} onPublic={()=>{setPublicMode(true);setLoginOpen(false)}} error={error}/>;

  const title=publicMode?"Public Dashboard":user?.role==="admin"?"Admin Dashboard":user?.role==="player"?"Player Dashboard":"Youth Worker Dashboard";
  return <div className="app-shell">
    <aside className={`sidebar ${mobileNav?"open":""}`}>
      <div className="brand"><div className="brand-mark">Q</div><div><strong>QUEST<span>HUB</span></strong><small>CUMBERNAULD CLIMB</small></div></div>
      <div className="role-switch"><span>CONNECTED AS</span><div className="identity-chip">{publicMode?"PUBLIC VIEW":user?.username ?? "GUEST"}</div><div className="role-actions"><button className={publicMode?"active":""} onClick={()=>{setPublicMode(true);setSection("Home")}}>Public</button>{isStaff&&<button className={!publicMode?"active":""} onClick={()=>{setPublicMode(false);setSection(user?.role==="admin"?"Dashboard":"Overview")}}>My dashboard</button>}</div></div>
      <nav>{nav.map((item,i)=><button key={item} className={section===item?"nav-item active":"nav-item"} onClick={()=>{setSection(item);setMobileNav(false)}}>{i===0?<LayoutDashboard size={17}/>:i===1?<Users size={17}/>:i===2?<WalletCards size={17}/>:i===3?<Zap size={17}/>:i===4?<Map size={17}/>:i===5?<Award size={17}/>:i===6?<ShieldCheck size={17}/>:<BarChart3 size={17}/>} {item}</button>)}</nav>
      <div className="sidebar-bottom"><div className="system-chip"><span className="pulse-dot"/> API connected</div>{user&&<button className="nav-item" onClick={logout}><LogOut size={17}/> Sign out</button>}<button className="nav-item"><CircleHelp size={17}/> Help & support</button></div>
    </aside>
    <main className="main">
      <header className="topbar"><button className="mobile-menu" onClick={()=>setMobileNav(!mobileNav)}><Menu/></button><div><div className="eyebrow">QUESTHUB / {publicMode?"PUBLIC":user?.role?.toUpperCase()}</div><h1>{title}</h1><p>{publicMode?"Collective progress, anonymised rankings and phase activity.":"Live data from the supplied FastAPI backend."}</p></div><div className="top-actions"><button className="icon-btn" onClick={()=>refresh()}><RotateIcon/></button><button className="icon-btn" onClick={()=>pushToast("Notifications endpoint can be connected here","info")}><Bell size={18}/></button>{user&&<div className="staff-avatar">{user.username.slice(0,2).toUpperCase()}</div>}</div></header>
      {error&&<div className="api-error"><AlertTriangle size={16}/><span>{error}</span><button onClick={()=>setError("")}><X size={14}/></button></div>}
      {publicMode?<PublicView data={data} section={section}/>:user?.role==="player"?<PlayerView data={data} section={section} openWheel={()=>setWheelOpen(true)} openQr={()=>setPlayerQrOpen(true)} pushToast={pushToast}/>:<StaffView role={user?.role} data={data} section={section} setSelectedPlayer={setSelectedPlayer} openAward={()=>setAwardOpen(true)} openWheel={()=>setWheelOpen(true)} pushToast={pushToast} openUsers={()=>setUserManagerOpen(true)} openEconomy={()=>setEconomyOpen(true)} openRewards={()=>setRewardManagerOpen(true)} openPointRequests={()=>setPointRequestsOpen(true)} refresh={refresh} demoPlayers={demoPlayers}/>} 
    </main>
    {wheelOpen&&<WheelModal data={data?.games} onClose={()=>setWheelOpen(false)} pushToast={pushToast}/>} 
    {userManagerOpen&&<UserManagerModal users={data?.users??[]} onClose={()=>setUserManagerOpen(false)} refresh={refresh} pushToast={pushToast}/>}
    {economyOpen&&<EconomyModal onClose={()=>setEconomyOpen(false)} pushToast={pushToast}/>} 
    {rewardManagerOpen&&<RewardManagerModal onClose={()=>setRewardManagerOpen(false)} pushToast={pushToast}/>}
    {playerQrOpen&&<PlayerQrModal onClose={()=>setPlayerQrOpen(false)} pushToast={pushToast}/>}
    {pointRequestsOpen&&<PointRequestsModal onClose={()=>setPointRequestsOpen(false)} pushToast={pushToast} refresh={refresh}/>} 
    {awardOpen&&<AwardModal players={data?.players??[]} selected={selectedPlayer} setSelected={setSelectedPlayer} onClose={()=>setAwardOpen(false)} pushToast={pushToast}/>} 
    <div className="toast-stack">{toasts.map(t=><div className={`toast ${t.tone??"success"}`} key={t.id}><Check size={16}/>{t.text}<button onClick={()=>setToasts(v=>v.filter(x=>x.id!==t.id))}><X size={14}/></button></div>)}</div>
  </div>
}


function StaffView({role,data,section,setSelectedPlayer,openAward,openWheel,pushToast,openUsers,openEconomy,openRewards,openPointRequests,refresh,demoPlayers}:{role?:Role;data:any;section:string;setSelectedPlayer:(p:any)=>void;openAward:()=>void;openWheel:()=>void;pushToast:(s:string,t?:any)=>void;openUsers:()=>void;openEconomy:()=>void;openRewards:()=>void;openPointRequests:()=>void;refresh:()=>Promise<void>;demoPlayers:any[]}){if(section==="Groups")return <Groups data={data} pushToast={pushToast}/>;if(section==="Players"||section==="Users & Groups")return <Players data={data} setSelectedPlayer={setSelectedPlayer} openAward={openAward} openUsers={openUsers} pushToast={pushToast} refresh={refresh}/>;if(section==="Points & Rewards")return <Points openAward={openAward} pushToast={pushToast} openEconomy={openEconomy} openRewards={openRewards}/>;if(section==="Points Requests")return <PointRequests data={data} openPointRequests={openPointRequests} pushToast={pushToast} refresh={refresh}/>;if(section==="Challenges")return <Challenges openWheel={openWheel} pushToast={pushToast}/>;if(section==="Analytics")return <Analytics pushToast={pushToast}/>;if(section==="System Settings")return <EconomyPanel openEconomy={openEconomy}/>;return <Overview data={data} role={role} openAward={openAward} openWheel={openWheel} openRewards={openRewards} pushToast={pushToast} demoPlayers={demoPlayers}/>}


function Analytics({pushToast}:{pushToast:(s:string,t?:any)=>void}){
  const [data,setData]=useState<any>(null);
  const [loading,setLoading]=useState(true);

  const load=async()=>{
    try{
      setLoading(true);
      const result=await api.analytics();
      setData(result);
    }catch(e:any){
      pushToast(e.message,"warning");
    }finally{
      setLoading(false);
    }
  };

  useEffect(()=>{load()},[]);

  const o=data?.overview??{};
  const attendance=data?.attendance??{};
  const challenges=data?.challenges??{};
  const requests=data?.point_requests??{};
  const operations=data?.operations??{};
  const daily=data?.xp?.daily??[];
  const sources=data?.xp?.by_source??[];
  const groups=data?.groups??[];

  const maxDaily=Math.max(
    1,
    ...daily.map((d:any)=>Math.max(0,Number(d.xp??0)))
  );

  return <div className="page">
    <section className="page-title-row">
      <div>
        <span className="eyebrow">PROGRAMME INTELLIGENCE</span>
        <h2>Analytics</h2>
        <p>Operational insight across XP, participation and programme activity.</p>
      </div>
      <button className="secondary-btn" onClick={load} disabled={loading}>
        {loading?"Refreshing…":"Refresh analytics"}
      </button>
    </section>

    <section className="stats-grid">
      <Stat
        icon={<Gauge/>}
        label="Total XP"
        value={Number(o.total_xp??0).toLocaleString()}
        delta={`${Number(o.xp_this_week??0).toLocaleString()} this week`}
      />
      <Stat
        icon={<Users/>}
        label="Active players"
        value={String(o.total_players??0)}
        delta={`${o.public_players??0} publicly visible`}
      />
      <Stat
        icon={<Trophy/>}
        label="Group XP"
        value={Number(o.group_xp??0).toLocaleString()}
        delta={`${Number(o.group_xp_this_week??0).toLocaleString()} this week`}
      />
      <Stat
        icon={<Activity/>}
        label="Attendance"
        value={String(attendance.checkins??0)}
        delta={`${attendance.checkins_this_week??0} this week`}
      />
    </section>

    <section className="content-grid">
      <div className="panel large">
        <div className="panel-head">
          <div>
            <span className="eyebrow">XP ACTIVITY</span>
            <h3>Last 14 days</h3>
          </div>
          <Activity size={18}/>
        </div>

        {daily.length===0 ? (
          <div className="empty-state">No XP activity recorded yet.</div>
        ) : (
          <div style={{
            display:"flex",
            alignItems:"end",
            gap:8,
            height:220,
            padding:"18px 4px 8px"
          }}>
            {daily.map((d:any)=>(
              <div
                key={d.date}
                style={{
                  flex:1,
                  height:"100%",
                  display:"flex",
                  flexDirection:"column",
                  justifyContent:"end",
                  minWidth:0
                }}
              >
                <div
                  title={`${d.date}: ${Number(d.xp??0).toLocaleString()} XP`}
                  style={{
                    height:`${Math.max(4,(Number(d.xp??0)/maxDaily)*165)}px`,
                    borderRadius:"8px 8px 3px 3px",
                    background:"linear-gradient(180deg,#64e7ff,#7857ff)",
                    boxShadow:"0 0 18px rgba(100,231,255,.18)"
                  }}
                />
                <small style={{
                  marginTop:8,
                  color:"#70808e",
                  fontSize:10,
                  textAlign:"center",
                  overflow:"hidden"
                }}>
                  {String(d.date).slice(5)}
                </small>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="panel">
        <div className="panel-head">
          <div>
            <span className="eyebrow">XP SOURCES</span>
            <h3>Where XP comes from</h3>
          </div>
          <Award size={18}/>
        </div>

        {sources.length===0 ? (
          <div className="empty-state">No XP transactions yet.</div>
        ) : (
          <div className="analytics-list">
            {sources.slice(0,8).map((item:any)=>(
              <div className="setting-line" key={item.source}>
                <span>
                  <b>{String(item.source).replace(/_/g," ")}</b>
                  <small style={{display:"block",color:"#70808e"}}>
                    {item.transactions} transaction{item.transactions===1?"":"s"}
                  </small>
                </span>
                <strong>
                  {Number(item.xp??0).toLocaleString()} XP
                </strong>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>

    <section className="content-grid">
      <div className="panel large">
        <div className="panel-head">
          <div>
            <span className="eyebrow">GROUP PERFORMANCE</span>
            <h3>Collective progress</h3>
          </div>
          <Users size={18}/>
        </div>

        {groups.length===0 ? (
          <div className="empty-state">No groups configured.</div>
        ) : (
          <div className="analytics-list">
            {groups.map((group:any)=>(
              <div className="setting-line" key={group.id}>
                <span>
                  <b>{group.name}</b>
                  <small style={{display:"block",color:"#70808e"}}>
                    {group.players} player{group.players===1?"":"s"} · {group.active?"Active":"Inactive"}
                  </small>
                </span>
                <strong>{Number(group.xp??0).toLocaleString()} XP</strong>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="panel">
        <div className="panel-head">
          <div>
            <span className="eyebrow">PROGRAMME OPERATIONS</span>
            <h3>Activity snapshot</h3>
          </div>
          <Activity size={18}/>
        </div>

        <div className="analytics-kpis">
          <div>
            <span>Attendance sessions</span>
            <b>{attendance.sessions??0}</b>
          </div>
          <div>
            <span>Challenge attempts</span>
            <b>{challenges.attempts??0}</b>
          </div>
          <div>
            <span>Pending point requests</span>
            <b>{requests.pending??0}</b>
          </div>
          <div>
            <span>Approved request XP</span>
            <b>{Number(requests.approved_xp??0).toLocaleString()}</b>
          </div>
          <div>
            <span>Audit events this week</span>
            <b>{operations.audit_events_this_week??0}</b>
          </div>
        </div>
      </div>
    </section>
  </div>
}

function PointRequestsModal({onClose,pushToast,refresh}:{onClose:()=>void;pushToast:(s:string,t?:any)=>void;refresh:()=>Promise<void>}){const [rows,setRows]=useState<any[]>([]);const [busy,setBusy]=useState<number|null>(null);const load=async()=>{try{setRows(await api.pointRequests("pending"))}catch(e:any){pushToast(e.message,"warning")}};useEffect(()=>{load()},[]);const decide=async(r:any,approved:boolean)=>{let amount=r.requested_xp;let note="";if(approved){const x=window.prompt(`Approve XP for ${r.gamertag}`,String(r.requested_xp));if(x===null)return;amount=Number(x);if(!Number.isFinite(amount)||amount<1||amount>5000){pushToast("XP must be between 1 and 5,000","warning");return};note=window.prompt("Optional review note","")||""}else note=window.prompt("Reason for rejection","")||"Request declined by youth worker.";setBusy(r.id);try{if(approved)await api.approvePointRequest(r.id,{approved_xp:amount,review_note:note||null});else await api.rejectPointRequest(r.id,{review_note:note});pushToast(approved?`+${amount.toLocaleString()} XP approved`:`Request #${r.id} rejected`);await load();await refresh()}catch(e:any){pushToast(e.message,"warning")}finally{setBusy(null)}};return <Modal title="Points requests" onClose={onClose}><div className="panel inset"><div className="panel-head"><h3>Pending review</h3><button className="ghost-btn" onClick={load}><RotateIcon/></button></div>{rows.length===0?<p className="muted">Nothing waiting for review.</p>:rows.map(r=><div className="request-card" key={r.id}><div className="request-card-head"><div><b>{r.gamertag}</b><small>Request #{r.id} · {r.created_at?new Date(r.created_at).toLocaleString():""}</small></div><strong>+{r.requested_xp.toLocaleString()} XP</strong></div><p>{r.reason}</p><div className="nom-actions"><button className="primary-btn" disabled={busy===r.id} onClick={()=>decide(r,true)}><Check size={15}/> Approve</button><button className="ghost-btn" disabled={busy===r.id} onClick={()=>decide(r,false)}>Reject</button></div></div>)}</div></Modal>}
function PlayerQrModal({onClose,pushToast}:{onClose:()=>void;pushToast:(s:string,t?:any)=>void}){const [token,setToken]=useState("");const [busy,setBusy]=useState(true);const load=async()=>{setBusy(true);try{const r=await api.rotatePlayerQr();setToken(r.token)}catch(e:any){pushToast(e.message,"warning")}finally{setBusy(false)}};useEffect(()=>{load()},[]);const value=token?`${window.location.origin}/request-points?token=${encodeURIComponent(token)}`:"";return <Modal title="My Quest QR" onClose={onClose}><div className="qr-modal">{busy?<div className="loader-ring"/>:token?<><div className="qr-frame"><QRCodeCanvas value={value} size={230} includeMargin/></div><h3>Show this code</h3><p className="muted">The code does not reveal the player's name. Scanning opens the extra-XP request form.</p><button className="ghost-btn wide" onClick={load}>Rotate QR</button></>:<p className="muted">Unable to generate your QR.</p>}</div></Modal>}
function PointRequestPage({token}:{token:string}){const [amount,setAmount]=useState(250);const [reason,setReason]=useState("");const [busy,setBusy]=useState(false);const [done,setDone]=useState(false);const [error,setError]=useState("");const submit=async()=>{setBusy(true);setError("");try{await api.createPointRequest({token,requested_xp:Number(amount),reason});setDone(true)}catch(e:any){setError(e.message)}finally{setBusy(false)}};if(done)return <div className="center-screen"><div className="login-card"><div className="brand centered"><div className="brand-mark">Q</div><div><strong>QUEST<span>HUB</span></strong><small>CUMBERNAULD CLIMB</small></div></div><span className="eyebrow">REQUEST SUBMITTED</span><h1>XP request sent.</h1><p>Your request is waiting for a youth worker to review. No XP has been awarded yet.</p></div></div>;return <div className="center-screen"><div className="login-card"><div className="brand centered"><div className="brand-mark">Q</div><div><strong>QUEST<span>HUB</span></strong><small>CUMBERNAULD CLIMB</small></div></div><span className="eyebrow">QUEST POINTS</span><h1>Request extra XP.</h1><p>Explain what was achieved. A youth worker must approve the request before XP is added.</p>{error&&<div className="api-error">{error}</div>}<label>XP requested<input type="number" min="1" max="5000" value={amount} onChange={e=>setAmount(Number(e.target.value))}/></label><label>Reason<textarea value={reason} onChange={e=>setReason(e.target.value)} placeholder="What was achieved or contributed?"/></label><button className="primary-btn wide" disabled={busy||reason.trim().length<3} onClick={submit}>{busy?"Submitting…":"Submit request"}</button></div></div>}

function AwardModal({players,selected,setSelected,onClose,pushToast}:{players:any[];selected:any;setSelected:(p:any)=>void;onClose:()=>void;pushToast:(s:string,t?:any)=>void}){const[pick,setPick]=useState(selected?.id??players[0]?.id??"");const[amount,setAmount]=useState(500);const[reason,setReason]=useState("Positive participation");return <Modal title="Award Points" onClose={onClose}><div className="form-grid"><label>Player<select value={pick} onChange={e=>{setPick(Number(e.target.value));setSelected(players.find(p=>p.id===Number(e.target.value)))}}>{players.map(p=><option key={p.id} value={p.id}>{p.gamertag}</option>)}</select></label><label>Amount<input type="number" value={amount} onChange={e=>setAmount(Number(e.target.value))}/></label><label>Reason<textarea value={reason} onChange={e=>setReason(e.target.value)}/></label></div><button className="primary-btn wide" onClick={async()=>{try{await api.awardXp(Number(pick),amount,reason);pushToast(`+${amount.toLocaleString()} XP awarded`);onClose()}catch(e:any){pushToast(e.message,"warning")}}}><Plus size={17}/> Award XP</button></Modal>}


function UserManagerModal({users,onClose,refresh,pushToast}:{users:any[];onClose:()=>void;refresh:()=>Promise<void>;pushToast:(s:string,t?:any)=>void}){const [editing,setEditing]=useState<any>(null);const [form,setForm]=useState<any>({username:"",password:"",role:"player",display_name:"",gamertag:"",avatar:"avatar-01",group_id:"",public_visible:true});const [busy,setBusy]=useState(false);const set=(k:string,v:any)=>setForm((x:any)=>({...x,[k]:v}));const open=(u:any)=>{setEditing(u);setForm({username:u.username,password:"",role:u.role,display_name:u.display_name??"",gamertag:u.player?.gamertag??"",avatar:u.player?.avatar??"avatar-01",group_id:u.player?.group_id??"",public_visible:u.player?.public_visible??true})};const create=()=>{setEditing(null);setForm({username:"",password:"",role:"player",display_name:"",gamertag:"",avatar:"avatar-01",group_id:"",public_visible:true})};const save=async()=>{setBusy(true);try{const body:any={username:form.username,role:form.role,display_name:form.display_name||null};if(form.password)body.password=form.password;if(form.role==="player"){body.gamertag=form.gamertag;body.avatar=form.avatar;body.public_visible=!!form.public_visible;if(form.group_id!=="")body.group_id=Number(form.group_id)}if(editing)await api.updateUser(editing.id,body);else await api.createUser({...body,password:form.password,active:true});pushToast(editing?"Account updated":"User created");await refresh();if(!editing)create()}catch(e:any){pushToast(e.message,"warning")}finally{setBusy(false)}};const action=async(u:any,kind:string)=>{try{if(kind==="pause")await api.pauseUser(u.id);if(kind==="reactivate")await api.reactivateUser(u.id);if(kind==="suspend"&&u.player)await api.suspendPlayer(u.player.id);if(kind==="unsuspend"&&u.player)await api.unsuspendPlayer(u.player.id);pushToast(kind+" complete");await refresh()}catch(e:any){pushToast(e.message,"warning")}};return <Modal title="Manage accounts" onClose={onClose}><div className="user-manager"><div className="section-heading"><span className="eyebrow">ADMIN ONLY</span><button className="primary-btn" onClick={create}><Plus size={15}/> New user</button></div><div className="form-grid"><label>Username<input value={form.username} onChange={e=>set("username",e.target.value)} /></label><label>Role<select value={form.role} onChange={e=>set("role",e.target.value)}><option value="player">Young person</option><option value="youth_worker">Youth worker</option><option value="admin">Admin</option></select></label><label>Password {editing&&<small>(leave blank to keep current)</small>}<input type="password" value={form.password} onChange={e=>set("password",e.target.value)} placeholder="Minimum 10 characters" /></label>{form.role==="player"&&<><label>Gamertag<input value={form.gamertag} onChange={e=>set("gamertag",e.target.value)} /></label><label>Group ID<input type="number" value={form.group_id} onChange={e=>set("group_id",e.target.value)} placeholder="Optional" /></label><label>Avatar<input value={form.avatar} onChange={e=>set("avatar",e.target.value)} /></label></>}</div><button className="primary-btn wide" disabled={busy||!form.username||(!editing&&!form.password)} onClick={save}>{busy?"Saving…":editing?"Save changes":"Create user"}</button><div className="panel inset"><div className="panel-head"><h3>Accounts</h3><span className="count-pill">{users.length}</span></div>{users.map((u:any)=><div className="setting-line" key={u.id}><div><b>{u.username}</b><small style={{display:"block",color:"#70808e"}}>{u.role} · {u.player?.gamertag??u.display_name??"Staff account"}</small></div><div className="nom-actions"><span className={`status ${u.active?"":"inactive"}`}>{u.active?"Active":"Paused"}</span><button className="ghost-btn" onClick={()=>open(u)}>Edit</button>{u.active?<button className="ghost-btn" onClick={()=>action(u,"pause")}>Pause</button>:<button className="ghost-btn" onClick={()=>action(u,"reactivate")}>Reactivate</button>}{u.player&&(u.player.suspended?<button className="ghost-btn" onClick={()=>action(u,"unsuspend")}>Unsuspend</button>:<button className="ghost-btn" onClick={()=>action(u,"suspend")}>Suspend</button>)}</div></div>)}</div></div></Modal>}
function EconomyModal({onClose,pushToast}:{onClose:()=>void;pushToast:(s:string,t?:any)=>void}){const [v,setV]=useState<any>(null);const [busy,setBusy]=useState(false);useEffect(()=>{api.economy().then(setV).catch(e=>pushToast(e.message,"warning"))},[]);if(!v)return <Modal title="Economy settings" onClose={onClose}><p className="muted">Loading…</p></Modal>;const set=(k:string,x:any)=>setV((a:any)=>({...a,[k]:x}));const save=async()=>{setBusy(true);try{await api.updateEconomy({jackpot_target_xp:Number(v.jackpot_target_xp),max_group_penalty_percent:Number(v.max_group_penalty_percent),max_staff_multiplier:Number(v.max_staff_multiplier),weekly_growth_cap_multiplier:Number(v.weekly_growth_cap_multiplier),group_penalties_enabled:!!v.group_penalties_enabled,multipliers_enabled:!!v.multipliers_enabled});pushToast("Economy saved");onClose()}catch(e:any){pushToast(e.message,"warning")}finally{setBusy(false)}};return <Modal title="Economy settings" onClose={onClose}><div className="form-grid"><label>Jackpot target XP<input type="number" value={v.jackpot_target_xp} onChange={e=>set("jackpot_target_xp",e.target.value)}/></label><label>Max group penalty %<input type="number" value={v.max_group_penalty_percent} onChange={e=>set("max_group_penalty_percent",e.target.value)}/></label><label>Max staff multiplier<input type="number" step="0.1" value={v.max_staff_multiplier} onChange={e=>set("max_staff_multiplier",e.target.value)}/></label><label>Weekly growth cap multiplier<input type="number" step="0.1" value={v.weekly_growth_cap_multiplier} onChange={e=>set("weekly_growth_cap_multiplier",e.target.value)}/></label><label>Group penalties<select value={String(!!v.group_penalties_enabled)} onChange={e=>set("group_penalties_enabled",e.target.value==="true")}><option value="true">Enabled</option><option value="false">Disabled</option></select></label><label>Multipliers<select value={String(!!v.multipliers_enabled)} onChange={e=>set("multipliers_enabled",e.target.value==="true")}><option value="true">Enabled</option><option value="false">Disabled</option></select></label></div><button className="primary-btn wide" disabled={busy} onClick={save}>{busy?"Saving…":"Save economy"}</button></Modal>}
function RewardManagerModal({onClose,pushToast}:{onClose:()=>void;pushToast:(s:string,t?:any)=>void}){const [games,setGames]=useState<any[]>([]);const [targets,setTargets]=useState<any>({players:[],groups:[]});const [form,setForm]=useState<any>({name:"Spin the Wheel",description:"",game_type:"wheel",prize_values:"500,1000,2000",starts_at:"",ends_at:"",active:true,show_upcoming:true});const [target,setTarget]=useState("player");const [targetId,setTargetId]=useState("");const load=async()=>{try{const [g,t]=await Promise.all([api.adminRewardGames(),api.rewardGameTargets()]);setGames(g);setTargets(t)}catch(e:any){pushToast(e.message,"warning")}};useEffect(()=>{load()},[]);const set=(k:string,x:any)=>setForm((a:any)=>({...a,[k]:x}));const create=async()=>{try{await api.createRewardGame({...form,prize_values:form.prize_values.split(",").map((x:string)=>Number(x.trim())).filter((x:number)=>Number.isFinite(x)),starts_at:form.starts_at||null,ends_at:form.ends_at||null});pushToast("Reward game created");await load()}catch(e:any){pushToast(e.message,"warning")}};const grant=async(game:any)=>{if(!targetId)return;try{await api.grantRewardGame(game.id,target==="player"?{player_id:Number(targetId)}:{group_id:Number(targetId)});pushToast("Reward entitlement granted")}catch(e:any){pushToast(e.message,"warning")}};const toggle=async(g:any)=>{try{await api.updateRewardGame(g.id,{active:!g.active});pushToast(g.active?"Reward game paused":"Reward game activated");await load()}catch(e:any){pushToast(e.message,"warning")}};return <Modal title="Reward games" onClose={onClose}><div className="form-grid"><label>Name<input value={form.name} onChange={e=>set("name",e.target.value)}/></label><label>Description<textarea value={form.description} onChange={e=>set("description",e.target.value)}/></label><label>Prize values (XP, comma separated)<input value={form.prize_values} onChange={e=>set("prize_values",e.target.value)} placeholder="500,1000,2000"/></label><label>Starts at<input type="datetime-local" value={form.starts_at} onChange={e=>set("starts_at",e.target.value)}/></label><label>Ends at<input type="datetime-local" value={form.ends_at} onChange={e=>set("ends_at",e.target.value)}/></label></div><button className="primary-btn wide" onClick={create}><Plus size={15}/> Create reward game</button><div className="panel inset" style={{marginTop:12}}><div className="panel-head"><h3>Grant entitlement</h3></div><div className="form-grid"><label>Target<select value={target} onChange={e=>{setTarget(e.target.value);setTargetId("")}}><option value="player">Player</option><option value="group">Group</option></select></label><label>{target==="player"?"Player":"Group"}<select value={targetId} onChange={e=>setTargetId(e.target.value)}><option value="">Select…</option>{target==="player"?targets.players.map((p:any)=><option key={p.id} value={p.id}>{p.gamertag}</option>):targets.groups.map((g:any)=><option key={g.id} value={g.id}>{g.name}</option>)}</select></label></div>{games.map(g=><div className="setting-line" key={g.id}><span><b>{g.name}</b><small style={{display:"block",color:"#70808e"}}>{g.active?"Active":"Paused"} · {g.available_entitlements} available · prizes hidden from players</small></span><div className="nom-actions"><button className="ghost-btn" onClick={()=>toggle(g)}>{g.active?"Pause":"Activate"}</button><button className="secondary-btn" disabled={!targetId||!g.active} onClick={()=>grant(g)}>Grant</button></div></div>)}</div></Modal>}
function EconomyPanel({openEconomy}:{openEconomy:()=>void}){return <div className="page"><div className="section-heading"><div><span className="eyebrow">SYSTEM SETTINGS</span><h2>Programme economy</h2></div><button className="primary-btn" onClick={openEconomy}><Settings size={16}/> Configure</button></div><div className="panel"><p className="muted">Admin-controlled jackpot target, penalty ceiling, staff multiplier, growth cap and economy toggles.</p></div></div>}
