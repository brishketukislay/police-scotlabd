import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from "react-router-dom";
import { Activity, AlertTriangle, ArrowUpRight, Award, BarChart3, Bell, Check, ChevronRight, CircleHelp, Gauge, LayoutDashboard, LogOut, Map, Menu, MoreHorizontal, Search, Settings, ShieldCheck, Sparkles, Trophy, Users as LucideUsers, WalletCards, X, Zap } from "lucide-react";
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
import UserManagerModal from "./components/modals/UserManagerModal";
import EconomyModal from "./components/modals/EconomyModal";
import RewardManagerModal from "./components/modals/RewardManagerModal";
import DrawingGameManagerModal from "./components/modals/DrawingGameManagerModal";
import PlayerQrModal from "./components/modals/PlayerQrModal";
import PointRequestsModal from "./components/modals/PointRequestsModal";
import AwardModal from "./components/modals/AwardModal";
import { getNavigation } from "./navigation";

const demoPlayers = [
  {id:1,gamertag:"PixelRanger",xp:24530,status:"Active",badge:"Silver",color:"lime"},
  {id:2,gamertag:"NovaSquad",xp:18740,status:"Active",badge:"Bronze",color:"purple"},
  {id:3,gamertag:"StormCrew",xp:15640,status:"Active",badge:"Bronze",color:"cyan"},
  {id:4,gamertag:"UrbanLegends",xp:12450,status:"At risk",badge:"Iron",color:"yellow"},
];

type Toast = {id:number;text:string;tone?:"success"|"info"|"warning"};

const isStaff = (user: SessionUser | null) =>
  user?.role === "admin" || user?.role === "youth_worker";

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
  // Public dashboard shell state.
  // The sidebar remains available outside TV/fullscreen mode.
  const [publicSidebarOpen, setPublicSidebarOpen] = useState(true);
  const [publicTvMode, setPublicTvMode] = useState(false);
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

  useEffect(() => {
    const handlePublicTvMode = (event: Event) => {
      const customEvent = event as CustomEvent<{ active?: boolean }>;

      if (typeof customEvent.detail?.active === "boolean") {
        setPublicTvMode(customEvent.detail.active);
      }
    };

    window.addEventListener("public-tv-mode", handlePublicTvMode);

    return () => {
      window.removeEventListener("public-tv-mode", handlePublicTvMode);
    };
  }, []);

  // We'll keep the nav memo, but we will base it on the current route and user.
  // However, note that the nav is used in the sidebar, which is only shown in the dashboard route.
  // We will compute the nav items based on the user role, but we will only use it when we are in the dashboard route.


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

  const nav = getNavigation(user, isStaff);

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
          <div className={`app-shell public-app-shell${publicTvMode ? " public-tv-mode" : ""}`}>
            {/* Public dashboard sidebar. Hidden automatically in TV mode via CSS. */}
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
              {data ? (
                <PublicView
                  data={data}
                  onTvModeChange={(active) => {
                    setPublicTvMode(active);
                  }}
                />
              ) : (
                <div className="center-screen">
                  <p>Loading public dashboard...</p>
                </div>
              )}
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

