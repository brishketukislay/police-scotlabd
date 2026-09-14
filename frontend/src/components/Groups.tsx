import React, { useState, useEffect } from "react";
import { Users, Plus, ChevronRight } from "lucide-react";
import { api } from "../api";

function Groups({
  data,
  pushToast,
}: {
  data: any;
  pushToast: (s: string, t?: any) => void;
}) {
  const [groups, setGroups] = useState<any[]>([]);
  const [players, setPlayers] = useState<any[]>(data?.players ?? []);
  const [selected, setSelected] = useState<any>(null);
  const [name, setName] = useState("");
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);

  const load = async () => {
    try {
      const result = await api.staffGroups();
      setGroups(result);

      if (selected) {
        setSelected(
          result.find((g: any) => g.id === selected.id) ?? null
        );
      }
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

  const create = async () => {
    const clean = name.trim();

    if (clean.length < 2) {
      pushToast("Enter a group name.", "warning");
      return;
    }

    setBusy(true);

    try {
      await api.createStaffGroup({
        name: clean,
        player_ids: [],
      });

      setName("");
      pushToast("Group created");
      await load();
    } catch (e: any) {
      pushToast(e.message, "warning");
    } finally {
      setBusy(false);
    }
  };

  const save = async () => {
    if (!selected) return;

    const clean = name.trim();

    if (clean.length < 2) {
      pushToast("Enter a group name.", "warning");
      return;
    }

    setBusy(true);

    try {
      await api.updateStaffGroup(selected.id, {
        name: clean,
        active: selected.active,
      });

      pushToast("Group updated");
      setEditing(false);
      await load();
    } catch (e: any) {
      pushToast(e.message, "warning");
    } finally {
      setBusy(false);
    }
  };

  const toggle = async (group: any) => {
    try {
      await api.updateStaffGroup(group.id, {
        name: group.name,
        active: !group.active,
      });

      pushToast(
        group.active ? "Group deactivated" : "Group activated"
      );

      await load();
    } catch (e: any) {
      pushToast(e.message, "warning");
    }
  };

  const add = async (playerId: number) => {
    if (!selected) return;

    try {
      await api.addPlayerToGroup(selected.id, playerId);
      pushToast("Young person added to group");
      await load();
    } catch (e: any) {
      pushToast(e.message, "warning");
    }
  };

  const remove = async (playerId: number) => {
    if (!selected) return;

    try {
      await api.removePlayerFromGroup(selected.id, playerId);
      pushToast("Young person removed from group");
      await load();
    } catch (e: any) {
      pushToast(e.message, "warning");
    }
  };

  const members = selected?.players ?? [];

  const memberIds = new Set(
    members.map((p: any) => p.id)
  );

  const available = players.filter(
    (p: any) =>
      p.active !== false && !memberIds.has(p.id)
  );

  return (
    <div className="page">
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

            <Users size={18} />
          </div>

          <div className="form-grid">
            <label>
              Group name

              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
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
            <Plus size={16} />
            {busy ? "Creating…" : "Create group"}
          </button>
        </div>

        <div className="panel">
          <div className="panel-head">
            <div>
              <span className="eyebrow">GROUPS</span>

              <h3>
                {groups.length} group
                {groups.length === 1 ? "" : "s"}
              </h3>
            </div>

            <span className="count-pill">
              {groups.filter((g: any) => g.active).length} active
            </span>
          </div>

          {groups.length === 0 ? (
            <div className="empty-state">
              No groups have been created yet.
            </div>
          ) : (
            <div className="analytics-list">
              {groups.map((group: any) => (
                <button
                  key={group.id}
                  className="setting-line"
                  style={{
                    width: "100%",
                    textAlign: "left",
                    cursor: "pointer",
                    background:
                      selected?.id === group.id
                        ? "rgba(100,231,255,.06)"
                        : "transparent",
                    border: "0",
                    color: "inherit",
                  }}
                  onClick={() => {
                    setSelected(group);
                    setName(group.name);
                    setEditing(false);
                  }}
                >
                  <span>
                    <b>{group.name}</b>

                    <small
                      style={{
                        display: "block",
                        color: "#70808e",
                      }}
                    >
                      {group.player_count} young person
                      {group.player_count === 1 ? "" : "s"} ·{" "}
                      {group.active ? "Active" : "Inactive"}
                    </small>
                  </span>

                  <ChevronRight size={16} />
                </button>
              ))}
            </div>
          )}
        </div>

        {selected && (
          <section className="content-grid">
            <div className="panel large">
              <div className="panel-head">
                <div>
                  <span className="eyebrow">SELECTED GROUP</span>

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
                  {!editing && (
                    <button
                      className="ghost-btn"
                      onClick={() => setEditing(true)}
                    >
                      Edit
                    </button>
                  )}

                  <button
                    className="ghost-btn"
                    onClick={() => toggle(selected)}
                  >
                    {selected.active
                      ? "Deactivate"
                      : "Activate"}
                  </button>
                </div>
              </div>

              <div className="panel inset">
                <div className="panel-head">
                  <div>
                    <span className="eyebrow">MEMBERS</span>

                    <h3>
                      {members.length} young person
                      {members.length === 1 ? "" : "s"}
                    </h3>
                  </div>
                </div>

                {members.length === 0 ? (
                  <div className="empty-state">
                    No young people are currently in this group.
                  </div>
                ) : (
                  members.map((player: any) => (
                    <div
                      className="setting-line"
                      key={player.id}
                    >
                      <span>
                        <b>{player.gamertag}</b>

                        <small
                          style={{
                            display: "block",
                            color: "#70808e",
                          }}
                        >
                          {Number(
                            player.xp ?? 0
                          ).toLocaleString()}{" "}
                          XP
                        </small>
                      </span>

                      <button
                        className="ghost-btn"
                        onClick={() => remove(player.id)}
                      >
                        Remove
                      </button>
                    </div>
                  ))
                )}
              </div>

              <div className="panel">
                <div className="panel-head">
                  <div>
                    <span className="eyebrow">ADD MEMBERS</span>
                    <h3>Available young people</h3>
                  </div>

                  <Users size={18} />
                </div>

                {!selected.active ? (
                  <div className="empty-state">
                    Activate this group before adding young people.
                  </div>
                ) : available.length === 0 ? (
                  <div className="empty-state">
                    All active young people are already in this group.
                  </div>
                ) : (
                  available.map((player: any) => (
                    <div
                      className="setting-line"
                      key={player.id}
                    >
                      <span>
                        <b>{player.gamertag}</b>

                        <small
                          style={{
                            display: "block",
                            color: "#70808e",
                          }}
                        >
                          {player.group_id
                            ? `Currently in group #${player.group_id}`
                            : "No group"}
                        </small>
                      </span>

                      <button
                        className="secondary-btn"
                        onClick={() => add(player.id)}
                      >
                        Add
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          </section>
        )}
      </section>
    </div>
  );
}

export default Groups;