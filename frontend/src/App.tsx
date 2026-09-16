import { useEffect, useMemo, useState } from "react";
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from "react-router-dom";
import { QRCodeCanvas } from "qrcode.react";
import { Activity, AlertTriangle, ArrowUpRight, Award, BarChart3, Bell, Check, ChevronRight, CircleHelp, Gauge, LayoutDashboard, LogOut, Map, Menu, MoreHorizontal, Plus, Search, Settings, ShieldCheck, Sparkles, Trophy, Users as LucideUsers, WalletCards, X, Zap } from "lucide-react";
import { api, type Role, type SessionUser } from "./api";
import Stat from "./components/Stat";
import Login from "./components/Login";
import Modal from "./components/Modal";
import RotateIcon from "./components/RotateIcon";
import PointRequests from "./components/PointRequests";
import PublicView from "./components/PublicView";
import PlayerView from "./components/PlayerView";
import WheelModal from "./components/WheelModal";
import DrawShapeModal from "./components/DrawShapeModal";
import Players from "./components/Players";
import Points from "./components/Points";
import Challenges from "./components/Challenges";
import Groups from "./components/Groups";
import Overview from "./components/Overview";

const demoPlayers = [
  {id:1,gamertag:"PixelRanger",xp:24530,status:"Active",badge:"Silver",color:"lime"},
  {id:2,gamertag:"NovaSquad",xp:18740,status:"Active",badge:"Bronze",color:"purple"},
  {id:3,gamertag:"StormCrew",xp:15640,status:"Active",badge:"Bronze",color:"cyan"},
  {id:4,gamertag:"UrbanLegends",xp:12450,status:"At risk",badge:"Iron",color:"yellow"},
];

type Toast = {id:number;text:string;tone?:"success"|"info"|"warning"};

