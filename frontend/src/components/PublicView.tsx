import {
  Activity,
  Award,
  Gauge,
  Map as MapIcon,
  Trophy,
} from "lucide-react";

type PublicViewProps = {
  data: any;
  section: string;
};

export default function PublicView({
  data,
  section,
}: PublicViewProps) {
  const programme = data?.programme;
  const groupXp = Number(data?.group_xp ?? 0);
  const targetXp = Number(programme?.target_xp ?? 1500000);

  const percentage =
    targetXp > 0
      ? Math.min(100, (groupXp / targetXp) * 100)
      : 0;

  if (section === "Leaderboard") {
    return <PublicLeaderboard data={data} />;
  }

  if (section === "Map") {
    return <PublicMap data={data} />;
  }

  if (section === "Milestones") {
    return <PublicMilestones data={data} />;
  }

  return (
    <div className="page">
      <div className="section-heading">
        <div>
          <span className="eyebrow">
            PUBLIC DASHBOARD
          </span>

          <h2>Community progress</h2>

          <p>
            Collective progress and programme activity.
          </p>
        </div>
      </div>

      <section className="hero-grid">
        <div className="hero-card">
          <div className="hero-copy">
            <div className="badge-line">
              <span className="live-dot" />
              LIVE DATA
            </div>

            <h2>
              {groupXp.toLocaleString()}{" "}
              <span>XP</span>
            </h2>

            <p>
              {percentage.toFixed(1)}% toward the{" "}
              <b>
                {targetXp.toLocaleString()} XP
                target
              </b>
            </p>

            <div className="progress">
              <i
                style={{
                  width: `${percentage}%`,
                }}
              />
            </div>

            <div className="milestones">
              <span>
                <b>500K</b>
                <small>Level 1</small>
              </span>

              <span>
                <b>1M</b>
                <small>Level 2</small>
              </span>

              <span>
                <b>1.5M</b>
                <small>Finale</small>
              </span>
            </div>
          </div>

          <div className="hero-visual">
            <div className="orbit orbit-1" />
            <div className="orbit orbit-2" />
            <div className="trophy">
              <Trophy size={42} />
            </div>
          </div>
        </div>

        <section className="stats-grid">
          <div className="stat">
            <div className="stat-icon">
              <Gauge />
            </div>

            <div>
              <span>Programme target</span>

              <strong>
                {targetXp.toLocaleString()}
              </strong>

              <small>
                {Number(
                  programme?.weekly_target_xp ?? 0
                ).toLocaleString()}{" "}
                weekly
              </small>
            </div>
          </div>

          <div className="stat">
            <div className="stat-icon">
              <Activity />
            </div>

            <div>
              <span>Collective XP</span>

              <strong>
                {groupXp.toLocaleString()}
              </strong>

              <small>Live from the API</small>
            </div>
          </div>

          <div className="stat">
            <div className="stat-icon">
              <Award />
            </div>

            <div>
              <span>Active phases</span>

              <strong>
                {data?.phases?.length ?? 0}
              </strong>

              <small>Programme phases</small>
            </div>
          </div>

          <div className="stat">
            <div className="stat-icon">
              <MapIcon />
            </div>

            <div>
              <span>Map locations</span>

              <strong>
                {data?.map?.locations?.length ?? 0}
              </strong>

              <small>
                {data?.map?.name ?? "No active map"}
              </small>
            </div>
          </div>
        </section>
      </section>

      <section className="content-grid">
        <div className="panel large">
          <div className="panel-head">
            <div>
              <span className="eyebrow">
                CURRENT PROGRAMME
              </span>

              <h3>
                {programme?.name ??
                  "Youth Challenge"}
              </h3>
            </div>
          </div>

          <p className="muted">
            {programme?.description ??
              "Collective progress is updated from the programme database."}
          </p>
        </div>

        <div className="panel">
          <div className="panel-head">
            <div>
              <span className="eyebrow">
                ACTIVE PHASES
              </span>

              <h3>Programme activity</h3>
            </div>
          </div>

          {(data?.phases ?? []).length === 0 ? (
            <div className="empty-state">
              No active phases configured.
            </div>
          ) : (
            <div className="analytics-list">
              {(data?.phases ?? []).map(
                (phase: any) => (
                  <div
                    className="setting-line"
                    key={phase.id}
                  >
                    <span>
                      <b>{phase.name}</b>

                      <small
                        style={{
                          display: "block",
                          color: "#70808e",
                        }}
                      >
                        {phase.description ??
                          "Programme phase"}
                      </small>
                    </span>

                    <span className="status">
                      Active
                    </span>
                  </div>
                )
              )}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

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
