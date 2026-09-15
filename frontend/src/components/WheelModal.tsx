import React, { useEffect, useRef, useState } from "react";
import Modal from "./Modal";
import { api } from "../api";

type WheelModalProps = {
  data: any;
  onClose: () => void;
  pushToast: (s: string, t?: any) => void;
};

export default function WheelModal({ data, onClose, pushToast }: WheelModalProps) {
  const wheelRef = useRef<HTMLDivElement>(null);
  const [spinning, setSpinning] = useState(false);
  const [selectedPrize, setSelectedPrize] = useState<number | null>(null);
  const [showWinPopup, setShowWinPopup] = useState(false);
  const [winAmount, setWinAmount] = useState(0);

  // Extract games array from data object
  const games = data?.available ?? [];

  // Calculate wheel segments based on number of games
  useEffect(() => {
    if (!games || games.length === 0) return;

    // Set CSS variable for wheel segment count (based on number of games)
    const wheelElement = wheelRef.current;
    if (wheelElement) {
      wheelElement.style.setProperty('--wheel-count', games.length.toString());
    }
  }, [games]);

  // Handle spin completion via transitionend event
  useEffect(() => {
    const handleTransitionEnd = (event: TransitionEvent) => {
      // Only listen for transitions on the wheel element itself
      if (event.target === wheelRef.current && event.propertyName === 'transform') {
        setSpinning(false);
      }
    };

    const wheelElement = wheelRef.current;
    if (wheelElement) {
      wheelElement.addEventListener('transitionend', handleTransitionEnd);
    }

    return () => {
      if (wheelElement) {
        wheelElement.removeEventListener('transitionend', handleTransitionEnd);
      }
    };
  }, []);

  const handleSpin = async () => {
    if (!games || games.length === 0 || spinning) {
      return;
    }

    try {
      setSpinning(true);

      // Find all available wheel games
      const wheelGames = games.filter((game: any) => game.game_type === 'wheel');

      if (wheelGames.length === 0) {
        pushToast("No wheel games available", "warning");
        setSpinning(false);
        return;
      }

      // Try each wheel game until one works
      let lastError = null;
      for (const wheelGame of wheelGames) {
        try {
          // Call the API to play a wheel game
          // Use play_id instead of id as it appears to be the correct identifier for gameplay
          const result = await api.playRewardGame(wheelGame.play_id);
          const awardAmount = result.awarded_xp ?? 0;

          setSelectedPrize(awardAmount);
          setWinAmount(awardAmount);
          setShowWinPopup(true);

          // Show success toast
          pushToast(`🎉 You won ${awardAmount} XP!`, "success");
          return; // Success, exit the function
        } catch (error: any) {
          lastError = error;
          // Check if this is an "already played" error (safely)
          const isAlreadyPlayed =
            (error.response &&
             error.response.data &&
             error.response.data.detail &&
             error.response.data.detail.includes('already played')) ||
            (error.message &&
             error.message.includes('already played'));

          // If it's not an "already played" error, don't try other games
          if (!isAlreadyPlayed) {
            throw error;
          }
          // Otherwise, continue to try the next game
        }
      }

      // If we got here, all games failed
      if (lastError) {
        // Check if it's an "already played" error for all games (safely)
        const isAllAlreadyPlayed =
          (lastError.response &&
           lastError.response.data &&
           lastError.response.data.detail &&
           lastError.response.data.detail.includes('already played')) ||
          (lastError.message &&
           lastError.message.includes('already played'));

        if (isAllAlreadyPlayed) {
          pushToast("All wheel games have already been played. Try again later!", "warning");
        } else {
          pushToast(lastError.message || "Failed to spin the wheel", "warning");
        }
      } else {
        pushToast("No wheel games available", "warning");
      }
    } catch (error: any) {
      pushToast(error.message || "Failed to spin the wheel", "warning");
    } finally {
      setSpinning(false);
    }
  };

  const handleWinPopupClose = () => {
    setShowWinPopup(false);
  };

  return (
    <Modal title="Spin the Wheel" onClose={onClose}>
      <div className="wheel-wrap">
        {/* Enhanced wheel pointer */}
        <div className="wheel-pointer">
          <div className="pointer-triangle"></div>
          <div className="pointer-base"></div>
        </div>
        <div
          ref={wheelRef}
          className={`wheel ${spinning ? 'wheel-spinning' : ''}`}
          onClick={handleSpin}
          style={{
            cursor: spinning ? 'default' : 'pointer'
          }}
        >
          <div className="wheel-segments"
            style={ {
              '--wheel-count': games.length
            } as any }
          >
            {games.map((game: any, index: number) => (
              <div
                key={game.id}
                className="wheel-segment"
                style={ {
                  '--rotation': ((360 / games.length) * index).toString()
                } as any }
              >
                <div className="wheel-reward-label"
                  style={ {
                    '--label-angle': ((360 / games.length) * index + 90).toString()
                  } as any }
                >
                  {/* Enhanced segment content */}
                  <div className="segment-content">
                    <div className="segment-icon">🎯</div>
                    <div className="segment-text">{game.name}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          {/* Enhanced wheel core */}
          <div className="wheel-core">
            {spinning ? (
              <div className="core-content spinning">
                <div className="core-icon">⚡</div>
                <div className="core-text">SPINNING</div>
              </div>
            ) : (
              <div className="core-content">
                <div className="core-icon">🌀</div>
                <div className="core-text">SPIN</div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Enhanced Win Popup - Flash Card Style */}
      {showWinPopup && (
        <div className="win-popup-overlay" onClick={handleWinPopupClose}>
          <div className="win-popup-card win-popup-card--flash">
            <div className="win-popup-header">
              <div className="win-popup-icon">🎉</div>
              <h2 className="win-popup-title">Congratulations!</h2>
            </div>
            <div className="win-popup-body">
              <div className="win-popup-amount">{winAmount}</div>
              <div className="win-popup-unit">XP</div>
              <div className="win-popup-description">You won bonus XP!</div>
              {/* Additional flashy elements */}
              <div className="win-popup-sparkles">
                <span className="sparkle">✨</span>
                <span className="sparkle">🌟</span>
                <span className="sparkle">✨</span>
                <span className="sparkle">💫</span>
                <span className="sparkle">✨</span>
              </div>
            </div>
            <div className="win-popup-footer">
              <button className="win-popup-button win-popup-button--glow" onClick={handleWinPopupClose}>
                Claim Reward
              </button>
            </div>
          </div>
        </div>
      )}

      {!selectedPrize && (
        <div className="modal-note">
          Spin the wheel to win bonus XP! Each segment represents a different reward game.
        </div>
      )}
      <div className="modal-actions">
        <button className="primary-btn" onClick={onClose}>
          Close
        </button>
      </div>
    </Modal>
  );
}