export default function App() {
  const [user, setUser] = useState<SessionUser|null>(null);
  const [checking, setChecking] = useState(true);
  const [error, setError] = useState("");
  const [data, setData] = useState<any>(null);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [wheelOpen, setWheelOpen] = useState(false);
  const [awardOpen, setAwardOpen] = useState(false);
  const [drawShapeOpen, setDrawShapeOpen] = useState(false);
  const [selectedDrawShapeAssignment, setSelectedDrawShapeAssignment] = useState<any>(null);
  const [selectedPlayer, setSelectedPlayer] = useState<any>(null);
  const [userManagerOpen, setUserManagerOpen] = useState(false);
  const [economyOpen, setEconomyOpen] = useState(false);
  const [rewardManagerOpen, setRewardManagerOpen] = useState(false);
  const [drawingGameManagerOpen, setDrawingGameManagerOpen] = useState(false);
  const [playerQrOpen, setPlayerQrOpen] = useState(false);
  const [pointRequestsOpen, setPointRequestsOpen] = useState(false);
  // State for sidebar visibility in public mode
  const [publicSidebarOpen, setPublicSidebarOpen] = useState(true);
  // State for mobile sidebar
  const [mobileNav, setMobileNav] = useState(false);
  // State for current section in the dashboard
  const [section, setSection] = useState("Overview");

  const location = useLocation();
  const navigate = useNavigate();

  // Fetch user session on mount
  useEffect(() => {
    api.me().then(u => {
      setUser(u);
    }).catch(() => {
      // If me fails, we assume not logged in
      setUser(null);
    }).finally(() => {
      setChecking(false);
    });
  }, []);

  // Fetch data based on route and user
  const refresh = async () => {
    try {
      const pathname = location.pathname;
      if (pathname === "/public") {
        const [dashboard, leaderboards] = await Promise.all([
          api.publicDashboard(),
          api.leaderboards(),
        ]);

        setData({
          ...dashboard,
          leaderboards,
        });

        return;
      }

      if (!user) {
        // If we are not on /public and not logged in, we should be redirected to login by the route.
        // So we don't need to fetch data here.
        return;
      }

      if (user?.role === "player") {
        const [dashboard, games, drawingGames] = await Promise.all([
          api.playerDashboard(),
          api.rewardGames(),
          api.playerDrawingGames()
        ]);

        setData({
          ...dashboard,
          games,
          drawing_games: drawingGames,
        });

        return;
      }

      if (user?.role === "admin" || user?.role === "youth_worker") {
        setData({
          overview: await api.adminOverview(),
          players: await api.adminPlayers(),
          leaderboard: await api.leaderboards(),
          users:
            user?.role === "admin"
              ? await api.adminUsers()
              : undefined,
          pointRequests:
            await api.pointRequests("pending"),
        });

        return;
      }
    } catch (e: any) {
      setError(e.message);
    }
  };

  // Call refresh when checking becomes false, or when user changes, or when the route changes.
  useEffect(() => {
    if (!checking) {
      refresh();
    }
  }, [checking, user, location.pathname]);

  // Event listener for sidebar toggle from PublicView
  useEffect(() => {
    const handleSidebarToggle = (e: Event) => {
      const customEvent = e as CustomEvent<{open: boolean}>;
      // We only care about this event when we are in public mode, i.e., when the pathname is /public
      if (location.pathname === "/public" && customEvent.detail && customEvent.detail.open !== undefined) {
        setPublicSidebarOpen(customEvent.detail.open);
      }
    };

    window.addEventListener('toggle-public-sidebar', handleSidebarToggle);
    return () => {
      window.removeEventListener('toggle-public-sidebar', handleSidebarToggle);
    };
  }, [location.pathname]);

  // We'll keep the nav memo, but we will base it on the current route and user.
  // However, note that the nav is used in the sidebar, which is only shown in the dashboard route.
  // We will compute the nav items based on the user role, but we will only use it when we are in the dashboard route.
  const nav = useMemo(() => {
    // If we are in the public route, we don't use this nav.
    if (location.pathname === "/public") {
      return ["Home", "Leaderboard", "Map", "Milestones"];
    }
    // If we are in the dashboard route, we base it on the user role.
    if (!user) {
      // This shouldn't happen because the dashboard route redirects to login if not authenticated.
      return [];
    }
    if (user?.role === "player") {
      return ["Home", "Challenges", "Rewards", "Profile"];
    }
    if (user?.role === "admin") {
      return [
        "Dashboard",
        "Users & Groups",
        "Points & Rewards",
        "Drawing Games",
        "Points Requests",
        "Challenges",
        "Phases & Themes",
        "Community Nominations",
        "Analytics",
        "System Settings"
      ];
    }
    // For youth_worker, we can use the same as admin? Or a subset? We'll use admin for now.
    return [
      "Dashboard",
      "Users & Groups",
      "Points & Rewards",
      "Drawing Games",
      "Points Requests",
      "Challenges",
      "Phases & Themes",
      "Community Nominations",
      "Analytics",
      "System Settings"
    ];
  }, [location.pathname, user]);

  const logout = async () => {
    try {
        // Call backend logout API
        await api.logout();
    } catch (err) {
        console.warn("Logout API call failed:", err);
        // Continue with client-side cleanup even if API fails
    }

    // Clear all frontend state related to user session and data
    setUser(null);
    setData(null);
    setToasts([]);
    setError("");
    setChecking(false);

    // Reset UI state to defaults
    setWheelOpen(false);
    setAwardOpen(false);
    setDrawShapeOpen(false);
    setSelectedDrawShapeAssignment(null);
    setSelectedPlayer(null);
    setUserManagerOpen(false);
    setEconomyOpen(false);
    setRewardManagerOpen(false);
    setDrawingGameManagerOpen(false);
    setPlayerQrOpen(false);
    setPointRequestsOpen(false);
    setPublicSidebarOpen(true); // Default to sidebar open in public view
    setMobileNav(false);
    setSection("Overview");

    // Clear any potential frontend storage as backup
    // Note: Session uses HttpOnly cookie per login component note,
    // but we clear other storage just in case
    try {
        localStorage.removeItem('questhub-user');
        sessionStorage.removeItem('questhub-user');
    } catch (e) {
        // Ignore storage access errors
    }

    // Clear cookies (best effort for non-HttpOnly cookies)
    try {
        document.cookie.split(";").forEach(cookie => {
            const eqPos = cookie.indexOf("=");
            const name = eqPos > -1 ? cookie.substring(0, eqPos) : cookie;
            document.cookie = name.trim() + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/";
        });
    } catch (e) {
        // Ignore cookie clearing errors
    }

    pushToast("Signed out", "info");

    // Navigate to login page with replace to prevent back navigation to protected routes
    navigate("/login", { replace: true });

    // Force a reload after navigation to ensure clean state
    // This helps clear any potential stale state that might persist
    setTimeout(() => {
        window.location.reload();
    }, 100);
};

  const pushToast = (text:string, tone:Toast["tone"]="success") => {
    const id = Date.now();
    setToasts(v=>[...v,{id,text,tone}]);
    setTimeout(()=>setToasts(v=>v.filter(t=>t.id!==id)),3000);
  };

  const requestToken = new URLSearchParams(window.location.search).get("token");
  const requestMode = window.location.pathname === "/request-points" && !!requestToken;
  if (requestMode) {
    return (
      <div className="center-screen">
        <div className="login-card">
          <div className="brand centered">
            <div className="brand-mark">Q</div>
            <div>
              <strong>QUEST<span>HUB</span></strong>
              <small>CUMBERNAULD CLIMB</small>
            </div>
          </div>
        </div>
        <span className="eyebrow">REQUEST SUBMITTED</span>
        <h1>XP request sent.</h1>
        <p>Your request is waiting for a youth worker to review. No XP has been awarded yet.</p>
      </div>
    );
  }

  if (checking) {
    return (
      <div className="center-screen">
        <div className="loader-ring" />
        <p>Connecting to QuestHub…</p>
      </div>
    );
  }

  // Helper to check if user is staff
  const isStaff = (user: SessionUser | null) => {
    return user?.role === "admin" || user?.role === "youth_worker";
  };

  // We will now render based on the route.
  return (
    <>
      {/* We keep the modals outside the Routes so they are shown on top of everything */}
      {wheelOpen && <WheelModal data={data?.games} onClose={() => setWheelOpen(false)} pushToast={pushToast} />}
      {drawShapeOpen && <DrawShapeModal assignment={selectedDrawShapeAssignment} onClose={() => { setDrawShapeOpen(false); setSelectedDrawShapeAssignment(null); }} pushToast={pushToast} />}
      {userManagerOpen && <UserManagerModal users={data?.users ?? []} onClose={() => setUserManagerOpen(false)} refresh={refresh} pushToast={pushToast} />}
      {economyOpen && <EconomyModal onClose={() => setEconomyOpen(false)} pushToast={pushToast} />}
      {rewardManagerOpen && <RewardManagerModal onClose={() => setRewardManagerOpen(false)} pushToast={pushToast} />}
      {drawingGameManagerOpen && <DrawingGameManagerModal onClose={() => setDrawingGameManagerOpen(false)} />}
      {playerQrOpen && <PlayerQrModal onClose={() => setPlayerQrOpen(false)} pushToast={pushToast} />}
      {pointRequestsOpen && <PointRequestsModal onClose={() => setPointRequestsOpen(false)} pushToast={pushToast} refresh={refresh} />}
      {awardOpen && <AwardModal players={data?.players ?? []} selected={selectedPlayer} setSelected={setSelectedPlayer} onClose={() => setAwardOpen(false)} pushToast={pushToast} />}

      <Routes>
        {/* Public dashboard route - accessible without login */}
        <Route path="/public" element={
          <div className="app-shell">
            {/* Sidebar - conditionally hide in public mode based on publicSidebarOpen state */}
            {!publicSidebarOpen ? null : (
              <aside className={`sidebar ${mobileNav ? "open" : ""}`}>
                <div className="brand"><div className="brand-mark">Q</div><div><strong>QUEST<span>HUB</span></strong><small>CUMBERNAULD CLIMB</small></div></div>
                <div className="role-switch"><span>CONNECTED AS</span><div className="identity-chip">PUBLIC VIEW</div><div className="role-actions">
                  <button className={location.pathname === "/public" ? "active" : ""} onClick={() => { navigate("/public", { replace: true }); setSection("Home"); }}>
                    Public
                  </button>
                  {user && isStaff(user) && (
                    <button className={location.pathname === "/dashboard" ? "active" : ""} onClick={() => {
                      navigate("/dashboard", { replace: true });
                      setSection(user?.role === "admin" ? "Dashboard" : "Overview");
                    }}>
                      My dashboard
                    </button>
                  )}
                </div></div>
                <nav>{nav.map((item, i) => {
                  let icon;
                  switch (i) {
                    case 0: icon = <LayoutDashboard size={17} />; break;
                    case 1: icon = <LucideUsers size={17} />; break;
                    case 2: icon = <WalletCards size={17} />; break;
                    case 3: icon = <Zap size={17} />; break;
                    case 4: icon = <Map size={17} />; break;
                    case 5: icon = <Award size={17} />; break;
                    case 6: icon = <ShieldCheck size={17} />; break;
                    default: icon = <BarChart3 size={17} />;
                  }
                  return (
                    <button key={item} className={section === item ? "nav-item active" : "nav-item"} onClick={() => { setSection(item); setMobileNav(false); }}>
                      {icon}
                      {item}
                    </button>
                  );
                })}
                </nav>
                <div className="sidebar-bottom">
                  <div className="system-chip"><span className="pulse-dot"/> API connected</div>
                  {isStaff(user) && (<button className="nav-item" onClick={() => { setDrawingGameManagerOpen(true); }}>Drawing Games</button>)}
                  {user && <button className="nav-item" onClick={logout}><LogOut size={17}/> Sign out</button>}
                  <button className="nav-item"><CircleHelp size={17}/> Help & support</button>
                </div>
              </aside>
            )}

            <main className="main">
              <header className="topbar">
                <button className="mobile-menu" onClick={() => setMobileNav(!mobileNav)}>
                  <Menu/>
                </button>
                <div>
                  <div className="eyebrow">QUESTHUB / PUBLIC</div>
                  <h1>Public Dashboard</h1>
                  <p>Collective progress, anonymised rankings and phase activity.</p>
                </div>
                <div className="top-actions">
                  <button className="icon-btn" onClick={refresh}><RotateIcon/></button>
                  <button className="icon-btn" onClick={() => pushToast("Notifications endpoint can be connected here", "info")}><Bell size={18}/></button>
                  {user && <div className="staff-avatar">{user.username.slice(0,2).toUpperCase()}</div>}
                </div>
              </header>
              {error && <div className="api-error"><AlertTriangle size={16}/><span>{error}</span><button onClick={() => setError("")}><X size={14}/></button></div>}
              {data ? <PublicView data={data} /> : <div className="center-screen"><p>Loading public dashboard...</p></div>}
            </main>
          </div>
        } />

        {/* Login route */}
        <Route path="/login" element={
          <Login
            onLogin={async (username: string, password: string) => {
              setError("");
              try {
                const x = await api.login(username, password);
                setUser(x);
                pushToast(`Signed in as ${x.role.replace("_", " ")}`);
                // After login, go to dashboard
                navigate("/dashboard", { replace: true });
              } catch (e: any) {
                setError(e.message);
              }
            }}
            onPublic={() => {
              navigate("/public", { replace: true });
            }}
            error={error}
          />
        } />

        {/* Dashboard route - requires login */}
        <Route path="/dashboard" element={
          !user ? (
            <Navigate to="/login" replace={true} />
          ) : (
            <div className="app-shell">
              {/* Sidebar - we keep the same sidebar logic as before */}
              <aside className={`sidebar ${mobileNav ? "open" : ""}`}>
                <div className="brand"><div className="brand-mark">Q</div><div><strong>QUEST<span>HUB</span></strong><small>CUMBERNAULD CLIMB</small></div></div>
                <div className="role-switch"><span>CONNECTED AS</span><div className="identity-chip">{user?.username ?? "GUEST"}</div><div className="role-actions">
                  {/* Public button - navigate to public dashboard */}
                  <button className={location.pathname === "/public" ? "active" : ""} onClick={() => { navigate("/public", { replace: true }); setSection("Home"); }}>
                    Public
                  </button>
                  {/* My dashboard button - toggle between public and dashboard? We are already in dashboard. */}
                  {isStaff(user) && (
                    <button className={location.pathname === "/dashboard" ? "active" : ""} onClick={() => {
                      /* We are in dashboard, so we just set the section to the default for the role */
                      navigate("/dashboard", { replace: true });
                      setSection(user?.role === "admin" ? "Dashboard" : "Overview");
                    }}>
                      My dashboard
                    </button>
                  )}
                </div></div>
                <nav>{nav.map((item, i) => {
                  let icon;
                  switch (i) {
                    case 0: icon = <LayoutDashboard size={17} />; break;
                    case 1: icon = <LucideUsers size={17} />; break;
                    case 2: icon = <WalletCards size={17} />; break;
                    case 3: icon = <Zap size={17} />; break;
                    case 4: icon = <Map size={17} />; break;
                    case 5: icon = <Award size={17} />; break;
                    case 6: icon = <ShieldCheck size={17} />; break;
                    default: icon = <BarChart3 size={17} />;
                  }
                  return (
                    <button key={item} className={section === item ? "nav-item active" : "nav-item"} onClick={() => { setSection(item); setMobileNav(false); }}>
                      {icon}
                      {item}
                    </button>
                  );
                })}
                </nav>
                <div className="sidebar-bottom">
                  <div className="system-chip"><span className="pulse-dot"/> API connected</div>
                  {isStaff(user) && (<button className="nav-item" onClick={() => { setDrawingGameManagerOpen(true); }}>Drawing Games</button>)}
                  {user && <button className="nav-item" onClick={logout}><LogOut size={17}/> Sign out</button>}
                  <button className="nav-item"><CircleHelp size={17}/> Help & support</button>
                </div>
              </aside>

              <main className="main">
                <header className="topbar">
                  <button className="mobile-menu" onClick={() => setMobileNav(!mobileNav)}>
                    <Menu/>
                  </button>
                  <div>
                    <div className="eyebrow">QUESTHUB / {user?.role?.toUpperCase()}</div>
                    <h1>
                      {user?.role === "admin" ? "Admin Dashboard" :
                        user?.role === "youth_worker" ? "Yield Worker Dashboard" :
                        user?.role === "player" ? "Player Dashboard" :
                        "Overview"}
                    </h1>
                    <p>{user?.role === "player" ? "Live data from the supplied FastAPI backend." : "Live data from the supplied FastAPI backend."}</p>
                  </div>
                  <div className="top-actions">
                    <button className="icon-btn" onClick={refresh}><RotateIcon/></button>
                    <button className="icon-btn" onClick={() => pushToast("Notifications endpoint can be connected here", "info")}><Bell size={18}/></button>
                    {user && <div className="staff-avatar">{user.username.slice(0,2).toUpperCase()}</div>}
                  </div>
                </header>
                {error && <div className="api-error"><AlertTriangle size={16}/><span>{error}</span><button onClick={() => setError("")}><X size={14}/></button></div>}
                {/* Render the appropriate view based on the section */}
                {section === "Overview" && <Overview data={data} role={user?.role} openAward={() => setAwardOpen(true)} openWheel={() => setWheelOpen(true)} openRewards={() => setRewardManagerOpen(true)} pushToast={pushToast} demoPlayers={demoPlayers} />}
                {section === "Players" && <Players data={data} setSelectedPlayer={setSelectedPlayer} openAward={() => setAwardOpen(true)} openUsers={() => setUserManagerOpen(true)} pushToast={pushToast} refresh={refresh} />}
                {section === "Groups" && <Groups data={data} pushToast={pushToast} />}
                {section === "Challenges" && <Challenges openWheel={() => setWheelOpen(true)} pushToast={pushToast} />}
                {section === "Points & Rewards" && <Points openAward={() => setAwardOpen(true)} pushToast={pushToast} openEconomy={() => setEconomyOpen(true)} openRewards={() => setRewardManagerOpen(true)} />}
                {section === "Points Requests" && <PointRequests data={data} openPointRequests={() => setPointRequestsOpen(true)} pushToast={pushToast} refresh={refresh} />}
                {section === "Drawing Games" && <div>Drawing Games placeholder</div>}
                {section === "Users & Groups" && <Players data={data} setSelectedPlayer={setSelectedPlayer} openAward={() => setAwardOpen(true)} openUsers={() => setUserManagerOpen(true)} pushToast={pushToast} refresh={refresh} />}
                {section === "Map" && <div>Map placeholder</div>}
                {section === "Rewards & Points" && <div>Rewards & Points placeholder</div>}
                {section === "Community Nominations" && <div>Community Nominations placeholder</div>}
                {section === "Resources" && <div>Resources placeholder</div>}
                {section === "Reports" && <div>Reports placeholder</div>}
                {section === "Phases & Themes" && <div>Phases & Themes placeholder</div>}
                {section === "Analytics" && <div>Analytics placeholder</div>}
                {section === "System Settings" && <div>System Settings placeholder</div>}
                {/* Default to Overview if section doesn't match any of the above */}
                {!["Overview", "Players", "Groups", "Challenges", "Points & Rewards", "Points Requests", "Drawing Games", "Users & Groups", "Map", "Rewards & Points", "Community Nominations", "Resources", "Reports", "Phases & Themes", "Analytics", "System Settings"].includes(section) && <Overview data={data} role={user?.role} openAward={() => setAwardOpen(true)} openWheel={() => setWheelOpen(true)} openRewards={() => setRewardManagerOpen(true)} pushToast={pushToast} demoPlayers={demoPlayers} />}
              </main>
            </div>
          )
        } />

        {/* Default route - redirect to login if not authenticated, or to dashboard if authenticated */}
        <Route path="*" element={
          !user ? <Navigate to="/login" replace={true} /> : <Navigate to="/dashboard" replace={true} />
        } />
      </Routes>

      <div className="toast-stack">{toasts.map(t => <div className={`toast ${t.tone ?? "success"}`} key={t.id}><Check size={16}/>{t.text}<button onClick={() => setToasts(v => v.filter(x => x.id !== t.id))}><X size={14}/></button></div>)}
      </div>
    </>
  );
}

