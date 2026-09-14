import Stat from "./Stat";
import { Map, Trophy, Users, Gauge, Award, Activity, ArrowUpRight, MoreHorizontal, AlertTriangle, Sparkles, Plus } from "lucide-react";
import { Role } from "../api";

function Overview({data, role, openAward, openWheel, openRewards, pushToast, demoPlayers}: {data: any; role?: Role; openAward: () => void; openWheel: () => void; openRewards: () => void; pushToast: (s: string, t?: any) => void; demoPlayers: any[]}) {
  const o = data?.overview ?? {};
  const pct = o.target_xp ? Math.min(100, (o.group_xp / o.target_xp) * 100) : 0;
  const ps = data?.players ?? demoPlayers;
  return (
    <div className="page">
      <section className="hero-grid">
        <div className="hero-card">
          <div className="hero-copy">
            <div className="badge-line">
              <span className="live-dot"/> LIVE API DATA
            </div>
            <h2>
              {Number(o.group_xp ?? 0).toLocaleString()} <span>XP</span>
            </h2>
            <p>
              {pct.toFixed(0)}% toward the{" "}
              <b>{Number(o.target_xp ?? 1500000).toLocaleString()} XP jackpot</b>
            </p>
            <div className="progress">
              <i style={{width: `${pct}%`}} />
            </div>
            <div className="milestones">
              <span>
                <b>500K</b><small>£250</small>
              </span>
              <span>
                <b>1M</b><small>£750</small>
              </span>
              <span>
                <b>1.5M</b><small>£2,200</small>
              </span>
            </div>
          </div>
          <div className="hero-visual">
            <div className="orbit orbit-1" />
            <div className="orbit orbit-2" />
            <Trophy size={46} />
          </div>
          <div className="map-card">
            <div className="card-head">
              <div>
                <span className="eyebrow">CURRENT PROGRAMME</span>
                <h3>{o.programme ?? "Youth Challenge"}</h3>
              </div>
              <Map size={19} />
            </div>
            <div className="map-art">
              <div className="map-lines" />
              <div className="map-pin p1" />
              <div className="map-pin p2" />
              <div className="map-pin p3" />
              <button className="ghost-btn">
                Open Cumbernauld map <ArrowUpRight size={15} />
              </button>
            </div>
          </div>
        </div>
        <section className="stats-grid">
          <Stat icon={<Users/>} label="Active players" value={String(o.players ?? ps.length)} delta={`${o.staff ?? 0} staff`} />
          <Stat icon={<Gauge/>} label="Programme target" value={Number(o.target_xp ?? 0).toLocaleString()} delta={`${Number(o.weekly_target_xp ?? 0).toLocaleString()} weekly`} />
          <Stat icon={<Award/>} label="Public visibility" value="API" delta="Controlled by backend" />
          <Stat icon={<Activity/>} label="Data source" value="Live" delta="FastAPI + SQLite" />
        </section>
        <section className="content-grid">
          <div className="panel large">
            <div className="panel-head">
              <div>
                <span className="eyebrow">LIVE PLAYERS</span>
                <h3>Progress from the backend</h3>
              </div>
              <button className="icon-btn">
                <MoreHorizontal />
              </button>
            </div>
            {ps.slice(0, 5).map((p: any) => (
              <div className="activity" key={p.id ?? p.gamertag}>
                <div className="mini-avatar">
                  {(p.gamertag ?? "P")[0]}
                </div>
                <div>
                  <b>{p.gamertag}</b>
                  <span>
                    {Number(p.xp ?? 0).toLocaleString()} XP ·
                    {p.public_visible === false ? "Private" : "Visible"}
                  </span>
                </div>
                <strong>{p.status ?? "Active"}</strong>
                <small>{p.badge ?? ""}</small>
              </div>
            ))}
          </div>
          <div className="panel">
            <div className="panel-head">
              <div>
                <span className="eyebrow">SUPPORT SIGNALS</span>
                <h3>Not surveillance</h3>
              </div>
              <AlertTriangle size={18} />
            </div>
            <div className="risk-list">
              {ps.slice(0, 4).map((p: any) => (
                <div className="risk" key={p.id ?? p.gamertag}>
                  <div className="mini-avatar">
                    {(p.gamertag ?? "P")[0]}
                  </div>
                  <div>
                    <b>{p.gamertag}</b>
                    <span>Use activity data to support engagement.</span>
                  </div>
                  <span className="status">
                    {p.active === false ? "Inactive" : "Active"}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>
        <section className="panel jackpot">
          <div>
            <span className="eyebrow">QUICK ACTIONS</span>
            <h3>Keep the experience moving</h3>
            <p>Award XP or open a configured reward-game flow.</p>
          </div>
          <div className="jackpot-actions">
            <button className="secondary-btn" onClick={openRewards}>
              <Sparkles size={17} /> Reward game
            </button>
            <button className="primary-btn" onClick={openAward}>
              <Plus size={17} /> Award XP
            </button>
          </div>
        </section>
      </section>
    </div>
  );
}

export default Overview;
