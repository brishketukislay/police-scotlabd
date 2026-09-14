import { useEffect, useMemo, useState } from "react";
import { QRCodeCanvas } from "qrcode.react";
import { Activity, AlertTriangle, ArrowUpRight, Award, BarChart3, Bell, Check, ChevronRight, CircleHelp, Gauge, LayoutDashboard, LogOut, Map, Menu, MoreHorizontal, Plus, Search, Settings, ShieldCheck, Sparkles, Trophy, Users, WalletCards, X, Zap } from "lucide-react";
import { api, type Role, type SessionUser } from "./api";

type Toast = {id:number;text:string;tone?:"success"|"info"|"warning"};

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
      {publicMode?<PublicView data={data} section={section}/>:user?.role==="player"?<PlayerView data={data} section={section} openWheel={()=>setWheelOpen(true)} openQr={()=>setPlayerQrOpen(true)} pushToast={pushToast}/>:<StaffView role={user?.role} data={data} section={section} setSelectedPlayer={setSelectedPlayer} openAward={()=>setAwardOpen(true)} openWheel={()=>setWheelOpen(true)} pushToast={pushToast} openUsers={()=>setUserManagerOpen(true)} openEconomy={()=>setEconomyOpen(true)} openRewards={()=>setRewardManagerOpen(true)} openPointRequests={()=>setPointRequestsOpen(true)} refresh={refresh}/>} 
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