function UserManagerModal({users,onClose,refresh,pushToast}:{users:any[];onClose:()=>void;refresh:()=>Promise<void>;pushToast:(s:string,t?:any)=>void}) {
  const [editing,setEditing]=useState<any>(null);
  const [form,setForm]=useState<any>({username:"",password:"",role:"player",display_name:"",gamertag:"",avatar:"avatar-01",group_id:"",public_visible:true});
  const [busy,setBusy]=useState(false);
  const set=(k:string,v:any)=>setForm((x:any)=>({...x,[k]:v}));
  const open=(u:any)=>{setEditing(u);setForm({username:u.username,password:"",role:u.role,display_name:u.display_name??"",gamertag:u.player?.gamertag??"",avatar:u.player?.avatar??"avatar-01",group_id:u.player?.group_id??"",public_visible:u.player?.public_visible??true})};
  const create=()=>{setEditing(null);setForm({username:"",password:"",role:"player",display_name:"",gamertag:"",avatar:"avatar-01",group_id:"",public_visible:true})};
  const save=async()=>{
    setBusy(true);
    try{
      const body:any={username:form.username,role:form.role,display_name:form.display_name||null};
      if(form.password)body.password=form.password;
      if(form.role==="player"){body.gamertag=form.gamertag;body.avatar=form.avatar;body.public_visible=!!form.public_visible;if(form.group_id!=="")body.group_id=Number(form.group_id)}
      if(editing)await api.updateUser(editing.id,body);
      else await api.createUser({...body,password:form.password,active:true});
      pushToast(editing?"Account updated":"User created");
      await refresh();
      if(!editing)create();
    }catch(e:any){
      pushToast(e.message,"warning");
    }finally{
      setBusy(false);
    }
  };
  const action=async(u:any,kind:string)=>{try{if(kind==="pause")await api.pauseUser(u.id);if(kind==="reactivate")await api.reactivateUser(u.id);if(kind==="suspend"&&u.player)await api.suspendPlayer(u.player.id);if(kind==="unsuspend"&&u.player)await api.unsuspendPlayer(u.player.id);pushToast(kind+" complete");await refresh();}catch(e:any){pushToast(e.message,"warning");}};
  return <Modal title="Manage accounts" onClose={onClose}>
    <div className="user-manager">
      <div className="section-heading">
        <span className="eyebrow">ADMIN ONLY</span>
        <button className="primary-btn" onClick={create}><Plus size={15}/> New user</button>
      </div>
      <div className="form-grid">
        <label>Username<input value={form.username} onChange={e=>set("username",e.target.value)} /></label>
        <label>Role<select value={form.role} onChange={e=>set("role",e.target.value)}><option value="player">Young person</option><option value="youth_worker">Youth worker</option><option value="admin">Admin</option></select></label>
        <label>Password {editing&&<small>(leave blank to keep current)</small>}<input type="password" value={form.password} onChange={e=>set("password",e.target.value)} placeholder="Minimum 10 characters" /></label>
        {form.role==="player"&&<><label>Gamertag<input value={form.gamertag} onChange={e=>set("gamertag",e.target.value)} /></label><label>Group ID<input type="number" value={form.group_id} onChange={e=>set("group_id",e.target.value)} placeholder="Optional" /></label><label>Avatar<input value={form.avatar} onChange={e=>set("avatar",e.target.value)}/></label></>}
      </div>
      <button className="primary-btn wide" disabled={busy||!form.username||(!editing&&!form.password)} onClick={save}>{busy?"Saving…":editing?"Save changes":"Create user"}</button>
      <div className="panel inset">
        <div className="panel-head">
          <h3>Accounts</h3>
          <span className="count-pill">{users.length}</span>
        </div>
        {users.map((u:any)=><div className="setting-line" key={u.id}>
          <div><b>{u.username}</b><small style={{display:"block",color:"#70808e"}}>{u.role} · {u.player?.gamertag??u.display_name??"Staff account"}</small></div>
          <div className="nom-actions">
            <span className={`status ${u.active?"":"inactive"}`}>{u.active?"Active":"Paused"}</span>
            <button className="ghost-btn" onClick={()=>open(u)}>Edit</button>
            {u.active ? (
  <button className="ghost-btn" onClick={() => action(u, "pause")}>
    Pause
  </button>
) : (
  <button className="ghost-btn" onClick={() => action(u, "reactivate")}>
    Reactivate
  </button>
)}
{u.player && (
  u.player.suspended ? (
    <button className="ghost-btn" onClick={() => action(u, "unsuspend")}>
      Unsuspend
    </button>
  ) : (
    <button className="ghost-btn" onClick={() => action(u, "suspend")}>
      Suspend
    </button>
  )
)}
          </div>
        </div>)}
      </div>
    </div>
  </Modal>
}

