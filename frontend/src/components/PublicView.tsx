import React from "react";
import { Users, Gauge, Award, Activity, Plus, Sparkles, AlertTriangle } from "lucide-react";

type PublicViewProps = {
  data: any;
  section: string;
};

export default function PublicView({ data, section }: PublicViewProps) {
  return (
    <div className="page">
      <div className="section-heading">
        <div>
          <span className="eyebrow">PUBLIC DASHBOARD</span>
          <h2>Public Dashboard</h2>
          <p>View anonymised collective progress and community activity.</p>
        </div>
      </div>

      <div className="hero-grid">
        <div className="hero-card">
          <div className="hero-copy">
            <div className="badge-line">
              <span className="live-dot"/> LIVE DATA
            </div>
            <h2>
              {data?.overview?.group_xp ?? 0} <span>XP</span>
            </h2>
            <p>
              {((data?.overview?.group_xp ?? 0) / (data?.overview?.target_xp ?? 1500000)) * 100}% toward the{" "}
              <b>{(data?.overview?.target_xp ?? 1500000).toLocaleString()} XP jackpot</b>
            </p>
            <div className="progress">
              <i
                style={{
                  width: `${((data?.overview?.group_xp ?? 0) / (data?.overview?.target_xp ?? 1500000)) * 100}%`,
                }}
              />
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
            <div className="trophy" style={{ width: 46, height: 46 }} />
          </div>
          <div className="map-card">
            <div className="card-head">
              <div>
                <span className="eyebrow">CURRENT PROGRAMME</span>
                <h3>{data?.overview?.programme ?? "Youth Challenge"}</h3>
              </div>
              {/* Map placeholder */}
              <div className="map-art" style={{ height: 132 }}>
                <div className="map-lines" />
                <div className="map-pin p1" />
                <div className="map-pin p2" />
                <div className="map-pin p3" />
              </div>
            </div>
          </div>
        </div>

        <section className="stats-grid">
          <div className="stat">
            <div className="stat-icon">
              <Users />
            </div>
            <div>
              <span>Active players</span>
              <strong>{data?.overview?.players ?? 0}</strong>
              <small>{data?.overview?.staff ?? 0} staff</small>
            </div>
          </div>
          <div className="stat">
            <div className="stat-icon">
              <Gauge />
            </div>
            <div>
              <span>Programme target</span>
              <strong>{(data?.overview?.target_xp ?? 1500000).toLocaleString()}</strong>
              <small>{(data?.overview?.weekly_target_xp ?? 0).toLocaleString()} weekly</small>
            </div>
          </div>
          <div className="stat">
            <div className="stat-icon">
              <Award />
            </div>
            <div>
              <span>Public visibility</span>
              <strong>API</strong>
              <small>Controlled by backend</small>
            </div>
          </div>
          <div className="stat">
            <div className="stat-icon">
              <Activity />
            </div>
            <div>
              <span>Data source</span>
              <strong>Live</strong>
              <small>FastAPI + SQLite</small>
            </div>
          </div>
        </section>

        <section className="content-grid">
          <div className="panel large">
            <div className="panel-head">
              <div>
                <span className="eyebrow">LIVE PARTICIPATION</span>
                <h3>Recent activity</h3>
              </div>
            </div>
            <div className="activity-list">
              {/* Placeholder for live players */}
              {(data?.players ?? []).slice(0, 5).map((p: any) => (
                <div className="activity" key={p.id}>
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
          </div>

          <div className="panel">
            <div className="panel-head">
              <div>
                <span className="eyebrow">ENGAGEMENT INSIGHTS</span>
                <h3>Supportive metrics</h3>
              </div>
              <AlertTriangle size={18} />
            </div>
            <div className="risk-list">
              {/* Placeholder for at-risk players */}
              {(data?.players ?? []).slice(0, 4).map((p: any) => (
                <div className="risk" key={p.id}>
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
            <button className="secondary-btn" onClick={() => {/* openRewards placeholder */}}>
              <Sparkles size={17} /> Reward game
            </button>
            <button className="primary-btn" onClick={() => {/* openAward placeholder */}}>
              <Plus size={17} /> Award XP
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
