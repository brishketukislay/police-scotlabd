import React from "react";
import { Award, Plus, Sparkles, Settings } from "lucide-react";

type PointsProps = {
  openAward: () => void;
  pushToast: (s: string, t?: any) => void;
  openEconomy: () => void;
  openRewards: () => void;
};

export default function Points({ openAward, pushToast, openEconomy, openRewards }: PointsProps) {
  return (
    <div className="page">
      <div className="section-heading">
        <div>
          <span className="eyebrow">POINTS & REWARDS</span>
          <h2>Points & Rewards</h2>
          <p>Manage XP awards, reward games, and economy settings.</p>
        </div>
      </div>

      <div className="content-grid">
        <div className="panel">
          <div className="panel-head">
            <div>
              <span className="eyebrow">AWARD XP</span>
              <h3>Recognise achievement</h3>
            </div>

            <Award size={18} />
          </div>

          <button
            className="primary-btn wide"
            onClick={openAward}
          >
            <Plus size={16} />
            Award XP to a player
          </button>
        </div>

        <div className="panel">
          <div className="panel-head">
            <div>
              <span className="eyebrow">REWARD GAMES</span>
              <h3>Configure bonus opportunities</h3>
            </div>

            <Sparkles size={18} />
          </div>

          <button
            className="primary-btn wide"
            onClick={openRewards}
          >
            <Plus size={16} />
            Manage reward games
          </button>
        </div>

        <div className="panel">
          <div className="panel-head">
            <div>
              <span className="eyebrow">ECONOMY SETTINGS</span>
              <h3>Adjust programme parameters</h3>
            </div>

            <Settings size={18} />
          </div>

          <button
            className="primary-btn wide"
            onClick={openEconomy}
          >
            <Plus size={16} />
            Adjust economy
          </button>
        </div>
      </div>
    </div>
  );
}
