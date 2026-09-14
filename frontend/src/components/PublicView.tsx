import {
  Activity,
  Award,
  Gauge,
  Map as MapIcon,
  Trophy,
} from "lucide-react";
import { useState, useEffect } from "react";

type PublicViewProps = {
  data: any;
  section: string;
};

export default function PublicView({
  data,
  section,
}: PublicViewProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
  };

  // Update fullscreen state when it changes externally
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => {
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
    };
  }, []);

  const programme = data?.programme;
  const groupXp = Number(data?.group_xp ?? 0);
  const targetXp = Number(programme?.target_xp ?? 1500000);

  const percentage =
    targetXp > 0
      ? Math.min(100, (groupXp / targetXp) * 100)
      : 0;

  // Always show the dashboard view (ignore section prop for public dashboard)
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        backgroundColor: "#ffffff",
        color: "#17221e",
      }}
    >
      {/* Header */}
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "1.5rem 2rem",
          backgroundColor: "#070a0f",
          color: "#ffffff",
          borderBottom: "1px solid #00ff88",
        }}
      >
        <div>
          <h1 style={{ margin: 0, fontSize: "1.5rem" }}>QuestHub Public Dashboard</h1>
          <p style={{ margin: 0, fontSize: "0.9rem", opacity: 0.8 }}>
            Live community progress
          </p>
        </div>
        <button
          onClick={toggleFullscreen}
          style={{
            backgroundColor: isFullscreen ? "#00ff88" : "#ffffff",
            color: isFullscreen ? "#070a0f" : "#00ff88",
            border: "none",
            padding: "0.5rem 1rem",
            borderRadius: "4px",
            cursor: "pointer",
            fontWeight: 600,
          }}
        >
          {isFullscreen ? "Exit Fullscreen" : "View Fullscreen"}
        </button>
      </header>

      {/* Main Content */}
      <main
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          gap: "2rem",
          padding: "2rem",
          overflowY: "auto",
        }}
      >
        {/* Hero Stats */}
        <section
          style={{
            display: "flex",
            gap: "2rem",
            alignItems: "flex-start",
          }}
        >
          <div
            style={{
              flex: 1,
              backgroundColor: "#f3f7f5",
              borderRadius: "8px",
              padding: "1.5rem",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", marginBottom: "0.5rem" }}>
              <div
                style={{
                  width: "8px",
                  height: "8px",
                  backgroundColor: "#00ff88",
                  borderRadius: "50%",
                  marginRight: "0.5rem",
                }}
              />
              <span style={{ fontSize: "0.9rem", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                LIVE DATA
              </span>
            </div>
            <h2
              style={{
                margin: 0,
                fontSize: "2.5rem",
                fontWeight: 600,
                background: "linear-gradient(to right, #00ff88, #18775b)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              {groupXp.toLocaleString()}<span style={{ fontSize: "1.5rem" }}> XP</span>
            </h2>
            <p style={{ margin: "0.5rem 0", fontSize: "1.1rem", color: "#70808e" }}>
              {percentage.toFixed(1)}% toward the{" "}
              <span style={{ fontWeight: 600 }}>
                {targetXp.toLocaleString()} XP target
              </span>
            </p>
            <div
              style={{
                height: "12px",
                backgroundColor: "#e0e0e0",
                borderRadius: "6px",
                overflow: "hidden",
                marginTop: "1rem",
              }}
            >
              <div
                style={{
                  width: `${percentage}%`,
                  height: "100%",
                  background: "linear-gradient(to right, #00ff88, #18775b)",
                  transition: "width 0.3s ease",
                }}
              ></div>
            </div>
            <div style={{ marginTop: "0.5rem", fontSize: "0.9rem", color: "#70808e" }}>
              <span>
                <b>500K</b> <small>Level 1</small>
              </span>
              <span style={{ margin: "0 1rem" }}>
                <b>1M</b> <small>Level 2</small>
              </span>
              <span>
                <b>1.5M</b> <small>Finale</small>
              </span>
            </div>
          </div>

          {/* Hero Visual - simplified */}
          <div
            style={{
              width: "200px",
              height: "200px",
              position: "relative",
            }}
          >
            <div
              style={{
                position: "absolute",
                top: "50%",
                left: "50%",
                transform: "translate(-50%, -50%)",
                width: "120px",
                height: "120px",
                borderRadius: "50%",
                background: "radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%)",
              }}
            ></div>
            <div
              style={{
                position: "absolute",
                top: "50%",
                left: "50%",
                transform: "translate(-50%, -50%)",
                width: "80px",
                height: "80px",
                backgroundColor: "#00ff88",
                borderRadius: "50%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#070a0f",
                fontWeight: 600,
                fontSize: "1.5rem",
              }}
            >
              Q
            </div>
          </div>
        </section>

        {/* Stats Grid */}
        <section
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "1.5rem",
          }}
        >
          <div
            style={{
              backgroundColor: "#f3f7f5",
              borderRadius: "8px",
              padding: "1.5rem",
              textAlign: "center",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "0.5rem" }}>
              <Gauge size={24} color="#00ff88" style={{ marginRight: "0.5rem" }} />
              <div>
                <div style={{ fontSize: "0.85rem", color: "#70808e" }}>Programme target</div>
                <div style={{ fontWeight: 600, marginTop: "0.25rem" }}>
                  {targetXp.toLocaleString()}
                </div>
                <div
                  style={{
                    fontSize: "0.85rem",
                    color: "#70808e",
                    marginTop: "0.25rem",
                  }}
                >
                  {Number(
                    programme?.weekly_target_xp ?? 0
                  ).toLocaleString()} weekly
                </div>
              </div>
            </div>
          </div>

          <div
            style={{
              backgroundColor: "#f3f7f5",
              borderRadius: "8px",
              padding: "1.5rem",
              textAlign: "center",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "0.5rem" }}>
              <Activity size={24} color="#00ff88" style={{ marginRight: "0.5rem" }} />
              <div>
                <div style={{ fontSize: "0.85rem", color: "#70808e" }}>Collective XP</div>
                <div style={{ fontWeight: 600, marginTop: "0.25rem" }}>
                  {groupXp.toLocaleString()}
                </div>
                <div
                  style={{
                    fontSize: "0.85rem",
                    color: "#70808e",
                    marginTop: "0.25rem",
                  }}
                >
                  Live from the API
                </div>
              </div>
            </div>
          </div>

          <div
            style={{
              backgroundColor: "#f3f7f5",
              borderRadius: "8px",
              padding: "1.5rem",
              textAlign: "center",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "0.5rem" }}>
              <Award size={24} color="#00ff88" style={{ marginRight: "0.5rem" }} />
              <div>
                <div style={{ fontSize: "0.85rem", color: "#70808e" }}>Active phases</div>
                <div style={{ fontWeight: 600, marginTop: "0.25rem" }}>
                  {data?.phases?.length ?? 0}
                </div>
                <div
                  style={{
                    fontSize: "0.85rem",
                    color: "#70808e",
                    marginTop: "0.25rem",
                  }}
                >
                  Programme phases
                </div>
              </div>
            </div>
          </div>

          <div
            style={{
              backgroundColor: "#f3f7f5",
              borderRadius: "8px",
              padding: "1.5rem",
              textAlign: "center",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "0.5rem" }}>
              <MapIcon size={24} color="#00ff88" style={{ marginRight: "0.5rem" }} />
              <div>
                <div style={{ fontSize: "0.85rem", color: "#70808e" }}>Map locations</div>
                <div style={{ fontWeight: 600, marginTop: "0.25rem" }}>
                  {data?.map?.locations?.length ?? 0}
                </div>
                <div
                  style={{
                    fontSize: "0.85rem",
                    color: "#70808e",
                    marginTop: "0.25rem",
                  }}
                >
                  {data?.map?.name ?? "No active map"}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Dashboard Sections: Group Progress and Weekly Risers */}
        <section
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: "1.5rem",
          }}
        >
          {/* Group Progress */}
          <div
            style={{
              backgroundColor: "#f3f7f5",
              borderRadius: "8px",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "1.25rem 1.5rem",
                backgroundColor: "#070a0f",
                color: "#ffffff",
              }}
            >
              <div>
                <h2 style={{ margin: 0, fontSize: "1.25rem" }}>GROUP PROGRESS</h2>
                <p style={{ margin: "0.25rem 0 0", fontSize: "0.9rem", opacity: 0.8 }}>
                  Team contributions to collective goal
                </p>
              </div>
            </div>
            <div style={{ padding: "1.5rem" }}>
              {data?.group_progress?.length === 0 ? (
                <p
                  style={{
                    textAlign: "center",
                    color: "#70808e",
                    fontStyle: "italic",
                  }}
                >
                  No group data available
                </p>
              ) : (
                <div>
                  {data?.group_progress?.map((group: any) => (
                    <div
                      key={group.id}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        padding: "0.75rem 0",
                        borderBottom: "1px solid #e0e0e0",
                      }}
                    >
                      <div>
                        <div
                          style={{
                            fontWeight: 600,
                            marginBottom: "0.25rem",
                          }}
                        >
                          {group.name}
                        </div>
                        <div style={{ fontSize: "0.9rem", color: "#70808e" }}>
                          {group.xp.toLocaleString()} XP
                        </div>
                      </div>
                      <div
                        style={{
                          textAlign: "right",
                          fontSize: "0.9rem",
                        }}
                      >
                        {group.progress_percentage.toFixed(1)}% of target
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Weekly Risers */}
          <div
            style={{
              backgroundColor: "#f3f7f5",
              borderRadius: "8px",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "1.25rem 1.5rem",
                backgroundColor: "#070a0f",
                color: "#ffffff",
              }}
            >
              <div>
                <h2 style={{ margin: 0, fontSize: "1.25rem" }}>WEEKLY RISERS</h2>
                <p style={{ margin: "0.25rem 0 0", fontSize: "0.9rem", opacity: 0.8 }}>
                  Top 5 XP gainers (last 7 days)
                </p>
              </div>
            </div>
            <div style={{ padding: "1.5rem" }}>
              {data?.top_5_weekly_high_riser?.length === 0 ? (
                <p
                  style={{
                    textAlign: "center",
                    color: "#70808e",
                    fontStyle: "italic",
                  }}
                >
                  No weekly riser data available
                </p>
              ) : (
                <ol
                  style={{
                    margin: 0,
                    paddingLeft: "1.5rem",
                  }}
                >
                  {data?.top_5_weekly_high_riser?.map((riser: any, index: number) => (
                    <li
                      key={riser.player_id}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        padding: "0.5rem 0",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          marginRight: "1rem",
                          flexShrink: 0,
                        }}
                      >
                        <div
                          style={{
                            width: "28px",
                            height: "28px",
                            backgroundColor: "#00ff88",
                            borderRadius: "50%",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            fontWeight: 600,
                            color: "#070a0f",
                          }}
                        >
                          #{index + 1}
                        </div>
                      </div>
                      <div
                        style={{
                          display: "flex",
                          flexDirection: "column",
                        }}
                      >
                        <div
                          style={{
                            fontWeight: 600,
                            marginBottom: "0.25rem",
                          }}
                        >
                          {riser.gamertag}
                        </div>
                        <div style={{ fontSize: "0.9rem", color: "#70808e" }}>
                          +{riser.weekly_xp.toLocaleString()} XP
                        </div>
                      </div>
                    </li>
                  ))}
                </ol>
              )}
            </div>
          </div>
        </section>

        {/* Content Grid: Programme Info and Active Phases */}
        <section
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
            gap: "1.5rem",
          }}
        >
          <div
            style={{
              backgroundColor: "#f3f7f5",
              borderRadius: "8px",
              padding: "1.5rem",
            }}
          >
            <h2 style={{ marginTop: 0, marginBottom: "1rem", fontSize: "1.25rem" }}>
              CURRENT PROGRAMME
            </h2>
            <p style={{ color: "#70808e", marginBottom: "1rem" }}>
              {programme?.description ?? "Collective progress is updated from the programme database."}
            </p>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                flexWrap: "wrap",
                gap: "1rem",
              }}
            >
              <div>
                <div style={{ fontSize: "0.85rem", color: "#70808e" }}>Programme</div>
                <div style={{ fontWeight: 600 }}>
                  {programme?.name ?? "Youth Challenge"}
                </div>
              </div>
              <div>
                <div style={{ fontSize: "0.85rem", color: "#70808e" }}>Target XP</div>
                <div style={{ fontWeight: 600 }}>
                  {targetXp.toLocaleString()}
                </div>
              </div>
              <div>
                <div style={{ fontSize: "0.85rem", color: "#70808e" }}>Weekly Target</div>
                <div style={{ fontWeight: 600 }}>
                  {Number(
                    programme?.weekly_target_xp ?? 0
                  ).toLocaleString()}
                </div>
              </div>
            </div>
          </div>

          <div
            style={{
              backgroundColor: "#f3f7f5",
              borderRadius: "8px",
              padding: "1.5rem",
            }}
          >
            <h2 style={{ marginTop: 0, marginBottom: "1rem", fontSize: "1.25rem" }}>
              ACTIVE PHASES
            </h2>
            {(data?.phases ?? []).length === 0 ? (
              <p
                style={{
                  textAlign: "center",
                  color: "#70808e",
                  fontStyle: "italic",
                }}
              >
                No active phases configured.
              </p>
            ) : (
              <div>
                {data?.phases?.map(
                  (phase: any) => (
                    <div
                      key={phase.id}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        padding: "0.75rem 0",
                        borderBottom: "1px solid #e0e0e0",
                      }}
                    >
                      <div>
                        <div
                          style={{
                            fontWeight: 600,
                            marginBottom: "0.25rem",
                          }}
                        >
                          {phase.name}
                        </div>
                        <div style={{ fontSize: "0.9rem", color: "#70808e" }}>
                          {phase.description ?? "Programme phase"}
                        </div>
                      </div>
                      <div
                        style={{
                          width: "10px",
                          height: "10px",
                          backgroundColor: "#00ff88",
                          borderRadius: "50%",
                        }}
                      />
                    </div>
                  )
                )}
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

