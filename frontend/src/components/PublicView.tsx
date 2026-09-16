import {
  Activity,
  Award,
  Gauge,
  Map as MapIcon,
  Menu,
  X,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";

type PublicViewProps = {
  data: any;
};

export default function PublicView({ data }: PublicViewProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [showControls, setShowControls] = useState(true);

  const controlsTimeoutRef = useRef<number | undefined>(undefined);
  const controlsHideDelay = 3000;

  const programme = data?.programme;
  const groupXp = Number(data?.group_xp ?? 0);
  const targetXp = Number(programme?.target_xp ?? 1500000);

  const percentage =
    targetXp > 0 ? Math.min(100, Math.max(0, (groupXp / targetXp) * 100)) : 0;

  const phases = data?.phases ?? [];
  const groupProgress = data?.group_progress ?? [];
  const weeklyRisers = data?.top_5_weekly_high_riser ?? [];
  const mapLocations = data?.map?.locations ?? [];

  const clearControlsTimeout = () => {
    if (controlsTimeoutRef.current !== undefined) {
      window.clearTimeout(controlsTimeoutRef.current);
      controlsTimeoutRef.current = undefined;
    }
  };

  const scheduleControlsHide = () => {
    clearControlsTimeout();

    if (!isFullscreen) {
      return;
    }

    controlsTimeoutRef.current = window.setTimeout(() => {
      setShowControls(false);
      controlsTimeoutRef.current = undefined;
    }, controlsHideDelay);
  };

  const toggleFullscreen = async () => {
    try {
      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen();
      } else {
        await document.exitFullscreen();
      }
    } catch (error) {
      console.error("Unable to toggle fullscreen:", error);
    }
  };

  useEffect(() => {
    const handleFullscreenChange = () => {
      const fullscreen = !!document.fullscreenElement;

      setIsFullscreen(fullscreen);

      if (!fullscreen) {
        setShowControls(true);
        clearControlsTimeout();
      } else {
        setShowControls(true);
      }
    };

    document.addEventListener("fullscreenchange", handleFullscreenChange);

    return () => {
      document.removeEventListener(
        "fullscreenchange",
        handleFullscreenChange
      );
    };
  }, []);

  const toggleSidebar = () => {
    const nextOpen = !isSidebarOpen;

    setIsSidebarOpen(nextOpen);

    window.dispatchEvent(
      new CustomEvent("toggle-public-sidebar", {
        detail: { open: nextOpen },
      })
    );
  };

  useEffect(() => {
    const handleSidebarToggle = (event: Event) => {
      const customEvent = event as CustomEvent<{ open?: boolean }>;

      if (typeof customEvent.detail?.open === "boolean") {
        setIsSidebarOpen(customEvent.detail.open);
      }
    };

    window.addEventListener(
      "toggle-public-sidebar",
      handleSidebarToggle as EventListener
    );

    return () => {
      window.removeEventListener(
        "toggle-public-sidebar",
        handleSidebarToggle as EventListener
      );
    };
  }, []);

  useEffect(() => {
    if (isFullscreen && showControls) {
      scheduleControlsHide();
    } else if (!isFullscreen) {
      setShowControls(true);
      clearControlsTimeout();
    }

    return () => {
      clearControlsTimeout();
    };
  }, [isFullscreen, showControls]);

  useEffect(() => {
    const handleMouseMove = () => {
      if (!isFullscreen) {
        return;
      }

      if (!showControls) {
        setShowControls(true);
      }

      scheduleControlsHide();
    };

    document.addEventListener("mousemove", handleMouseMove);

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      clearControlsTimeout();
    };
  }, [isFullscreen, showControls]);

  const renderStatsGrid = (large = false) => (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(2, 1fr)",
        gap: large ? "1.5rem" : "1rem",
        margin: large ? "0 2rem 2rem 2rem" : "0.5rem 0 0",
      }}
    >
      <div
        style={{
          backgroundColor: "var(--panel)",
          borderRadius: "var(--radius)",
          padding: large ? "1.5rem" : "1.25rem",
          textAlign: "center",
          border: "1px solid var(--line)",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            marginBottom: large ? "0.75rem" : "0.5rem",
          }}
        >
          <Gauge
            size={large ? 32 : 24}
            color="var(--lime)"
            style={{ marginRight: large ? "1rem" : "0.75rem" }}
          />
          <div>
            <div
              style={{
                fontSize: large ? "1.1rem" : "0.9rem",
                color: "var(--muted)",
              }}
            >
              Programme target
            </div>
            <div
              style={{
                fontWeight: 500,
                marginTop: large ? "0.5rem" : "0.3rem",
                fontSize: large ? "2rem" : "1.3rem",
              }}
            >
              {targetXp.toLocaleString()}
            </div>
          </div>
        </div>
      </div>

      <div
        style={{
          backgroundColor: "var(--panel)",
          borderRadius: "var(--radius)",
          padding: large ? "1.5rem" : "1.25rem",
          textAlign: "center",
          border: "1px solid var(--line)",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            marginBottom: large ? "0.75rem" : "0.5rem",
          }}
        >
          <Activity
            size={large ? 32 : 24}
            color="var(--lime)"
            style={{ marginRight: large ? "1rem" : "0.75rem" }}
          />
          <div>
            <div
              style={{
                fontSize: large ? "1.1rem" : "0.9rem",
                color: "var(--muted)",
              }}
            >
              Collective XP
            </div>
            <div
              style={{
                fontWeight: 500,
                marginTop: large ? "0.5rem" : "0.3rem",
                fontSize: large ? "2rem" : "1.3rem",
              }}
            >
              {groupXp.toLocaleString()}
            </div>
          </div>
        </div>
      </div>

      <div
        style={{
          backgroundColor: "var(--panel)",
          borderRadius: "var(--radius)",
          padding: large ? "1.5rem" : "1.25rem",
          textAlign: "center",
          border: "1px solid var(--line)",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            marginBottom: large ? "0.75rem" : "0.5rem",
          }}
        >
          <Award
            size={large ? 32 : 24}
            color="var(--lime)"
            style={{ marginRight: large ? "1rem" : "0.75rem" }}
          />
          <div>
            <div
              style={{
                fontSize: large ? "1.1rem" : "0.9rem",
                color: "var(--muted)",
              }}
            >
              Active phases
            </div>
            <div
              style={{
                fontWeight: 500,
                marginTop: large ? "0.5rem" : "0.3rem",
                fontSize: large ? "2rem" : "1.3rem",
              }}
            >
              {phases.length}
            </div>
          </div>
        </div>
      </div>

      <div
        style={{
          backgroundColor: "var(--panel)",
          borderRadius: "var(--radius)",
          padding: large ? "1.5rem" : "1.25rem",
          textAlign: "center",
          border: "1px solid var(--line)",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            marginBottom: large ? "0.75rem" : "0.5rem",
          }}
        >
          <MapIcon
            size={large ? 32 : 24}
            color="var(--lime)"
            style={{ marginRight: large ? "1rem" : "0.75rem" }}
          />
          <div>
            <div
              style={{
                fontSize: large ? "1.1rem" : "0.9rem",
                color: "var(--muted)",
              }}
            >
              Map locations
            </div>
            <div
              style={{
                fontWeight: 500,
                marginTop: large ? "0.5rem" : "0.3rem",
                fontSize: large ? "2rem" : "1.3rem",
              }}
            >
              {mapLocations.length}
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderHero = (large = false) => (
    <div
      style={{
        display: "flex",
        gap: large ? "2rem" : "1.5rem",
        alignItems: "flex-start",
        backgroundColor: "var(--panel)",
        borderRadius: "var(--radius)",
        padding: large ? "2rem" : "1.5rem",
        border: "1px solid var(--line)",
        ...(large ? { margin: "2rem" } : {}),
      }}
    >
      <div
        style={{
          flex: 1,
          minWidth: 0,
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            marginBottom: large ? "0.75rem" : "0.5rem",
          }}
        >
          <div
            style={{
              width: large ? "12px" : "10px",
              height: large ? "12px" : "10px",
              backgroundColor: "var(--lime)",
              borderRadius: "50%",
              marginRight: large ? "1rem" : "0.75rem",
            }}
          />

          <span
            style={{
              fontSize: large ? "1.25rem" : "1rem",
              textTransform: "uppercase",
              letterSpacing: "0.5px",
              color: "var(--lime)",
            }}
          >
            LIVE DATA
          </span>
        </div>

        <div
          style={{
            fontSize: large ? "4rem" : "2.5rem",
            fontWeight: 600,
            marginBottom: large ? "0.5rem" : "0.25rem",
          }}
        >
          {groupXp.toLocaleString()}
          <span style={{ fontSize: large ? "1.5rem" : "1.2rem" }}> XP</span>
        </div>

        <p
          style={{
            margin: 0,
            fontSize: large ? "1.75rem" : "1.1rem",
            color: "var(--muted)",
          }}
        >
          {percentage.toFixed(1)}% toward{" "}
          <span style={{ fontWeight: 500, color: "var(--text)" }}>
            {targetXp.toLocaleString()} XP target
          </span>
        </p>

        <div
          style={{
            height: large ? "14px" : "10px",
            backgroundColor: "var(--line)",
            borderRadius: large ? "7px" : "5px",
            overflow: "hidden",
            marginTop: large ? "1.5rem" : "1rem",
          }}
        >
          <div
            style={{
              width: `${percentage}%`,
              height: "100%",
              background: "linear-gradient(to right, var(--lime), var(--green))",
              transition: "width 0.3s ease",
            }}
          />
        </div>
      </div>

      <div
        style={{
          width: large ? "220px" : "160px",
          height: large ? "220px" : "160px",
          position: "relative",
          flexShrink: 0,
        }}
      >
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: large ? "180px" : "130px",
            height: large ? "180px" : "130px",
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(200,255,22,0.1) 0%, transparent 70%)",
            border: large ? "3px solid rgba(200,255,22,0.2)" : "2px solid rgba(200,255,22,0.2)",
          }}
        />

        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: large ? "140px" : "100px",
            height: large ? "140px" : "100px",
            backgroundColor: "var(--lime)",
            borderRadius: "50%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#07100a",
            fontWeight: 600,
            fontSize: large ? "2.5rem" : "2rem",
            fontFamily: "'Space Grotesk', sans-serif",
          }}
        >
          Q
        </div>
      </div>
    </div>
  );

  const renderGroupProgress = (large = false) => (
    <div
      style={{
        backgroundColor: "var(--panel)",
        borderRadius: "var(--radius)",
        border: "1px solid var(--line)",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: large ? "1.5rem 2rem" : "1rem 1.5rem",
          backgroundColor: "var(--line)",
          color: "var(--lime)",
        }}
      >
        <h2
          style={{
            margin: 0,
            fontSize: large ? "2rem" : "1.3rem",
            fontWeight: 600,
          }}
        >
          GROUP PROGRESS
        </h2>
      </div>

      <div
        style={{
          padding: large ? "1.5rem 2rem" : "1rem 1.5rem",
          maxHeight: large ? "250px" : "180px",
          overflowY: "auto",
        }}
      >
        {groupProgress.length === 0 ? (
          <p
            style={{
              textAlign: "center",
              color: "var(--muted)",
              fontStyle: "italic",
              fontSize: large ? "1.5rem" : "1rem",
            }}
          >
            No group data available
          </p>
        ) : (
          groupProgress.slice(0, large ? 6 : 4).map((group: any) => (
            <div
              key={group.id}
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: large ? "1rem 0" : "0.75rem 0",
                borderBottom: "1px solid var(--line)",
              }}
            >
              <div>
                <div
                  style={{
                    fontWeight: 500,
                    marginBottom: large ? "0.5rem" : "0.25rem",
                    fontSize: large ? "1.75rem" : "1.1rem",
                  }}
                >
                  {group.name}
                </div>

                <div
                  style={{
                    fontSize: large ? "1.5rem" : "1rem",
                    color: "var(--muted)",
                  }}
                >
                  {Number(group.xp ?? 0).toLocaleString()} XP
                </div>
              </div>

              <div
                style={{
                  textAlign: "right",
                  fontSize: large ? "1.5rem" : "1rem",
                }}
              >
                {Number(group.progress_percentage ?? 0).toFixed(1)}% of target
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );

  const renderWeeklyRisers = (large = false) => (
    <div
      style={{
        backgroundColor: "var(--panel)",
        borderRadius: "var(--radius)",
        border: "1px solid var(--line)",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: large ? "1.5rem 2rem" : "1rem 1.5rem",
          backgroundColor: "var(--line)",
          color: "var(--lime)",
        }}
      >
        <h2
          style={{
            margin: 0,
            fontSize: large ? "2rem" : "1.3rem",
            fontWeight: 600,
          }}
        >
          WEEKLY RISERS
        </h2>
      </div>

      <div
        style={{
          padding: large ? "1.5rem 2rem" : "1rem 1.5rem",
          maxHeight: large ? "250px" : "180px",
          overflowY: "auto",
        }}
      >
        {weeklyRisers.length === 0 ? (
          <p
            style={{
              textAlign: "center",
              color: "var(--muted)",
              fontStyle: "italic",
              fontSize: large ? "1.5rem" : "1rem",
            }}
          >
            No weekly riser data available
          </p>
        ) : (
          weeklyRisers.slice(0, large ? 6 : 4).map((riser: any, index: number) => (
            <div
              key={riser.player_id ?? `${riser.gamertag}-${index}`}
              style={{
                display: "flex",
                alignItems: "center",
                padding: large ? "1rem 0" : "0.75rem 0",
                borderBottom: "1px solid var(--line)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  marginRight: large ? "2rem" : "1.5rem",
                  flexShrink: 0,
                }}
              >
                <div
                  style={{
                    width: large ? "36px" : "28px",
                    height: large ? "36px" : "28px",
                    backgroundColor: "var(--lime)",
                    borderRadius: "50%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 600,
                    color: "#07100a",
                    fontFamily: "'Space Grotesk', sans-serif",
                    fontSize: large ? "0.9rem" : "0.75rem",
                  }}
                >
                  #{index + 1}
                </div>
              </div>

              <div>
                <div
                  style={{
                    fontWeight: 500,
                    marginBottom: large ? "0.5rem" : "0.25rem",
                    fontSize: large ? "1.75rem" : "1.1rem",
                  }}
                >
                  {riser.gamertag ?? "Unknown player"}
                </div>

                <div
                  style={{
                    fontSize: large ? "1.5rem" : "1rem",
                    color: "var(--muted)",
                  }}
                >
                  +{Number(riser.weekly_xp ?? 0).toLocaleString()} XP
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );

  const renderProgrammeInfo = (large = false) => (
    <div
      style={{
        backgroundColor: "var(--panel)",
        borderRadius: "var(--radius)",
        border: "1px solid var(--line)",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: large ? "1.5rem 2rem" : "1rem 1.5rem",
          backgroundColor: "var(--line)",
          color: "var(--lime)",
        }}
      >
        <h2
          style={{
            margin: 0,
            fontSize: large ? "2rem" : "1.3rem",
            fontWeight: 600,
          }}
        >
          CURRENT PROGRAMME
        </h2>
      </div>

      <div style={{ padding: large ? "1.5rem 2rem" : "1rem 1.5rem" }}>
        <p
          style={{
            margin: large ? "0 0 1rem 0" : "0 0 0.75rem 0",
            fontSize: large ? "1.5rem" : "1rem",
            color: "var(--muted)",
          }}
        >
          {programme?.description ??
            "Collective progress is updated from the programme database."}
        </p>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            fontSize: large ? "1.75rem" : "1.1rem",
            gap: "1rem",
            flexWrap: "wrap",
          }}
        >
          <div>
            <span style={{ fontWeight: 500 }}>Programme:</span>{" "}
            <span>{programme?.name ?? "Youth Challenge"}</span>
          </div>

          <div>
            <span style={{ fontWeight: 500 }}>Target:</span>{" "}
            <span>{targetXp.toLocaleString()} XP</span>
          </div>
        </div>
      </div>
    </div>
  );

  const renderActivePhases = (large = false) => (
    <div
      style={{
        backgroundColor: "var(--panel)",
        borderRadius: "var(--radius)",
        border: "1px solid var(--line)",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: large ? "1.5rem 2rem" : "1rem 1.5rem",
          backgroundColor: "var(--line)",
          color: "var(--lime)",
        }}
      >
        <h2
          style={{
            margin: 0,
            fontSize: large ? "2rem" : "1.3rem",
            fontWeight: 600,
          }}
        >
          ACTIVE PHASES
        </h2>
      </div>

      <div
        style={{
          padding: large ? "1.5rem 2rem" : "1rem 1.5rem",
          maxHeight: large ? "180px" : "120px",
          overflowY: "auto",
        }}
      >
        {phases.length === 0 ? (
          <p
            style={{
              textAlign: "center",
              color: "var(--muted)",
              fontStyle: "italic",
              fontSize: large ? "1.5rem" : "1rem",
            }}
          >
            No active phases configured.
          </p>
        ) : (
          <div>
            {phases.slice(0, large ? 6 : 4).map((phase: any) => (
              <div
                key={phase.id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: large ? "0.75rem 0" : "0.5rem 0",
                  borderBottom: "1px solid var(--line)",
                }}
              >
                <div
                  style={{
                    fontWeight: 500,
                    fontSize: large ? "1.75rem" : "1.1rem",
                  }}
                >
                  {phase.name}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div
      style={{
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        backgroundColor: "var(--bg)",
        color: "var(--text)",
        fontFamily: "Inter, system-ui, sans-serif",
        overflow: "hidden",
        position: "relative",
      }}
    >
      {/* Header */}
      {!isFullscreen || showControls ? (
        <header
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "1.5rem 2rem",
            backgroundColor: "var(--panel)",
            borderBottom: "2px solid var(--line)",
            position: "relative",
            flexShrink: 0,
            zIndex: 100,
          }}
        >
          <div>
            <h1
              style={{
                margin: 0,
                fontSize: "2.2rem",
                fontWeight: 600,
                letterSpacing: "-0.5px",
              }}
            >
              QuestHub Public Display
            </h1>

            <p
              style={{
                margin: "0.5rem 0 0",
                fontSize: "1.1rem",
                opacity: 0.9,
                color: "var(--muted)",
              }}
            >
              Community Progress Dashboard
            </p>
          </div>

          <div
            style={{
              display: "flex",
              gap: "1rem",
              alignItems: "center",
            }}
          >
            <button
              onClick={toggleSidebar}
              type="button"
              style={{
                backgroundColor: isSidebarOpen
                  ? "var(--line)"
                  : "transparent",
                color: isSidebarOpen ? "var(--lime)" : "var(--text)",
                border: "1px solid var(--line)",
                borderRadius: "var(--radius)",
                padding: "0.75rem 1.5rem",
                cursor: "pointer",
                fontWeight: 500,
                fontSize: "1rem",
                transition: "all 0.3s ease",
                fontFamily: "Inter, system-ui, sans-serif",
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
              }}
            >
              <Menu size={20} />
              <span>{isSidebarOpen ? "‹ Menu" : "Menu ›"}</span>
            </button>

            <button
              onClick={toggleFullscreen}
              type="button"
              style={{
                backgroundColor: isFullscreen
                  ? "var(--line)"
                  : "transparent",
                color: isFullscreen ? "var(--lime)" : "var(--text)",
                border: "1px solid var(--line)",
                borderRadius: "var(--radius)",
                padding: "0.75rem 1.5rem",
                cursor: "pointer",
                fontWeight: 500,
                fontSize: "1rem",
                transition: "all 0.3s ease",
                marginLeft: "0.5rem",
                fontFamily: "Inter, system-ui, sans-serif",
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
              }}
            >
              {isFullscreen ? <X size={20} /> : <Menu size={20} />}
              <span>{isFullscreen ? "Exit Full" : "Fullscreen"}</span>
            </button>
          </div>
        </header>
      ) : (
        <div
          style={{
            padding: "1.5rem 2rem",
            backgroundColor: "var(--panel)",
            borderBottom: "2px solid var(--line)",
            position: "relative",
            flexShrink: 0,
            zIndex: 100,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <div
            className="brand-mark"
            style={{
              width: "35px",
              height: "35px",
              borderRadius: "10px",
              backgroundColor: "var(--lime)",
              color: "#07100a",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: "900",
              fontFamily: "'Space Grotesk', sans-serif",
            }}
          >
            Q
          </div>
        </div>
      )}

      {/* Main Content */}
      <main
        style={{
          flex: 1,
          display:
            isFullscreen && !showControls ? "block" : "grid",
          gridTemplateColumns:
            isFullscreen && !showControls
              ? "1fr"
              : "repeat(12, 1fr)",
          gap: isFullscreen && !showControls ? "0" : "1rem",
          padding: isFullscreen && !showControls ? "0" : "1.5rem",
          overflowY: "auto",
          position: "relative",
        }}
      >
        {!isFullscreen || showControls ? (
          <>
            {/* Left Column */}
            <section
              style={{
                gridColumn: "span 6",
                display: "flex",
                flexDirection: "column",
                gap: "1rem",
              }}
            >
              {renderHero(false)}
              {renderStatsGrid(false)}
            </section>

            {/* Right Column */}
            <section
              style={{
                gridColumn: "span 6",
                display: "flex",
                flexDirection: "column",
                gap: "1rem",
              }}
            >
              {renderGroupProgress(false)}
              {renderWeeklyRisers(false)}
              {renderProgrammeInfo(false)}
              {renderActivePhases(false)}
            </section>
          </>
        ) : (
          /* Fullscreen with controls hidden */
          <div
            style={{
              width: "100%",
              display: "flex",
              flexDirection: "column",
            }}
          >
            {renderHero(true)}
            {renderStatsGrid(true)}

            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "1.5rem",
                margin: "0 2rem 2rem 2rem",
              }}
            >
              {renderGroupProgress(true)}
              {renderWeeklyRisers(true)}
              {renderProgrammeInfo(true)}
              {renderActivePhases(true)}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