function Login({onLogin,onPublic,error}:{onLogin:(u:string,p:string)=>void;onPublic:()=>void;error:string}){const [u,setU]=useState("");const[p,setP]=useState("");return <div className="login-screen"><div className="login-card"><div className="brand centered"><div className="brand-mark">Q</div><div><strong>QUEST<span>HUB</span></strong><small>CUMBERNAULD CLIMB</small></div></div><div className="eyebrow">NEW FRONTEND / API CONNECTED</div><h1>Enter the climb.</h1><p>Use an account from the supplied FastAPI backend, or preview the public dashboard.</p>{error&&<div className="api-error">{error}</div>}<label>Username<input value={u} onChange={e=>setU(e.target.value)} placeholder="admin / youthworker / player01"/></label><label>Password<input type="password" value={p} onChange={e=>setP(e.target.value)} placeholder="Password" onKeyDown={e=>e.key==="Enter"&&onLogin(u,p)}/></label><button className="primary-btn wide" onClick={()=>onLogin(u,p)}>Sign in <ArrowUpRight size={15}/></button><button className="ghost-btn wide" onClick={onPublic}>View public dashboard</button><small className="login-note">Sessions use the backend's HttpOnly cookie. No token is stored in localStorage.</small></div></div>}

function StaffView({role,data,section,setSelectedPlayer,openAward,openWheel,pushToast,openUsers,openEconomy,openRewards,openPointRequests,refresh}:{role?:Role;data:any;section:string;setSelectedPlayer:(p:any)=>void;openAward:()=>void;openWheel:()=>void;pushToast:(s:string,t?:any)=>void;openUsers:()=>void;openEconomy:()=>void;openRewards:()=>void;openPointRequests:()=>void;refresh:()=>Promise<void>}){if(section==="Groups")return <Groups data={data} pushToast={pushToast}/>;if(section==="Players"||section==="Users & Groups")return <Players data={data} setSelectedPlayer={setSelectedPlayer} openAward={openAward} openUsers={openUsers} pushToast={pushToast} refresh={refresh}/>;if(section==="Points & Rewards")return <Points openAward={openAward} pushToast={pushToast} openEconomy={openEconomy} openRewards={openRewards}/>;if(section==="Points Requests")return <PointRequests data={data} openPointRequests={openPointRequests} pushToast={pushToast} refresh={refresh}/>;if(section==="Challenges")return <Challenges openWheel={openWheel} pushToast={pushToast}/>;if(section==="Analytics")return <Analytics pushToast={pushToast}/>;if(section==="System Settings")return <EconomyPanel openEconomy={openEconomy}/>;return <Overview data={data} role={role} openAward={openAward} openWheel={openWheel} openRewards={openRewards} pushToast={pushToast}/>}


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

function Overview({data,role,openAward,openWheel,openRewards,pushToast}:{data:any;role?:Role;openAward:()=>void;openWheel:()=>void;openRewards:()=>void;pushToast:(s:string,t?:any)=>void}){const o=data?.overview??{};const pct=o.target_xp?Math.min(100,(o.group_xp/o.target_xp)*100):0;const ps=data?.players??demoPlayers;return <div className="page"><section className="hero-grid"><div className="hero-card"><div className="hero-copy"><div className="badge-line"><span className="live-dot"/> LIVE API DATA</div><h2>{Number(o.group_xp??0).toLocaleString()} <span>XP</span></h2><p>{pct.toFixed(0)}% toward the <b>{Number(o.target_xp??1500000).toLocaleString()} XP jackpot</b></p><div className="progress"><i style={{width:`${pct}%`}}/></div><div className="milestones"><span><b>500K</b><small>£250</small></span><span><b>1M</b><small>£750</small></span><span><b>1.5M</b><small>£2,200</small></span></div></div><div className="hero-visual"><div className="orbit orbit-1"/><div className="orbit orbit-2"/><Trophy size={46}/></div></div><div className="map-card"><div className="card-head"><div><span className="eyebrow">CURRENT PROGRAMME</span><h3>{o.programme??"Youth Challenge"}</h3></div><Map size={19}/></div><div className="map-art"><div className="map-lines"/><div className="map-pin p1"/><div className="map-pin p2"/><div className="map-pin p3"/></div><button className="ghost-btn">Open Cumbernauld map <ArrowUpRight size={15}/></button></div></section><section className="stats-grid"><Stat icon={<Users/>} label="Active players" value={String(o.players??ps.length)} delta={`${o.staff??0} staff`}/><Stat icon={<Gauge/>} label="Programme target" value={Number(o.target_xp??0).toLocaleString()} delta={`${Number(o.weekly_target_xp??0).toLocaleString()} weekly`}/><Stat icon={<Award/>} label="Public visibility" value="API" delta="Controlled by backend"/><Stat icon={<Activity/>} label="Data source" value="Live" delta="FastAPI + SQLite"/></section><section className="content-grid"><div className="panel large"><div className="panel-head"><div><span className="eyebrow">LIVE PLAYERS</span><h3>Progress from the backend</h3></div><button className="icon-btn"><MoreHorizontal/></button></div>{ps.slice(0,5).map((p:any)=><div className="activity" key={p.id??p.gamertag}><div className="mini-avatar">{(p.gamertag??"P")[0]}</div><div><b>{p.gamertag}</b><span>{Number(p.xp??0).toLocaleString()} XP · {p.public_visible===false?"Private":"Visible"}</span></div><strong>{p.status??"Active"}</strong><small>{p.badge??""}</small></div>)}</div><div className="panel"><div className="panel-head"><div><span className="eyebrow">SUPPORT SIGNALS</span><h3>Not surveillance</h3></div><AlertTriangle size={18}/></div><div className="risk-list">{ps.slice(0,4).map((p:any)=><div className="risk" key={p.id??p.gamertag}><div className="mini-avatar">{(p.gamertag??"P")[0]}</div><div><b>{p.gamertag}</b><span>Use activity data to support engagement.</span></div><span className="status">{p.active===false?"Inactive":"Active"}</span></div>)}</div></div></section><section className="panel jackpot"><div><span className="eyebrow">QUICK ACTIONS</span><h3>Keep the experience moving</h3><p>Award XP or open a configured reward-game flow.</p></div><div className="jackpot-actions"><button className="secondary-btn" onClick={openRewards}><Sparkles size={17}/> Reward game</button><button className="primary-btn" onClick={openAward}><Plus size={17}/> Award XP</button></div></section></div>}


function Groups({data,pushToast}:{data:any;pushToast:(s:string,t?:any)=>void}){
  const [groups,setGroups]=useState<any[]>([]);
  const [players,setPlayers]=useState<any[]>(data?.players??[]);
  const [selected,setSelected]=useState<any>(null);
  const [name,setName]=useState("");
  const [editing,setEditing]=useState(false);
  const [busy,setBusy]=useState(false);

  const load=async()=>{
    try{
      const result=await api.staffGroups();
      setGroups(result);
      if(selected){
        setSelected(result.find((g:any)=>g.id===selected.id)??null);
      }
    }catch(e:any){
      pushToast(e.message,"warning");
    }
  };

  useEffect(()=>{
    load();
  },[]);

  useEffect(()=>{
    setPlayers(data?.players??[]);
  },[data?.players]);

  const create=async()=>{
    const clean=name.trim();
    if(clean.length<2){
      pushToast("Enter a group name.","warning");
      return;
    }

    setBusy(true);

    try{
      await api.createStaffGroup({
        name:clean,
        player_ids:[],
      });

      setName("");
      pushToast("Group created");
      await load();
    }catch(e:any){
      pushToast(e.message,"warning");
    }finally{
      setBusy(false);
    }
  };

  const save=async()=>{
    if(!selected)return;

    const clean=name.trim();

    if(clean.length<2){
      pushToast("Enter a group name.","warning");
      return;
    }

    setBusy(true);

    try{
      await api.updateStaffGroup(selected.id,{
        name:clean,
        active:selected.active,
      });

      pushToast("Group updated");
      setEditing(false);
      await load();
    }catch(e:any){
      pushToast(e.message,"warning");
    }finally{
      setBusy(false);
    }
  };

  const toggle=async(group:any)=>{
    try{
      await api.updateStaffGroup(group.id,{
        name:group.name,
        active:!group.active,
      });

      pushToast(group.active?"Group deactivated":"Group activated");
      await load();
    }catch(e:any){
      pushToast(e.message,"warning");
    }
  };

  const add=async(playerId:number)=>{
    if(!selected)return;

    try{
      await api.addPlayerToGroup(selected.id,playerId);
      pushToast("Young person added to group");
      await load();
    }catch(e:any){
      pushToast(e.message,"warning");
    }
  };

  const remove=async(playerId:number)=>{
    if(!selected)return;

    try{
      await api.removePlayerFromGroup(selected.id,playerId);
      pushToast("Young person removed from group");
      await load();
    }catch(e:any){
      pushToast(e.message,"warning");
    }
  };

  const members=selected?.players??[];
  const memberIds=new Set(members.map((p:any)=>p.id));
  const available=players.filter((p:any)=>p.active!==false&&!memberIds.has(p.id));

  return <div className="page">
    <div className="section-heading">
      <div>
        <span className="eyebrow">GROUP MANAGEMENT</span>
        <h2>Groups</h2>
        <p>Create groups and manage young-person membership.</p>
      </div>
    </div>

    <section className="content-grid">
      <div className="panel">
        <div className="panel-head">
          <div>
            <span className="eyebrow">NEW GROUP</span>
            <h3>Create a group</h3>
          </div>
          <Users size={18}/>
        </div>

        <div className="form-grid">
          <label>
            Group name
            <input
              value={name}
              onChange={e=>setName(e.target.value)}
              placeholder="e.g. Friday Squad"
              disabled={busy}
            />
          </label>
        </div>

        <button
          className="primary-btn wide"
          onClick={create}
          disabled={busy}
        >
          <Plus size={16}/>
          {busy?"Creating…":"Create group"}
        </button>
      </div>

      <div className="panel">
        <div className="panel-head">
          <div>
            <span className="eyebrow">GROUPS</span>
            <h3>{groups.length} group{groups.length===1?"":"s"}</h3>
          </div>
          <span className="count-pill">{groups.filter((g:any)=>g.active).length} active</span>
        </div>

        {groups.length===0 ? (
          <div className="empty-state">No groups have been created yet.</div>
        ) : (
          <div className="analytics-list">
            {groups.map((group:any)=>(
              <button
                key={group.id}
                className="setting-line"
                style={{
                  width:"100%",
                  textAlign:"left",
                  cursor:"pointer",
                  background:selected?.id===group.id?"rgba(100,231,255,.06)":"transparent",
                  border:"0",
                  color:"inherit"
                }}
                onClick={()=>{
                  setSelected(group);
                  setName(group.name);
                  setEditing(false);
                }}
              >
                <span>
                  <b>{group.name}</b>
                  <small style={{display:"block",color:"#70808e"}}>
                    {group.player_count} young person{group.player_count===1?"":"s"} · {group.active?"Active":"Inactive"}
                  </small>
                </span>
                <ChevronRight size={16}/>
              </button>
            ))}
          </div>
        )}
      </div>
    </section>

    {selected&&<section className="content-grid">
      <div className="panel large">
        <div className="panel-head">
          <div>
            <span className="eyebrow">SELECTED GROUP</span>
            {editing ? (
              <div style={{display:"flex",gap:8,alignItems:"center"}}>
                <input
                  value={name}
                  onChange={e=>setName(e.target.value)}
                  style={{maxWidth:280}}
                />
                <button className="primary-btn" onClick={save} disabled={busy}>
                  Save
                </button>
                <button
                  className="ghost-btn"
                  onClick={()=>{
                    setEditing(false);
                    setName(selected.name);
                  }}
                >
                  Cancel
                </button>
              </div>
            ) : (
              <h3>{selected.name}</h3>
            )}
          </div>

          <div className="nom-actions">
            {!editing&&<button
              className="ghost-btn"
              onClick={()=>setEditing(true)}
            >
              Edit
            </button>}
            <button
              className="ghost-btn"
              onClick={()=>toggle(selected)}
            >
              {selected.active?"Deactivate":"Activate"}
            </button>
          </div>
        </div>

        <div className="panel inset">
          <div className="panel-head">
            <div>
              <span className="eyebrow">MEMBERS</span>
              <h3>{members.length} young person{members.length===1?"":"s"}</h3>
            </div>
          </div>

          {members.length===0 ? (
            <div className="empty-state">
              No young people are currently in this group.
            </div>
          ) : (
            members.map((player:any)=>(
              <div className="setting-line" key={player.id}>
                <span>
                  <b>{player.gamertag}</b>
                  <small style={{display:"block",color:"#70808e"}}>
                    {Number(player.xp??0).toLocaleString()} XP
                  </small>
                </span>
                <button
                  className="ghost-btn"
                  onClick={()=>remove(player.id)}
                >
                  Remove
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="panel">
        <div className="panel-head">
          <div>
            <span className="eyebrow">ADD MEMBERS</span>
            <h3>Available young people</h3>
          </div>
          <Users size={18}/>
        </div>

        {!selected.active ? (
          <div className="empty-state">
            Activate this group before adding young people.
          </div>
        ) : available.length===0 ? (
          <div className="empty-state">
            All active young people are already in this group.
          </div>
        ) : (
          available.map((player:any)=>(
            <div className="setting-line" key={player.id}>
              <span>
                <b>{player.gamertag}</b>
                <small style={{display:"block",color:"#70808e"}}>
                  {player.group_id
                    ? `Currently in group #${player.group_id}`
                    : "No group"}
                </small>
              </span>
              <button
                className="secondary-btn"
                onClick={()=>add(player.id)}
              >
                Add
              </button>
            </div>
          ))
        )}
      </div>
    </section>}
  </div>
}

function Players({data,setSelectedPlayer,openAward,openUsers,pushToast,refresh}:{data:any;setSelectedPlayer:(p:any)=>void;openAward:()=>void;openUsers:()=>void;pushToast:(s:string,t?:any)=>void;refresh:()=>Promise<void>}){const ps=data?.players??[];return <div className="page"><div className="section-heading"><div><span className="eyebrow">PLAYER MANAGEMENT</span><h2>People, progress and support</h2></div><div className="jackpot-actions"><button className="ghost-btn" onClick={openUsers}><Users size={15}/> Manage accounts</button><button className="primary-btn" onClick={openAward}><Plus size={17}/> Award points</button></div></div><div className="panel player-table"><div className="search-row"><div className="search-box"><Search size={16}/><input placeholder="Search players…"/></div></div>{ps.map((p:any)=><button className="player-row" key={p.id} onClick={()=>setSelectedPlayer(p)}><div className="avatar lime">{(p.gamertag??"P")[0]}</div><div><b>{p.gamertag}</b><span>#{p.id} · {Number(p.xp??0).toLocaleString()} XP · Group {p.group_id??"—"}</span></div><span className={`status ${p.suspended?"at-risk":p.active?"":"inactive"}`}>{p.suspended?"Suspended":p.active?"Active":"Inactive"}</span><ChevronRight size={16}/></button>)}</div></div>}

function Points({openAward,pushToast,openEconomy,openRewards}:{openAward:()=>void;pushToast:(s:string,t?:any)=>void;openEconomy:()=>void;openRewards:()=>void}){return <div className="page"><div className="section-heading"><div><span className="eyebrow">POINTS & REWARDS</span><h2>Configure the economy</h2></div><button className="primary-btn" onClick={openAward}><Plus size={17}/> Award points</button></div><div className="content-grid"><div className="panel"><div className="panel-head"><h3>Economy settings</h3><Settings size={18}/></div><p className="muted">Control jackpot target, group penalty ceiling, multipliers and economy toggles from the admin dashboard.</p><button className="primary-btn wide" onClick={openEconomy}>Open economy settings</button></div><div className="panel"><div className="panel-head"><h3>Reward games</h3><Sparkles size={18}/></div><p className="muted">Create, pause, edit prize values and grant Spin the Wheel entitlements to players or groups.</p><button className="secondary-btn wide" onClick={openRewards}>Manage reward games</button></div></div><div className="panel"><div className="panel-head"><h3>Existing controls</h3></div>{["Point rules","Rewards","Jackpot","Phases","Themes"].map(x=><div className="setting-line" key={x}><span>{x}</span><button className="ghost-btn" onClick={()=>pushToast(`${x} is available in the API and can be connected next`,"info")}>API</button></div>)}</div></div>}

function Challenges({openWheel,pushToast}:{openWheel:()=>void;pushToast:(s:string,t?:any)=>void}){return <div className="page"><div className="section-heading"><div><span className="eyebrow">CHALLENGES & REWARD GAMES</span><h2>Interactive moments</h2></div><button className="primary-btn" onClick={()=>pushToast("Challenge creation UI can be mapped to /api/challenges","info")}>New challenge</button></div><div className="challenge-grid"><div className="panel challenge-card"><div className="challenge-icon"><Sparkles/></div><span className="eyebrow">REWARD GAME</span><h3>Spin the Wheel</h3><strong>Server-side prize selection</strong><p>Uses the backend reward-game entitlement and play endpoint.</p><button className="secondary-btn" onClick={openWheel}>Open wheel</button></div><div className="panel challenge-card"><div className="challenge-icon"><Zap/></div><span className="eyebrow">FLASH CHALLENGE</span><h3>Time-bound game</h3><strong>/api/challenges</strong><p>Challenge listing and attempt APIs are ready for mapping.</p><button className="ghost-btn" onClick={()=>pushToast("Challenge endpoints detected","info")}>API connected</button></div><div className="panel challenge-card"><div className="challenge-icon"><Trophy/></div><span className="eyebrow">DRAWING GAME</span><h3>Draw It Clean</h3><strong>/api/drawing-games</strong><p>Player/admin drawing game routes exist in the backend.</p><button className="ghost-btn" onClick={()=>pushToast("Drawing game endpoints detected","info")}>API connected</button></div></div></div>}


function SkillTree({dash}:{dash:any}) {
  const xp = Number(dash?.player?.xp ?? 0);
  const tree = dash?.skill_tree;
  const milestones = Array.isArray(tree?.milestones)
    ? tree.milestones
    : [];

  if (!milestones.length) {
    return (
      <section className="panel skill-tree-panel">
        <div className="panel-head">
          <div>
            <span className="eyebrow">SKILL TREE</span>
            <h3>Your progression</h3>
          </div>
        </div>
        <p className="muted">
          Your next progression stages will appear here.
        </p>
      </section>
    );
  }

  /*
   * Sort by required XP so the visual path always progresses
   * from the first stage to the final stage.
   */
  const stages = [...milestones].sort(
    (a:any,b:any) =>
      Number(a.required_xp ?? 0) - Number(b.required_xp ?? 0)
  );

  const completed = stages.filter(
    (m:any) => xp >= Number(m.required_xp ?? 0)
  ).length;

  const currentIndex = Math.min(
    completed,
    Math.max(0, stages.length - 1)
  );

  const progressToNext = (() => {
    if (completed >= stages.length) return 100;

    const previousXp =
      completed > 0
        ? Number(stages[completed - 1]?.required_xp ?? 0)
        : 0;

    const nextXp =
      Number(stages[completed]?.required_xp ?? 0);

    if (nextXp <= previousXp) return 0;

    return Math.max(
      0,
      Math.min(
        100,
        ((xp - previousXp) / (nextXp - previousXp)) * 100
      )
    );
  })();

  return (
    <section className="panel skill-tree-panel">

      <div className="panel-head skill-tree-head">
        <div>
          <span className="eyebrow">SKILL TREE</span>
          <h3>{tree?.name ?? "Your progression"}</h3>
          <p className="muted">
            Build XP, unlock each stage and reach the top.
          </p>
        </div>

        <div className="skill-tree-score">
          <strong>{xp.toLocaleString()}</strong>
          <span>XP</span>
        </div>
      </div>

      <div className="skill-tree-graphic">

        <div className="skill-tree-line">
          <i
            style={{
              width: `${
                stages.length > 1
                  ? (
                      (Math.min(completed, stages.length - 1) /
                        (stages.length - 1)) * 100
                    ) + (
                      completed < stages.length
                        ? (progressToNext /
                            (stages.length - 1))
                        : 0
                    )
                  : 100
              }%`
            }}
          />
        </div>

        <div className="skill-tree-stages">
          {stages.map((stage:any, i:number) => {
            const required = Number(stage.required_xp ?? 0);
            const isComplete = xp >= required;
            const isCurrent =
              !isComplete &&
              i === currentIndex;

            const remaining = Math.max(0, required - xp);

            return (
              <div
                className={[
                  "skill-stage",
                  isComplete ? "complete" : "",
                  isCurrent ? "current" : "locked"
                ].join(" ")}
                key={stage.id ?? stage.name ?? i}
              >

                <div className="skill-stage-orb">
                  <div className="skill-stage-core">
                    {isComplete ? "✓" : i + 1}
                  </div>
                </div>

                <div className="skill-stage-card">

                  <span className="skill-stage-label">
                    {isComplete
                      ? "UNLOCKED"
                      : isCurrent
                        ? "NEXT STAGE"
                        : "LOCKED"}
                  </span>

                  <strong>
                    {stage.name ?? `Stage ${i + 1}`}
                  </strong>

                  <span className="skill-stage-xp">
                    {required.toLocaleString()} XP
                  </span>

                  {isCurrent && (
                    <small>
                      {remaining.toLocaleString()} XP to unlock
                    </small>
                  )}

                  {isComplete && (
                    <small>
                      Stage complete
                    </small>
                  )}

                </div>
              </div>
            );
          })}
        </div>

      </div>

      <div className="skill-tree-footer">
        <div>
          <span>STAGES UNLOCKED</span>
          <strong>
            {completed} / {stages.length}
          </strong>
        </div>

        <div className="skill-tree-next">
          {completed >= stages.length ? (
            <>
              <span>SKILL TREE COMPLETE</span>
              <strong>MAX LEVEL</strong>
            </>
          ) : (
            <>
              <span>NEXT UNLOCK</span>
              <strong>
                {Number(
                  stages[completed]?.required_xp ?? 0
                ).toLocaleString()} XP
              </strong>
            </>
          )}
        </div>
      </div>

    </section>
  );
}

function PlayerView({data,section,openWheel,openQr,pushToast}:{data:any;section:string;openWheel:()=>void;openQr:()=>void;pushToast:(s:string,t?:any)=>void}){const p=data?.player?.player??data?.player?.player;const dash=data?.player??{};if(section==="Challenges")return <div className="page"><div className="section-heading"><div><span className="eyebrow">LIVE CHALLENGES</span><h2>{dash.phase?.name??"Current phase"}</h2></div></div>{(dash.challenges??[]).map((c:any)=><div className="panel challenge-card" key={c.id}><span className="eyebrow">CHALLENGE</span><h3>{c.title}</h3><p>{c.description}</p><strong>{c.participation_xp} XP participation · {c.elite_xp} XP elite</strong></div>)}</div>;if(section==="Rewards")return <div className="page"><div className="section-heading"><div><span className="eyebrow">REWARD VAULT</span><h2>Spin the Wheel</h2></div></div><div className="panel jackpot"><div><h3>{data?.games?.available?.length??0} reward game(s) available</h3><p>Rewards are selected server-side by the backend. Every result is a configured non-negative prize value.</p></div><button className="primary-btn" onClick={openWheel}><Sparkles size={17}/> Spin</button></div></div>;return <div className="page"><section className="hero-grid"><div className="hero-card"><div><span className="eyebrow">PLAYER PROFILE</span><h2>{dash.player?.xp?.toLocaleString?.()??0} <span>XP</span></h2><h3>{dash.player?.gamertag??"Player"}</h3><p>{dash.group?.name??"No group"} · {dash.phase?.name??"No active phase"}</p><div className="progress"><i style={{width:`${Math.min(100,((dash.player?.xp??0)/75000)*100)}%`}}/></div></div><div className="hero-visual"><Trophy size={48}/></div></div><SkillTree dash={dash}/></section><div className="content-grid"><section className="content-grid">
  <div className="panel">
    <div className="panel-head">
      <div>
        <span className="eyebrow">MY PERFORMANCE</span>
        <h3>Your climb</h3>
      </div>
      <Gauge size={19}/>
    </div>
    <div className="stats-grid">
      <Stat
        label="My XP"
        value={Number(dash.performance?.player_xp ?? dash.player?.xp ?? 0).toLocaleString()}
        delta="Lifetime individual XP"
      />
      <Stat
        label="Group contribution"
        value={`${Number(dash.performance?.group?.player_contribution_pct ?? 0).toFixed(1)}%`}
        delta="Of current group XP"
      />
    </div>
  </div>

  <div className="panel">
    <div className="panel-head">
      <div>
        <span className="eyebrow">GROUP PERFORMANCE</span>
        <h3>{dash.performance?.group?.name ?? dash.group?.name ?? "No group"}</h3>
      </div>
      <Users size={19}/>
    </div>

    {dash.performance?.group ? (
      <>
        <div className="stats-grid">
          <Stat
            label="Group XP"
            value={Number(dash.performance.group.xp ?? 0).toLocaleString()}
            delta={`${dash.performance.group.member_count ?? 0} members`}
          />
          <Stat
            label="Group position"
            value={dash.performance.group.rank ? `#${dash.performance.group.rank}` : "—"}
            delta={`of ${dash.performance.group.groups_ranked ?? 0} groups`}
          />
        </div>

        <div className="setting-line">
          <span>Progress to programme target</span>
          <b>{Number(dash.performance.group.progress_pct ?? 0).toFixed(0)}%</b>
        </div>

        <div className="progress">
          <i style={{width:`${Math.min(100, Number(dash.performance.group.progress_pct ?? 0))}%`}}/>
        </div>
      </>
    ) : (
      <p className="muted">You are not currently assigned to a group.</p>
    )}
  </div>
</section>

<div className="panel">
  <div className="panel-head">
    <h3>Rewards</h3>
    <button className="secondary-btn" onClick={openWheel}>Open reward wheel</button>
  </div>
  {(dash.mystery_rewards??[]).map((r:any)=><div className="setting-line" key={r.id}><span>{r.name}</span><b>{r.unlocked?"Unlocked":`${r.xp_threshold} XP`}</b></div>)}
</div><div className="panel quest-qr-card"><div className="panel-head"><div><span className="eyebrow">YOUR QUEST QR</span><h3>Request extra XP</h3></div><Zap size={19}/></div><p className="muted">Show your personal QR to a youth worker or activity lead. They can submit a points request for you; staff approve it before XP is added.</p><button className="primary-btn wide" onClick={openQr}>Show my QR</button></div></div></div>}

function PublicView({data,section}:{data:any;section:string}){const xp=Number(data?.group_xp??0),target=Number(data?.programme?.target_xp??1500000),pct=target?Math.min(100,xp/target*100):0;return <div className="page public-page"><div className="public-hero"><div><span className="eyebrow">{data?.programme?.name??"CUMBERNAULD"} / PUBLIC</span><h2>Real actions.<br/><span>More rewards.</span><br/>A stronger squad.</h2><p>Anonymous progress powered by the live backend.</p></div><div className="public-score"><span>COLLECTIVE PROGRESS</span><strong>{xp.toLocaleString()}</strong><small>XP · {pct.toFixed(0)}%</small><div className="progress"><i style={{width:`${pct}%`}}/></div></div></div><section className="public-grid"><div className="panel"><div className="panel-head"><h3>Leaderboard</h3></div>{(data?.phases??[]).slice(0,5).map((x:any,i:number)=><div className="leader-row" key={x.id}><span className="rank">{i+1}</span><div className="avatar purple">{(x.name??"P")[0]}</div><b>{x.name}</b><strong>PHASE</strong></div>)}</div><div className="panel public-map"><div className="panel-head"><h3>{data?.map?.name??"Cumbernauld map"}</h3><Map size={18}/></div><div className="map-art big">{(data?.map?.locations??[]).map((l:any)=><div key={l.id} className="map-pin" style={{left:`${l.x}%`,top:`${l.y}%`}}/>)}<div className="map-lines"/></div></div><div className="panel"><div className="panel-head"><h3>Jackpot</h3></div>{[{x:500000,r:"£250"},{x:1000000,r:"£750"},{x:1500000,r:"£2,200"}].map(m=><div className="milestone-card" key={m.x}><b>{(m.x/1000).toLocaleString()}K XP</b><span>{xp>=m.x?"Unlocked":"Next milestone"}</span><strong>{m.r}</strong></div>)}</div></section></div>}


function WheelModal({data,onClose,pushToast}:{data:any;onClose:()=>void;pushToast:(s:string,t?:any)=>void}){
  const games = Array.isArray(data) ? data : (data?.available ?? []);
  const game = games[0];

  /*
   * The backend can expose either:
   *   segments: [{label, value}]
   * or the older:
   *   display_prizes: [...]
   *   prize_values: [...]
   *
   * The wheel only DISPLAYs these values.
   * The server remains responsible for selecting the actual reward.
   */
  const configuredSegments = Array.isArray(game?.segments)
    ? game.segments
    : Array.isArray(game?.display_prizes)
      ? game.display_prizes
      : Array.isArray(game?.prize_values)
        ? game.prize_values
        : [];

  // Never invent a reward when the admin has not configured one.
  // An empty reward list makes this wheel unavailable.
  const segments = configuredSegments;

  const [spinning,setSpinning] = useState(false);
  const [result,setResult] = useState<any>(null);
  const [rotation,setRotation] = useState(0);
  const [showReward,setShowReward] = useState(false);

  const resultLabel = result?.reward_label
    ?? result?.reward
    ?? (result?.awarded_xp != null
      ? `+${Number(result.awarded_xp).toLocaleString()} XP`
      : "Reward unlocked");

  // No configured reward = no playable wheel.
  if (!game || !segments.length) {
    return <Modal title={game?.name ?? "Reward game"} onClose={onClose}>
      <div className="panel inset" style={{padding:24,textAlign:"center"}}>
        <h3>No reward configured</h3>
        <p className="muted">
          This reward game is not available yet. A youth worker or admin
          needs to configure at least one reward before players can spin.
        </p>
        <button className="secondary-btn wide" onClick={onClose}>
          Close
        </button>
      </div>
    </Modal>;
  }

  const segmentLabel = (segment:any) => {
    if(segment == null) return "Reward";
    if(typeof segment === "string") return segment;
    if(typeof segment === "number") return String(segment);
    return String(
      segment.label
      ?? segment.name
      ?? segment.title
      ?? segment.display
      ?? (segment.value != null ? segment.value : "Reward")
    );
  };

  const spin = async()=>{
    if(!game || spinning) return;

    setSpinning(true);
    setResult(null);
    setShowReward(false);

    /*
     * Purely visual rotation.
     * The winning reward is still selected by the backend.
     */
    const extraRotation = 1440 + Math.floor(Math.random()*720);
    setRotation(v=>v + extraRotation);

    try{
      const r = await api.playRewardGame(game.play_id);

      /*
       * Give the wheel time to finish its animation even if
       * the API responds very quickly.
       */
      setTimeout(()=>{
        setResult(r);
        setSpinning(false);
        setShowReward(true);

        const label = r?.reward_label
          ?? r?.reward
          ?? (r?.awarded_xp != null
            ? `+${Number(r.awarded_xp).toLocaleString()} XP`
            : "Reward unlocked");

        pushToast(`Reward unlocked: ${label}`);
      },1800);

    }catch(e:any){
      setSpinning(false);
      pushToast(e.message,"warning");
    }
  };

  return <Modal title={game?.name ?? "Spin the Wheel"} onClose={onClose}>
    <div className="wheel-wrap">

      <div className="wheel-pointer">▼</div>

      <div
        className={`wheel ${spinning ? "wheel-spinning" : ""}`}
        style={{
          transform:`rotate(${rotation}deg)`,
          transition:spinning
            ? "transform 1.8s cubic-bezier(.12,.72,.18,1)"
            : "none"
        }}
      >
        <div
          className="wheel-segments"
          style={{
            "--wheel-count": segments.length,
            background: `conic-gradient(from -90deg, ${
              segments.map((_: any, i: number) => {
                const colours = [
                  "#7c3aed",
                  "#06b6d4",
                  "#f59e0b",
                  "#22c55e",
                  "#a3ff12",
                  "#ec4899",
                  "#3b82f6",
                  "#14b8a6",
                ];
                const angle = 360 / segments.length;
                const start = i * angle;
                const end = (i + 1) * angle;
                return `${colours[i % colours.length]} ${start}deg ${end}deg`;
              }).join(", ")
            })`
          } as React.CSSProperties}
        >
          {segments.map((segment:any,i:number)=>{
            const slice = 360 / segments.length;
            const midpoint = i * slice + slice / 2;
            const label = segmentLabel(segment);

            /*
             * Put the label in the middle of its own wedge.
             * The label itself follows the radial direction of
             * the wedge, so long rewards use the available depth
             * instead of spilling sideways into another wedge.
             */
            const radius = segments.length <= 4 ? 31 : 34;
            const x = 50 + radius * Math.sin(midpoint * Math.PI / 180);
            const y = 50 - radius * Math.cos(midpoint * Math.PI / 180);

            return (
              <div
                className="wheel-reward-label"
                key={i}
                title={label}
                style={{
                  left: `${x}%`,
                  top: `${y}%`,
                  transform: `translate(-50%, -50%) rotate(${midpoint}deg)`,
                } as React.CSSProperties}
              >
                <span>{label}</span>
              </div>
            );
          })}
        </div>

        <div className="wheel-core">
          {spinning
            ? "…"
            : result
              ? "✓"
              : "SPIN"}
        </div>
      </div>

      {game ? (
        <>
          <h3 className="wheel-title">{game.name}</h3>

          {game.description && (
            <p className="modal-note">{game.description}</p>
          )}

          <p className="modal-note">
            {segments.length} configured rewards
            {" · "}
            Entitlement #{game.play_id}
          </p>
        </>
      ) : (
        <p className="modal-note">
          No reward-game entitlement is currently available for this account.
        </p>
      )}

      <button
        className="primary-btn wide"
        disabled={!game || spinning}
        onClick={spin}
      >
        {spinning
          ? "Spinning…"
          : result
            ? "Spin again"
            : "Spin the Wheel"}
      </button>

      {showReward && result && (
        <div
          className="reward-flash"
          role="dialog"
          aria-modal="true"
          aria-label="Reward unlocked"
        >
          <div className="reward-flash-card">

            <div className="reward-flash-burst">✦</div>

            <div className="reward-flash-kicker">
              REWARD UNLOCKED
            </div>

            <div className="reward-flash-title">
              {resultLabel}
            </div>

            <div className="reward-flash-subtitle">
              Congratulations!
            </div>

            <button
              className="primary-btn wide reward-flash-button"
              onClick={()=>{
                setShowReward(false);
              }}
            >
              Continue
            </button>

          </div>
        </div>
      )}

    </div>
  </Modal>
}


function PointRequests({data,openPointRequests,pushToast,refresh}:{data:any;openPointRequests:()=>void;pushToast:(s:string,t?:any)=>void;refresh:()=>Promise<void>}){const rows=data?.pointRequests??[];return <div className="page"><div className="section-heading"><div><span className="eyebrow">STAFF REVIEW QUEUE</span><h2>Points requests</h2></div><button className="primary-btn" onClick={openPointRequests}><Check size={16}/> Review requests</button></div><div className="panel"><div className="panel-head"><h3>{rows.length} pending request{rows.length===1?"":"s"}</h3><span className="status at-risk">Approval required</span></div>{rows.length===0?<p className="muted">No points requests are waiting for review.</p>:rows.map((r:any)=><div className="setting-line" key={r.id}><div><b>{r.gamertag}</b><small style={{display:"block",color:"#70808e"}}>+{r.requested_xp.toLocaleString()} XP · {r.reason}</small></div><button className="secondary-btn" onClick={openPointRequests}>Review</button></div>)}</div></div>}
function PointRequestsModal({onClose,pushToast,refresh}:{onClose:()=>void;pushToast:(s:string,t?:any)=>void;refresh:()=>Promise<void>}){const [rows,setRows]=useState<any[]>([]);const [busy,setBusy]=useState<number|null>(null);const load=async()=>{try{setRows(await api.pointRequests("pending"))}catch(e:any){pushToast(e.message,"warning")}};useEffect(()=>{load()},[]);const decide=async(r:any,approved:boolean)=>{let amount=r.requested_xp;let note="";if(approved){const x=window.prompt(`Approve XP for ${r.gamertag}`,String(r.requested_xp));if(x===null)return;amount=Number(x);if(!Number.isFinite(amount)||amount<1||amount>5000){pushToast("XP must be between 1 and 5,000","warning");return};note=window.prompt("Optional review note","")||""}else note=window.prompt("Reason for rejection","")||"Request declined by youth worker.";setBusy(r.id);try{if(approved)await api.approvePointRequest(r.id,{approved_xp:amount,review_note:note||null});else await api.rejectPointRequest(r.id,{review_note:note});pushToast(approved?`+${amount.toLocaleString()} XP approved`:`Request #${r.id} rejected`);await load();await refresh()}catch(e:any){pushToast(e.message,"warning")}finally{setBusy(null)}};return <Modal title="Points requests" onClose={onClose}><div className="panel inset"><div className="panel-head"><h3>Pending review</h3><button className="ghost-btn" onClick={load}><RotateIcon/></button></div>{rows.length===0?<p className="muted">Nothing waiting for review.</p>:rows.map(r=><div className="request-card" key={r.id}><div className="request-card-head"><div><b>{r.gamertag}</b><small>Request #{r.id} · {r.created_at?new Date(r.created_at).toLocaleString():""}</small></div><strong>+{r.requested_xp.toLocaleString()} XP</strong></div><p>{r.reason}</p><div className="nom-actions"><button className="primary-btn" disabled={busy===r.id} onClick={()=>decide(r,true)}><Check size={15}/> Approve</button><button className="ghost-btn" disabled={busy===r.id} onClick={()=>decide(r,false)}>Reject</button></div></div>)}</div></Modal>}
function PlayerQrModal({onClose,pushToast}:{onClose:()=>void;pushToast:(s:string,t?:any)=>void}){const [token,setToken]=useState("");const [busy,setBusy]=useState(true);const load=async()=>{setBusy(true);try{const r=await api.rotatePlayerQr();setToken(r.token)}catch(e:any){pushToast(e.message,"warning")}finally{setBusy(false)}};useEffect(()=>{load()},[]);const value=token?`${window.location.origin}/request-points?token=${encodeURIComponent(token)}`:"";return <Modal title="My Quest QR" onClose={onClose}><div className="qr-modal">{busy?<div className="loader-ring"/>:token?<><div className="qr-frame"><QRCodeCanvas value={value} size={230} includeMargin/></div><h3>Show this code</h3><p className="muted">The code does not reveal the player's name. Scanning opens the extra-XP request form.</p><button className="ghost-btn wide" onClick={load}>Rotate QR</button></>:<p className="muted">Unable to generate your QR.</p>}</div></Modal>}
function PointRequestPage({token}:{token:string}){const [amount,setAmount]=useState(250);const [reason,setReason]=useState("");const [busy,setBusy]=useState(false);const [done,setDone]=useState(false);const [error,setError]=useState("");const submit=async()=>{setBusy(true);setError("");try{await api.createPointRequest({token,requested_xp:Number(amount),reason});setDone(true)}catch(e:any){setError(e.message)}finally{setBusy(false)}};if(done)return <div className="center-screen"><div className="login-card"><div className="brand centered"><div className="brand-mark">Q</div><div><strong>QUEST<span>HUB</span></strong><small>CUMBERNAULD CLIMB</small></div></div><span className="eyebrow">REQUEST SUBMITTED</span><h1>XP request sent.</h1><p>Your request is waiting for a youth worker to review. No XP has been awarded yet.</p></div></div>;return <div className="center-screen"><div className="login-card"><div className="brand centered"><div className="brand-mark">Q</div><div><strong>QUEST<span>HUB</span></strong><small>CUMBERNAULD CLIMB</small></div></div><span className="eyebrow">QUEST POINTS</span><h1>Request extra XP.</h1><p>Explain what was achieved. A youth worker must approve the request before XP is added.</p>{error&&<div className="api-error">{error}</div>}<label>XP requested<input type="number" min="1" max="5000" value={amount} onChange={e=>setAmount(Number(e.target.value))}/></label><label>Reason<textarea value={reason} onChange={e=>setReason(e.target.value)} placeholder="What was achieved or contributed?"/></label><button className="primary-btn wide" disabled={busy||reason.trim().length<3} onClick={submit}>{busy?"Submitting…":"Submit request"}</button></div></div>}

function AwardModal({players,selected,setSelected,onClose,pushToast}:{players:any[];selected:any;setSelected:(p:any)=>void;onClose:()=>void;pushToast:(s:string,t?:any)=>void}){const[pick,setPick]=useState(selected?.id??players[0]?.id??"");const[amount,setAmount]=useState(500);const[reason,setReason]=useState("Positive participation");return <Modal title="Award Points" onClose={onClose}><div className="form-grid"><label>Player<select value={pick} onChange={e=>{setPick(Number(e.target.value));setSelected(players.find(p=>p.id===Number(e.target.value)))}}>{players.map(p=><option key={p.id} value={p.id}>{p.gamertag}</option>)}</select></label><label>Amount<input type="number" value={amount} onChange={e=>setAmount(Number(e.target.value))}/></label><label>Reason<textarea value={reason} onChange={e=>setReason(e.target.value)}/></label></div><button className="primary-btn wide" onClick={async()=>{try{await api.awardXp(Number(pick),amount,reason);pushToast(`+${amount.toLocaleString()} XP awarded`);onClose()}catch(e:any){pushToast(e.message,"warning")}}}><Plus size={17}/> Award XP</button></Modal>}


function UserManagerModal({users,onClose,refresh,pushToast}:{users:any[];onClose:()=>void;refresh:()=>Promise<void>;pushToast:(s:string,t?:any)=>void}){const [editing,setEditing]=useState<any>(null);const [form,setForm]=useState<any>({username:"",password:"",role:"player",display_name:"",gamertag:"",avatar:"avatar-01",group_id:"",public_visible:true});const [busy,setBusy]=useState(false);const set=(k:string,v:any)=>setForm((x:any)=>({...x,[k]:v}));const open=(u:any)=>{setEditing(u);setForm({username:u.username,password:"",role:u.role,display_name:u.display_name??"",gamertag:u.player?.gamertag??"",avatar:u.player?.avatar??"avatar-01",group_id:u.player?.group_id??"",public_visible:u.player?.public_visible??true})};const create=()=>{setEditing(null);setForm({username:"",password:"",role:"player",display_name:"",gamertag:"",avatar:"avatar-01",group_id:"",public_visible:true})};const save=async()=>{setBusy(true);try{const body:any={username:form.username,role:form.role,display_name:form.display_name||null};if(form.password)body.password=form.password;if(form.role==="player"){body.gamertag=form.gamertag;body.avatar=form.avatar;body.public_visible=!!form.public_visible;if(form.group_id!=="")body.group_id=Number(form.group_id)}if(editing)await api.updateUser(editing.id,body);else await api.createUser({...body,password:form.password,active:true});pushToast(editing?"Account updated":"User created");await refresh();if(!editing)create()}catch(e:any){pushToast(e.message,"warning")}finally{setBusy(false)}};const action=async(u:any,kind:string)=>{try{if(kind==="pause")await api.pauseUser(u.id);if(kind==="reactivate")await api.reactivateUser(u.id);if(kind==="suspend"&&u.player)await api.suspendPlayer(u.player.id);if(kind==="unsuspend"&&u.player)await api.unsuspendPlayer(u.player.id);pushToast(kind+" complete");await refresh()}catch(e:any){pushToast(e.message,"warning")}};return <Modal title="Manage accounts" onClose={onClose}><div className="user-manager"><div className="section-heading"><span className="eyebrow">ADMIN ONLY</span><button className="primary-btn" onClick={create}><Plus size={15}/> New user</button></div><div className="form-grid"><label>Username<input value={form.username} onChange={e=>set("username",e.target.value)} /></label><label>Role<select value={form.role} onChange={e=>set("role",e.target.value)}><option value="player">Young person</option><option value="youth_worker">Youth worker</option><option value="admin">Admin</option></select></label><label>Password {editing&&<small>(leave blank to keep current)</small>}<input type="password" value={form.password} onChange={e=>set("password",e.target.value)} placeholder="Minimum 10 characters" /></label>{form.role==="player"&&<><label>Gamertag<input value={form.gamertag} onChange={e=>set("gamertag",e.target.value)} /></label><label>Group ID<input type="number" value={form.group_id} onChange={e=>set("group_id",e.target.value)} placeholder="Optional" /></label><label>Avatar<input value={form.avatar} onChange={e=>set("avatar",e.target.value)} /></label></>}</div><button className="primary-btn wide" disabled={busy||!form.username||(!editing&&!form.password)} onClick={save}>{busy?"Saving…":editing?"Save changes":"Create user"}</button><div className="panel inset"><div className="panel-head"><h3>Accounts</h3><span className="count-pill">{users.length}</span></div>{users.map((u:any)=><div className="setting-line" key={u.id}><div><b>{u.username}</b><small style={{display:"block",color:"#70808e"}}>{u.role} · {u.player?.gamertag??u.display_name??"Staff account"}</small></div><div className="nom-actions"><span className={`status ${u.active?"":"inactive"}`}>{u.active?"Active":"Paused"}</span><button className="ghost-btn" onClick={()=>open(u)}>Edit</button>{u.active?<button className="ghost-btn" onClick={()=>action(u,"pause")}>Pause</button>:<button className="ghost-btn" onClick={()=>action(u,"reactivate")}>Reactivate</button>}{u.player&&(u.player.suspended?<button className="ghost-btn" onClick={()=>action(u,"unsuspend")}>Unsuspend</button>:<button className="ghost-btn" onClick={()=>action(u,"suspend")}>Suspend</button>)}</div></div>)}</div></div></Modal>}
function EconomyModal({onClose,pushToast}:{onClose:()=>void;pushToast:(s:string,t?:any)=>void}){const [v,setV]=useState<any>(null);const [busy,setBusy]=useState(false);useEffect(()=>{api.economy().then(setV).catch(e=>pushToast(e.message,"warning"))},[]);if(!v)return <Modal title="Economy settings" onClose={onClose}><p className="muted">Loading…</p></Modal>;const set=(k:string,x:any)=>setV((a:any)=>({...a,[k]:x}));const save=async()=>{setBusy(true);try{await api.updateEconomy({jackpot_target_xp:Number(v.jackpot_target_xp),max_group_penalty_percent:Number(v.max_group_penalty_percent),max_staff_multiplier:Number(v.max_staff_multiplier),weekly_growth_cap_multiplier:Number(v.weekly_growth_cap_multiplier),group_penalties_enabled:!!v.group_penalties_enabled,multipliers_enabled:!!v.multipliers_enabled});pushToast("Economy saved");onClose()}catch(e:any){pushToast(e.message,"warning")}finally{setBusy(false)}};return <Modal title="Economy settings" onClose={onClose}><div className="form-grid"><label>Jackpot target XP<input type="number" value={v.jackpot_target_xp} onChange={e=>set("jackpot_target_xp",e.target.value)}/></label><label>Max group penalty %<input type="number" value={v.max_group_penalty_percent} onChange={e=>set("max_group_penalty_percent",e.target.value)}/></label><label>Max staff multiplier<input type="number" step="0.1" value={v.max_staff_multiplier} onChange={e=>set("max_staff_multiplier",e.target.value)}/></label><label>Weekly growth cap multiplier<input type="number" step="0.1" value={v.weekly_growth_cap_multiplier} onChange={e=>set("weekly_growth_cap_multiplier",e.target.value)}/></label><label>Group penalties<select value={String(!!v.group_penalties_enabled)} onChange={e=>set("group_penalties_enabled",e.target.value==="true")}><option value="true">Enabled</option><option value="false">Disabled</option></select></label><label>Multipliers<select value={String(!!v.multipliers_enabled)} onChange={e=>set("multipliers_enabled",e.target.value==="true")}><option value="true">Enabled</option><option value="false">Disabled</option></select></label></div><button className="primary-btn wide" disabled={busy} onClick={save}>{busy?"Saving…":"Save economy"}</button></Modal>}
function RewardManagerModal({onClose,pushToast}:{onClose:()=>void;pushToast:(s:string,t?:any)=>void}){const [games,setGames]=useState<any[]>([]);const [targets,setTargets]=useState<any>({players:[],groups:[]});const [form,setForm]=useState<any>({name:"Spin the Wheel",description:"",game_type:"wheel",prize_values:"500,1000,2000",starts_at:"",ends_at:"",active:true,show_upcoming:true});const [target,setTarget]=useState("player");const [targetId,setTargetId]=useState("");const load=async()=>{try{const [g,t]=await Promise.all([api.adminRewardGames(),api.rewardGameTargets()]);setGames(g);setTargets(t)}catch(e:any){pushToast(e.message,"warning")}};useEffect(()=>{load()},[]);const set=(k:string,x:any)=>setForm((a:any)=>({...a,[k]:x}));const create=async()=>{try{await api.createRewardGame({...form,prize_values:form.prize_values.split(",").map((x:string)=>Number(x.trim())).filter((x:number)=>Number.isFinite(x)),starts_at:form.starts_at||null,ends_at:form.ends_at||null});pushToast("Reward game created");await load()}catch(e:any){pushToast(e.message,"warning")}};const grant=async(game:any)=>{if(!targetId)return;try{await api.grantRewardGame(game.id,target==="player"?{player_id:Number(targetId)}:{group_id:Number(targetId)});pushToast("Reward entitlement granted")}catch(e:any){pushToast(e.message,"warning")}};const toggle=async(g:any)=>{try{await api.updateRewardGame(g.id,{active:!g.active});pushToast(g.active?"Reward game paused":"Reward game activated");await load()}catch(e:any){pushToast(e.message,"warning")}};return <Modal title="Reward games" onClose={onClose}><div className="form-grid"><label>Name<input value={form.name} onChange={e=>set("name",e.target.value)}/></label><label>Description<textarea value={form.description} onChange={e=>set("description",e.target.value)}/></label><label>Prize values (XP, comma separated)<input value={form.prize_values} onChange={e=>set("prize_values",e.target.value)} placeholder="500,1000,2000"/></label><label>Starts at<input type="datetime-local" value={form.starts_at} onChange={e=>set("starts_at",e.target.value)}/></label><label>Ends at<input type="datetime-local" value={form.ends_at} onChange={e=>set("ends_at",e.target.value)}/></label></div><button className="primary-btn wide" onClick={create}><Plus size={15}/> Create reward game</button><div className="panel inset" style={{marginTop:12}}><div className="panel-head"><h3>Grant entitlement</h3></div><div className="form-grid"><label>Target<select value={target} onChange={e=>{setTarget(e.target.value);setTargetId("")}}><option value="player">Player</option><option value="group">Group</option></select></label><label>{target==="player"?"Player":"Group"}<select value={targetId} onChange={e=>setTargetId(e.target.value)}><option value="">Select…</option>{target==="player"?targets.players.map((p:any)=><option key={p.id} value={p.id}>{p.gamertag}</option>):targets.groups.map((g:any)=><option key={g.id} value={g.id}>{g.name}</option>)}</select></label></div>{games.map(g=><div className="setting-line" key={g.id}><span><b>{g.name}</b><small style={{display:"block",color:"#70808e"}}>{g.active?"Active":"Paused"} · {g.available_entitlements} available · prizes hidden from players</small></span><div className="nom-actions"><button className="ghost-btn" onClick={()=>toggle(g)}>{g.active?"Pause":"Activate"}</button><button className="secondary-btn" disabled={!targetId||!g.active} onClick={()=>grant(g)}>Grant</button></div></div>)}</div></Modal>}
function EconomyPanel({openEconomy}:{openEconomy:()=>void}){return <div className="page"><div className="section-heading"><div><span className="eyebrow">SYSTEM SETTINGS</span><h2>Programme economy</h2></div><button className="primary-btn" onClick={openEconomy}><Settings size={16}/> Configure</button></div><div className="panel"><p className="muted">Admin-controlled jackpot target, penalty ceiling, staff multiplier, growth cap and economy toggles.</p></div></div>}
function Modal({title,onClose,children}:{title:string;onClose:()=>void;children:any}){return <div className="modal-backdrop" onMouseDown={onClose}><div className="modal" onMouseDown={e=>e.stopPropagation()}><div className="modal-head"><h2>{title}</h2><button className="icon-btn" onClick={onClose}><X/></button></div>{children}</div></div>}
function Stat({icon,label,value,delta}:{icon?:any;label:string;value:string;delta:string}){return <div className="stat"><div className="stat-icon">{icon}</div><div><span>{label}</span><strong>{value}</strong><small>{delta}</small></div></div>}
function RotateIcon(){return <span style={{fontSize:18}}>↻</span>}
