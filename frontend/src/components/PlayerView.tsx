import React from "react";
import { Activity, Award, Gauge, Trophy, Users } from "lucide-react";

type PlayerViewProps = {
  data: any;
  section: string;
  openWheel: () => void;
  openQr: () => void;
  pushToast: (s: string, t?: any) => void;
};

export default function PlayerView({ data, section, openWheel, openQr, pushToast }: PlayerViewProps) {
  const player = data?.player ?? {};
  const games = data?.games ?? [];

  return (
    <div className="page">
      <div className="section-heading">
        <div>
          <span className="eyebrow">PLAYER DASHBOARD</span>
          <h2>Player Dashboard</h2>
          <p>Your personal progress and rewards.</p>
        </div>
      </div>

      <div className="hero-grid">
        <div className="hero-card">
          <div className="hero-copy">
            <div className="badge-line">
              <span className="live-dot"/> YOUR DATA
            </div>
            <h2>
              {Number(player.xp ?? 0).toLocaleString()} <span>XP</span>
            </h2>
            <p>
              Level {Math.floor(Math.sqrt(player.xp ?? 0) / 10) + 1}
            </p>
            <div className="progress">
              <i
                style={{
                  width: `${Math.min(100, ((player.xp ?? 0) % 1000) / 10)}%`,
                }}
              />
            </div>
          </div>
          <div className="hero-visual">
            <div className="orbit orbit-1" />
            <div className="orbit orbit-2" />
            <div className="trophy" style={{ width: 46, height: 46 }} />
          </div>
        </div>

        <section className="stats-grid">
          <div className="stat">
            <div className="stat-icon">
              <Users />
            </div>
            <div>
              <span>Your rank</span>
              <strong>
                {player.rank ?? "?"}
              </strong>
              <small>out of {player.rank_total ?? 0}</small>
            </div>
          </div>
          <div className="stat">
            <div className="stat-icon">
              <Gauge />
            </div>
            <div>
              <span>Weekly XP</span>
              <strong>{Number(player.weekly_xp ?? 0).toLocaleString()}</strong>
              <small>/{Number(data?.overview?.weekly_target_xp ?? 0).toLocaleString()} target</small>
            </div>
          </div>
          <div className="stat">
            <div className="stat-icon">
              <Award />
            </div>
            <div>
              <span>Achievements</span>
              <strong>{player.achievements?.length ?? 0}</strong>
              <small>unlocked</small>
            </div>
          </div>
          <div className="stat">
            <div className="stat-icon">
              <Activity />
            </div>
            <div>
              <span>Activity</span>
              <strong>{player.activity_count ?? 0}</strong>
              <small>sessions this week</small>
            </div>
          </div>
        </section>

        <section className="content-grid">
          <div className="panel large">
            <div className="panel-head">
              <div>
                <span className="eyebrow">REWARDS AVAILABLE</span>
                <h3>Spin to win XP</h3>
              </div>
              <button className="primary-btn wide" onClick={openWheel}>
                <Trophy size={16} /> Spin the Wheel
              </button>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head">
              <div>
                <span className="eyebrow">YOUR QR CODE</span>
                <h3>Scan to request extra XP</h3>
              </div>
              <button className="secondary-btn wide" onClick={openQr}>
                <Users size={16} /> My QR Code
              </button>
            </div>
          </div>
        </section>

        {games.length > 0 && (
          <section className="panel jackpot">
            <div>
              <span className="eyebrow">ACTIVE REWARD GAMES</span>
              <h3>Current opportunities</h3>
              <p>Participate in active reward games to earn bonus XP.</p>
            </div>
            <div className="jackpot-actions">
              {games.map((game: any) => (
                <button
                  key={game.id}
                  className="secondary-btn"
                  onClick={() => {/* TODO: join game */}}
                >
                  {game.name}
                </button>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
