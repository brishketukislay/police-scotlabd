import type { SessionUser } from "./api";

export function getNavigation(
  user: SessionUser | null,
  isStaff: (user: SessionUser | null) => boolean,
) {

    // If we are in the public route, we don't use this nav.
    if (location.pathname === "/public") {
      return ["Home", "Leaderboard", "Map", "Milestones"];
    }
    // If we are in the dashboard route, we base it on the user role.
    if (!user) {
      // This shouldn't happen because the dashboard route redirects to login if not authenticated.
      return [];
    }
    if (user?.role === "player") {
      return ["Home", "Challenges", "Rewards", "Profile"];
    }
    if (user?.role === "admin") {
      return [
        "Dashboard",
        "Users & Groups",
        "Points & Rewards",
        "Drawing Games",
        "Points Requests",
        "Challenges",
        "Phases & Themes",
        "Community Nominations",
        "Analytics",
        "System Settings"
      ];
    }
    // For youth_worker, we can use the same as admin? Or a subset? We'll use admin for now.
    return [
      "Dashboard",
      "Users & Groups",
      "Points & Rewards",
      "Drawing Games",
      "Points Requests",
      "Challenges",
      "Phases & Themes",
      "Community Nominations",
      "Analytics",
      "System Settings"
    ];
  
}