function EconomyModal({onClose,pushToast}:{onClose:()=>void;pushToast:(s:string,t?:any)=>void}) {
  const [v,setV]=useState<any>(null);
  const [busy,setBusy]=useState(false);
  useEffect(()=>{api.economy().then(setV).catch(e=>pushToast(e.message,"warning"))},[]);
  if(!v)return <Modal title="Economy settings" onClose={onClose}><p className="muted">Loading…</p></Modal>;
  const set=(k:string,x:any)=>setV((a:any)=>({...a,[k]:x}));
  const save=async()=>{
    setBusy(true);
    try{
      await api.updateEconomy({jackpot_target_xp:Number(v.jackpot_target_xp),max_group_penalty_percent:Number(v.max_group_penalty_percent),max_staff_multiplier:Number(v.max_staff_multiplier),weekly_growth_cap_multiplier:Number(v.weekly_growth_cap_multiplier),group_penalties_enabled:!!v.group_penalties_enabled,multipliers_enabled:!!v.multipliers_enabled});
      pushToast("Economy saved");
      onClose();
    }catch(e:any){
      pushToast(e.message,"warning");
    }finally{
      setBusy(false);
    }
  };
  return <Modal title="Economy settings" onClose={onClose}>
    <div className="form-grid">
      <label>Jackpot target XP<input type="number" value={v.jackpot_target_xp} onChange={e=>set("jackpot_target_xp",e.target.value)}/></label>
      <label>Max group penalty %<input type="number" value={v.max_group_penalty_percent} onChange={e=>set("max_group_penalty_percent",e.target.value)}/></label>
      <label>Max staff multiplier<input type="number" step="0.1" value={v.max_staff_multiplier} onChange={e=>set("max_staff_multiplier",e.target.value)}/></label>
      <label>Weekly growth cap multiplier<input type="number" step="0.1" value={v.weekly_growth_cap_multiplier} onChange={e=>set("weekly_growth_cap_multiplier",e.target.value)}/></label>
      <label>Group penalties<select value={String(!!v.group_penalties_enabled)} onChange={e=>set("group_penalties_enabled",e.target.value==="true")}><option value="true">Enabled</option><option value="false">Disabled</option></select></label>
      <label>Multipliers<select value={String(!!v.multipliers_enabled)} onChange={e=>set("multipliers_enabled",e.target.value==="true")}><option value="true">Enabled</option><option value="false">Disabled</option></select></label>
    </div>
    <button className="primary-btn wide" disabled={busy} onClick={save}>{busy?"Saving…":"Save economy"}</button>
  </Modal>;
}

