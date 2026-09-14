import React from "react";
import Modal from "./Modal";

type WheelModalProps = {
  data: any;
  onClose: () => void;
  pushToast: (s: string, t?: any) => void;
};

export default function WheelModal({ data, onClose, pushToast }: WheelModalProps) {
  return (
    <Modal title="Spin the Wheel" onClose={onClose}>
      <div className="wheel-wrap">
        <div className="wheel-pointer">▲</div>
        <div className="wheel">
          {/* Wheel segments placeholder */}
          {data?.map((game: any, index: number) => (
            <div
              key={game.id}
              className="wheel-segment"
              style={{
                transform: `rotate(${(360 / data.length) * index}deg)`,
              }}
            >
              <div className="wheel-segment-label">
                <span>{game.name}</span>
              </div>
            </div>
          ))}
        </div>
        <div className="wheel-core">
          SPIN
        </div>
      </div>
      <div className="modal-note">
        Spin the wheel to win bonus XP! Each segment represents a different reward game.
      </div>
      <div className="modal-actions">
        <button className="primary-btn" onClick={onClose}>
          Close
        </button>
      </div>
    </Modal>
  );
}