// Keep the other components for potential use elsewhere
function PublicLeaderboard({
  data,
}: {
  data: any;
}) {
  const rows = data?.leaderboards?.overall ?? [];

  return (
    <div className="page">
      <div className="section-heading">
        <div>
          <span className="eyebrow">
            PUBLIC LEADERBOARD
          </span>

          <h2>Leaderboard</h2>

          <p>
            Public rankings use gamertags only.
          </p>
        </div>
      </div>

      <div className="panel">
        {rows.length === 0 ? (
          <div className="empty-state">
            No public leaderboard data yet.
          </div>
        ) : (
          <div className="analytics-list">
            {rows.map((row: any) => (
              <div
                className="setting-line"
                key={`${row.rank}-${row.gamertag}`}
              >
                <span>
                  <b>
                    #{row.rank} {row.gamertag}
                  </b>

                  <small
                    style={{
                      display: "block",
                      color: "#70808e",
                    }}
                  >
                    {Number(row.xp ?? 0).toLocaleString()} XP
                  </small>
                </span>

                <Trophy size={18} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function PublicMap({
  data,
}: {
  data: any;
}) {
  const map = data?.map;

  return (
    <div className="page">
      <div className="section-heading">
        <div>
          <span className="eyebrow">
            PROGRAMME MAP
          </span>

          <h2>{map?.name ?? "Programme map"}</h2>

          <p>
            Active locations configured for the
            programme.
          </p>
        </div>
      </div>

      <div className="panel">
        {!map ? (
          <div className="empty-state">
            No active map configured.
          </div>
        ) : (
          <div className="analytics-list">
            {(map.locations ?? []).map(
              (location: any) => (
                <div
                  className="setting-line"
                  key={location.id}
                >
                  <span>
                    <b>{location.name}</b>

                    <small
                      style={{
                        display: "block",
                        color: "#70808e",
                      }}
                    >
                      {location.description ??
                        "Programme location"}
                    </small>
                  </span>

                  <MapIcon size={18} />
                </div>
              )
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function PublicMilestones({
  data,
}: {
  data: any;
}) {
  const target = Number(
    data?.programme?.target_xp ?? 1500000
  );

  const milestones = [
    {
      xp: 500000,
      label: "Level 1",
    },
    {
      xp: 1000000,
      label: "Level 2",
    },
    {
      xp: target,
      label: "Grand Finale",
    },
  ];

  const current = Number(data?.group_xp ?? 0);

  return (
    <div className="page">
      <div className="section-heading">
        <div>
          <span className="eyebrow">
            PROGRAMME MILESTONES
          </span>

          <h2>Milestones</h2>

          <p>
            Collective XP progression.
          </p>
        </div>
      </div>

      <div className="panel">
        <div className="analytics-list">
          {milestones.map((milestone) => (
            <div
              className="setting-line"
              key={milestone.xp}
            >
              <span>
                <b>{milestone.label}</b>

                <small
                  style={{
                    display: "block",
                    color: "#70808e",
                  }}
                >
                  {milestone.xp.toLocaleString()} XP
                </small>
              </span>

              <span className="status">
                {current >= milestone.xp
                  ? "Unlocked"
                  : `${Math.max(
                      0,
                      milestone.xp - current
                    ).toLocaleString()} XP to go`}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}