import React, { useState, useEffect } from "react";
import { Users, Plus, ChevronRight } from "lucide-react";
import { api } from "../api";

type PlayersProps = {
  data: any;
  setSelectedPlayer: (p: any) => void;
  openAward: () => void;
  openUsers: () => void;
  pushToast: (s: string, t?: any) => void;
  refresh: () => Promise<void>;
};

export default function Players({ data, setSelectedPlayer, openAward, openUsers, pushToast, refresh }: PlayersProps) {
  const [players, setPlayers] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [name, setName] = useState("");
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);

  const load = async () => {
    try {
      const result = await api.adminPlayers();
      setPlayers(result);
    } catch (e: any) {
      pushToast(e.message, "warning");
    }
  };

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    setPlayers(data?.players ?? []);
  }, [data?.players]);

  const save = async () => {
    if (!selected) return;

    const clean = name.trim();

    if (clean.length < 2) {
      pushToast("Enter a name.", "warning");
      return;
    }

    setBusy(true);

    try {
      await api.updateUser(selected.id, {
        display_name: clean,
      });

      pushToast("Player updated");
      setEditing(false);
      await load();
    } catch (e: any) {
      pushToast(e.message, "warning");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page">
      <div className="section-heading">
        <div>
          <span className="eyebrow">PLAYER MANAGEMENT</span>
          <h2>Players</h2>
          <p>View and manage young people in the programme.</p>
        </div>
      </div>

      <section className="content-grid">
        <div className="panel">
          <div className="panel-head">
            <div>
              <span className="eyebrow">PLAYER LIST</span>
              <h3>All participants</h3>
            </div>

            <Users size={18} />
          </div>

          {players.length === 0 ? (
            <div className="empty-state">
              No player data available.
            </div>
          ) : (
            <div className="analytics-list">
              {players.map((player: any) => (
                <div
                  key={player.id}
                  className="setting-line"
                  style={{
                    width: "100%",
                    textAlign: "left",
                    cursor: "pointer",
                    background:
                      selected?.id === player.id
                        ? "rgba(100,231,255,.06)"
                        : "transparent",
                  }}
                  onClick={() => {
                    setSelected(player);
                    setSelectedPlayer(player);
                    setName(player.display_name ?? player.gamertag ?? "");
                    setEditing(false);
                  }}
                >
                  <span>
                    <b>{player.gamertag}</b>

                    <small
                      style={{
                        display: "block",
                        color: "#70808e",
                      }}
                    >
                      {Number(player.xp ?? 0).toLocaleString()} XP ·
                      {player.status ?? "Active"}
                    </small>
                  </span>

                  <ChevronRight size={16} />
                </div>
              ))}
            </div>
          )}
        </div>

        {selected && (
          <section className="content-grid">
            <div className="panel large">
              <div className="panel-head">
                <div>
                  <span className="eyebrow">SELECTED PLAYER</span>

                  {editing ? (
                    <div
                      style={{
                        display: "flex",
                        gap: 8,
                        alignItems: "center",
                      }}
                    >
                      <input
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        style={{ maxWidth: 280 }}
                      />

                      <button
                        className="primary-btn"
                        onClick={save}
                        disabled={busy}
                      >
                        Save
                      </button>

                      <button
                        className="ghost-btn"
                        onClick={() => {
                          setEditing(false);
                          setName(selected.display_name ?? selected.gamertag ?? "");
                        }}
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <h3>{selected.display_name ?? selected.gamertag}</h3>
                  )}
                </div>

                <div className="nom-actions">
                  <button
                    className="primary-btn"
                    onClick={openAward}
                  >
                    <Plus size={16} />
                    Award XP
                  </button>

                  <button
                    className="ghost-btn"
                    onClick={openUsers}
                  >
                    <Users size={16} />
                    Manage Users
                  </button>
                </div>
              </div>
            </div>
          </section>
        )}
      </section>
    </div>
  );
}