function RewardManagerModal({onClose,pushToast}:{onClose:()=>void;pushToast:(s:string,t?:any)=>void}) {
  const [games,setGames]=useState<any[]>([]);
  const [targets,setTargets]=useState<any>({players:[],groups:[]});
  const [form,setForm]=useState<any>({name:"Spin the Wheel",description:"",game_type:"wheel",prize_values:"500,1000,2000",starts_at:"",ends_at:"",active:true,show_upcoming:true});
  const [target,setTarget]=useState("player");
  const [targetId,setTargetId]=useState("");
  const load=async()=>{
    try{
      const [g,t]=await Promise.all([api.adminRewardGames(),api.rewardGameTargets()]);
      setGames(g);
      setTargets(t);
    }catch(e:any){
      pushToast(e.message,"warning");
    }
  };
  useEffect(()=>{load()},[]);
  const set=(k:string,x:any)=>setForm((a:any)=>({...a,[k]:x}));
  const create=async()=>{
    try{
      await api.createRewardGame({...form,prize_values:form.prize_values.split(",").map((x:string)=>Number(x.trim())).filter((x:number)=>Number.isFinite(x)),starts_at:form.starts_at||null,ends_at:form.ends_at||null});
      pushToast("Reward game created");
      await load();
    }catch(e:any){
      pushToast(e.message,"warning");
    }
  };
  const grant=async(game:any)=>{
    if(!targetId)return;
    try{
      await api.grantRewardGame(game.id,target==="player"?{player_id:Number(targetId)}:{group_id:Number(targetId)});
      pushToast("Reward entitlement granted");
    }catch(e:any){
      pushToast(e.message,"warning");
    }
  };
  const toggle=async(g:any)=>{
    try{
      await api.updateRewardGame(g.id,{active:!g.active});
      pushToast(g.active?"Reward game paused":"Reward game activated");
      await load();
    }catch(e:any){
      pushToast(e.message,"warning");
    }
  };
  return <Modal title="Reward games" onClose={onClose}>
    <div className="form-grid">
      <label>Name<input value={form.name} onChange={e=>set("name",e.target.value)}/></label>
      <label>Description<textarea value={form.description} onChange={e=>set("description",e.target.value)}/></label>
      <label>Prize values (XP, comma separated)<input value={form.prize_values} onChange={e=>set("prize_values",e.target.value)} placeholder="500,1000,2000"/></label>
      <label>Starts at<input type="datetime-local" value={form.starts_at} onChange={e=>set("starts_at",e.target.value)}/></label>
      <label>Ends at<input type="datetime-local" value={form.ends_at} onChange={e=>set("ends_at",e.target.value)}/></label>
    </div>
    <button className="primary-btn wide" onClick={create}><Plus size={15}/> Create reward game</button>
    <div className="panel inset" style={{marginTop:12}}>
      <div className="panel-head">
        <h3>Grant entitlement</h3>
      </div>
      <div className="form-grid">
        <label>Target<select value={target} onChange={e=>{setTarget(e.target.value);setTargetId("")}}><option value="player">Player</option><option value="group">Group</option></select></label>
        <label>{target==="player" ? "Player" : "Group"}<select value={targetId} onChange={e=>setTargetId(e.target.value)}><option value="">Select…</option>{target==="player" ? targets.players.map((p:any)=><option key={p.id} value={p.id}>{p.gamertag}</option>) : targets.groups.map((g:any)=><option key={g.id} value={g.id}>{g.name}</option>)}</select></label>
      </div>
      {games.map((g)=>(<div className="setting-line" key={g.id}>
        <span><b>{g.name}</b><small style={{display:"block",color:"#70808e"}}>{g.active?"Active":"Paused"} · {g.available_entitlements} available · prizes hidden from players</small></span>
        <div className="nom-actions">
          <button className="ghost-btn" onClick={()=>toggle(g)}>{g.active?"Pause":"Activate"}</button>
          <button className="secondary-btn" disabled={!targetId||!g.active} onClick={()=>grant(g)}>Grant</button>
        </div>
      </div>))}
    </div>
  </Modal>;
}

