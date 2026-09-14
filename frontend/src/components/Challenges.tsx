import React from "react";
import { Trophy } from "lucide-react";

type ChallengesProps = {
  openWheel: () => void;
  pushToast: (s: string, t?: any) => void;
};

export default function Challenges({ openWheel, pushToast }: ChallengesProps) {
  return (
    <div className="page">
      <div className="section-heading">
        <div>
          <span className="eyebrow">CHALLENGES</span>
          <h2>Challenges</h2>
          <p>Complete challenges to earn bonus XP and rewards.</p>
        </div>
      </div>

      <div className="content-grid">
        <div className="panel">
          <div className="panel-head">
            <div>
              <span className="eyebrow">CURRENT CHALLENGES</span>
              <h3>Active objectives</h3>
            </div>
          </div>

          {/* Placeholder for challenges list */}
          <div className="analytics-list">
            <div className="setting-line">
              <span>
                <b>Weekly Attendance</b>
                <small>Attend 3 sessions this week</small>
              </span>
              <strong>+500 XP</strong>
            </div>
            <div className="setting-line">
              <span>
                <b>Skill Builder</b>
                <small>Complete a skill module</small>
              </span>
              <strong>+300 XP</strong>
            </div>
            <div className="setting-line">
              <span>
                <b>Community Helper</b>
                <small>Help a fellow participant</small>
              </span>
              <strong>+400 XP</strong>
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-head">
            <div>
              <span className="eyebrow">REWARD SPIN</span>
              <h3>Try your luck</h3>
            </div>
          </div>

          <div className="wheel-wrap" style={{ width: 200, height: 200, margin: "0 auto" }}>
            <div className="wheel-pointer" style={{ position: "absolute", top: "-10px", left: "50%", transform: "translateX(-50%)" }}>
              ▲
            </div>
            <div className="wheel" style={{ width: 180, height: 180, position: "relative" }}>
              {/* Simple wheel with three segments */}
              <div className="wheel-segment" style={{ transform: "rotate(0deg)" }}>
                <div className="wheel-segment-label">
                  <span>+100 XP</span>
                </div>
              </div>
              <div className="wheel-segment" style={{ transform: "rotate(120deg)" }}>
                <div className="wheel-segment-label">
                  <span>+300 XP</span>
                </div>
              </div>
              <div className="wheel-segment" style={{ transform: "rotate(240deg)" }}>
                <div className="wheel-segment-label">
                  <span>+500 XP</span>
                </div>
              </div>
            </div>
            <div className="wheel-core">
              SPIN
            </div>
          </div>

          <div className="modal-note" style={{ textAlign: "center", marginTop: "16px" }}>
            Spin the wheel to win a random challenge reward.
          </div>

          <button
            className="primary-btn wide"
            onClick={openWheel}
          >
            <Trophy size={16} />
            Spin the Wheel
          </button>
        </div>
      </div>
    </div>
  );
}
