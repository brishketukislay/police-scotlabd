//export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";
export type Role = "admin" | "youth_worker" | "player";
export type SessionUser = { id: number; username: string; role: Role };

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(init.headers || {}) },
  });
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try { const body = await res.json(); message = body.detail ?? message; } catch {}
    throw new Error(message);
  }
  return res.json();
}

export const api = {
  health: () => request<{status:string}>("/api/health"),
  me: () => request<SessionUser>("/api/auth/me"),
  login: (username: string, password: string) => request<SessionUser>("/api/auth/login", { method:"POST", body: JSON.stringify({username,password}) }),
  logout: () => request<{success:boolean}>("/api/auth/logout", { method:"POST" }),
  adminOverview: () => request<any>("/api/admin/overview"),
  staffGroups: () => request<any[]>("/api/admin/groups"),
  createStaffGroup: (body:any) => request<any>("/api/admin/groups", {
    method:"POST",
    body:JSON.stringify(body)
  }),
  updateStaffGroup: (id:number, body:any) => request<any>(`/api/admin/groups/${id}`, {
    method:"PUT",
    body:JSON.stringify(body)
  }),
  addPlayerToGroup: (groupId:number, playerId:number, confirmMove=false) =>
    request<any>(
      `/api/admin/groups/${groupId}/players/${playerId}?confirm_move=${confirmMove ? "true" : "false"}`,
      {method:"POST"}
    ),
  removePlayerFromGroup: (groupId:number, playerId:number) =>
    request<any>(
      `/api/admin/groups/${groupId}/players/${playerId}`,
      {method:"DELETE"}
    ),

  publicDashboard: () => request<any>("/api/public/dashboard"),
  playerDashboard: () => request<any>("/api/player/dashboard"),
  rewardGames: () => request<any>("/api/reward-games/player"),
  adminPlayers: () => request<any>("/api/admin/players"),
  leaderboards: () => request<any>("/api/leaderboard"),
  adminUsers: () => request<any>("/api/admin/users"),
  pointRequests: (status?: string) => request<any>(`/api/points-requests${status ? `?status=${encodeURIComponent(status)}` : ""}`),
  approvePointRequest: (id:number, body:any={}) => request<any>(`/api/points-requests/${id}/approve`, {method:"POST", body:JSON.stringify(body)}),
  createPointRequest: (body:any) => request<any>("/api/points-requests", {method:"POST", body:JSON.stringify(body)}),
  rotatePlayerQr: () => request<any>("/api/attendance/player-qr/rotate", {method:"POST"}),
  playRewardGame: (playId:number) => request<any>(`/api/reward-games/${playId}/play`, {method:"POST"}),
  awardXp: (playerId:number, amount:number, reason?:string) =>
    request<any>("/api/admin/xp/award", {
      method:"POST",
      body:JSON.stringify({
        player_id:playerId,
        amount,
        reason:reason || null
      })
    }),
  updateUser: (id:number, body:any) =>
    request<any>(`/api/admin/users/${id}`, {
      method:"PUT",
      body:JSON.stringify(body)
    }),
  createUser: (body:any) =>
    request<any>("/api/admin/users", {
      method:"POST",
      body:JSON.stringify(body)
    }),
  pauseUser: (id:number) =>
    request<any>(`/api/admin/users/${id}/pause`, {method:"POST"}),
  reactivateUser: (id:number) =>
    request<any>(`/api/admin/users/${id}/reactivate`, {method:"POST"}),
  suspendPlayer: (id:number) =>
    request<any>(`/api/admin/players/${id}/suspend`, {method:"POST"}),
  unsuspendPlayer: (id:number) =>
    request<any>(`/api/admin/players/${id}/unsuspend`, {method:"POST"}),
  analytics: () => request<any>("/api/admin/analytics"),
  economy: () => request<any>("/api/admin/economy"),
  updateEconomy: (body:any) =>
    request<any>("/api/admin/economy", {
      method:"PUT",
      body:JSON.stringify(body)
    }),
  adminRewardGames: () => request<any>("/api/reward-games/admin"),
  rewardGameTargets: () => request<any>("/api/reward-games/admin/targets"),
  createRewardGame: (body:any) =>
    request<any>("/api/reward-games/admin", {
      method:"POST",
      body:JSON.stringify(body)
    }),
  updateRewardGame: (id:number, body:any) =>
    request<any>(`/api/reward-games/admin/${id}`, {
      method:"PUT",
      body:JSON.stringify(body)
    }),
  grantRewardGame: (id:number, body:any) =>
    request<any>(`/api/reward-games/admin/${id}/grant`, {
      method:"POST",
      body:JSON.stringify(body)
    }),

  rejectPointRequest: (id:number, body:any={}) => request<any>(`/api/points-requests/${id}/reject`, {method:"POST", body:JSON.stringify(body)}),
};