function DrawingGameManagerModal({onClose}:{onClose:()=>void}) {
  return <Modal title="Drawing Games Manager" onClose={onClose}>
    <p className="muted">Drawing games management coming soon.</p>
  </Modal>;
}

function PlayerQrModal({onClose,pushToast}:{onClose:()=>void;pushToast:(s:string,t?:any)=>void}) {
  const [token,setToken]=useState("");
  const [busy,setBusy]=useState(true);
  const load=async()=>{
    setBusy(true);
    try{
      const r=await api.rotatePlayerQr();
      setToken(r.token);
    }catch(e:any){
      pushToast(e.message,"warning");
    }finally{
      setBusy(false);
    }
  };
  useEffect(()=>{load()},[]);
  const value=token?`${window.location.origin}/request-points?token=${encodeURIComponent(token)}`:"";
  return <Modal title="My Quest QR" onClose={onClose}>
    <div className="qr-modal">{busy?<div className="loader-ring"/>:token?<><div className="qr-frame"><QRCodeCanvas value={value} size={230}/></div><h3>Show this code</h3><p className="muted">The code does not reveal the player's name. Scanning opens the extra-XP request form.</p><button className="ghost-btn wide" onClick={load}>Rotate QR</button></>:<p className="muted">Unable to generate your QR.</p>}</div>
  </Modal>
}

function PointRequestsModal({onClose,pushToast,refresh}:{onClose:()=>void;pushToast:(s:string,t?:any)=>void;refresh:()=>Promise<void>}) {
  const [rows,setRows]=useState<any[]>([]);
  const [busy,setBusy]=useState<number|null>(null);
  const load=async()=>{
    try{
      setRows(await api.pointRequests("pending"));
    }catch(e:any){
      pushToast(e.message,"warning");
    }
  };
  useEffect(()=>{load()},[]);
  const decide=async(r:any,approved:boolean)=>{
    let amount=r.requested_xp;
    let note="";
    if(approved){
      const x=window.prompt(`Approve XP for ${r.gamertag}`,String(r.requested_xp));
      if(x===null)return;
      amount=Number(x);
      if(!Number.isFinite(amount)||amount<1||amount>5000){
        pushToast("XP must be between 1 and 5,000","warning");
        return;
      }
      note=window.prompt("Optional review note","")||"";
    }else note=window.prompt("Reason for rejection","")||"Request declined by youth worker.";
    setBusy(r.id);
    try{
      if(approved)await api.approvePointRequest(r.id,{approved_xp:amount,review_note:note||null});
      else await api.rejectPointRequest(r.id,{review_note:note});
      pushToast(approved?`+${amount.toLocaleString()} XP approved`:`Request #${r.id} rejected`);
      await load();
      await refresh();
    }catch(e:any){
      pushToast(e.message,"warning");
    }finally{
      setBusy(null);
    }
  };
  return <Modal title="Points requests" onClose={onClose}>
    <div className="panel inset">
      <div className="panel-head">
        <h3>Pending review</h3>
        <button className="ghost-btn" onClick={load}><RotateIcon/></button>
      </div>
      {rows.length===0?<p className="muted">Nothing waiting for review.</p>:rows.map(r=><div className="request-card" key={r.id}>
        <div className="request-card-head">
          <div><b>{r.gamertag}</b><small>Request #{r.id} · {r.created_at?new Date(r.created_at).toLocaleString():""}</small></div>
          <strong>+{r.requested_xp.toLocaleString()} XP</strong>
        </div>
        <p>{r.reason}</p>
        <div className="nom-actions">
          <button className="primary-btn" disabled={busy===r.id} onClick={()=>decide(r,true)}><Check size={15}/> Approve</button>
          <button className="ghost-btn" disabled={busy===r.id} onClick={()=>decide(r,false)}>Reject</button>
        </div>
      </div>)}
    </div>
  </Modal>
}

function AwardModal({players,selected,setSelected,onClose,pushToast}:{players:any[];selected:any;setSelected:(p:any)=>void;onClose:()=>void;pushToast:(s:string,t?:any)=>void}) {
  const [pick,setPick]=useState(selected?.id??players[0]?.id??"");
  const [amount,setAmount]=useState(500);
  const [reason,setReason]=useState("Positive participation");
  return <Modal title="Award Points" onClose={onClose}>
    <div className="form-grid">
      <label>Player<select value={pick} onChange={e=>{setPick(Number(e.target.value));setSelected(players.find(p=>p.id===Number(e.target.value)))}}>{players.map(p=><option key={p.id} value={p.id}>{p.gamertag}</option>)}</select></label>
      <label>Amount<input type="number" value={amount} onChange={e=>setAmount(Number(e.target.value))}/></label>
      <label>Reason<textarea value={reason} onChange={e=>setReason(e.target.value)}/></label>
    </div>
    <button className="primary-btn wide" onClick={async()=>{try{await api.awardXp(Number(pick),amount,reason);pushToast(`+${amount.toLocaleString()} XP awarded`);onClose();}catch(e:any){pushToast(e.message,"warning");}}}><Plus size={17}/> Award XP</button>
  </Modal>;
}