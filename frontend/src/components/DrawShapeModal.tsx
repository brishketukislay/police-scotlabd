import React, { useEffect, useRef, useState } from "react";
import Modal from "./Modal";
import { api } from "../api";

type DrawShapeModalProps = {
  assignment: { // object with assignment_id, game details
    assignment_id: number;
    name: string;
    description: string | null;
    shape: string;
    config: { timeLimit?: number };
  };
  onClose: () => void;
  pushToast: (s: string, t?: any) => void;
};

export default function DrawShapeModal({ assignment, onClose, pushToast }: DrawShapeModalProps) {
  type Point = { x: number; y: number };
  type Result = { accuracy: number; awardedXp: number } | null;

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [points, setPoints] = useState<Point[]>([]);
  const [timeLeft, setTimeLeft] = useState<number>(assignment.config.timeLimit ?? 30);
  const [timerActive, setTimerActive] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [result, setResult] = useState<Result>(null);

  // Start the timer when the modal opens
  useEffect(() => {
    if (assignment) {
      setTimeLeft(assignment.config.timeLimit ?? 30);
      setTimerActive(true);
    }
  }, [assignment]);

  // Timer tick
  useEffect(() => {
    if (timerActive && timeLeft > 0) {
      const timer = setTimeout(() => {
        setTimeLeft(prev => prev - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else if (timeLeft === 0 && timerActive) {
      // Time's up, auto-submit
      handleSubmit();
    }
  }, [timerActive, timeLeft]);

  // Handle canvas drawing
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current) return;
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    setPoints(prev => [...prev, { x, y }]);
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current) return;
    // Only draw if mouse is pressed
    if (e.buttons === 1) {
      const canvas = canvasRef.current;
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      setPoints(prev => [...prev, { x, y }]);
    }
  };

  const handleMouseUp = (_e: React.MouseEvent<HTMLCanvasElement>) => {
    // Optionally, we could add a point on mouse up, but we already capture on move
  };

  const clearCanvas = () => {
    setPoints([]);
  };

  const handleSubmit = async () => {
    if (submitting) return;
    if (points.length < 8) {
      pushToast("Please draw the shape with at least 8 points", "warning");
      return;
    }

    setSubmitting(true);
    try {
      // Normalize points to 0-1 range based on canvas size
      const canvas = canvasRef.current;
      if (!canvas) throw new Error("Canvas not available");
      const { width, height } = canvas.getBoundingClientRect();

      const normalizedPoints = points.map(p => ({
        x: p.x / width,
        y: p.y / height
      }));

      const response = await api.submitDrawingAttempt(
        assignment.assignment_id,
        { points: normalizedPoints }
      );

      if (response.success) {
        setResult({
          accuracy: response.accuracy_percent,
          awardedXp: response.awarded_xp
        });
        pushToast(`🎯 You scored ${response.accuracy_percent.toFixed(2)}% accuracy and earned ${response.awarded_xp} XP!`, "success");
      } else {
        pushToast("Failed to submit attempt", "error");
      }
    } catch (err: any) {
      pushToast(err.message || "Failed to submit attempt", "error");
    } finally {
      setSubmitting(false);
      setTimerActive(false); // Stop timer
    }
  };

  // Render the drawing on the canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Set drawing style
    ctx.strokeStyle = '#3b82f6'; // blue-500
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    // Draw points
    if (points.length > 0) {
      ctx.beginPath();
      ctx.moveTo(points[0].x, points[0].y);
      for (let i = 1; i < points.length; i++) {
        ctx.lineTo(points[i].x, points[i].y);
      }
      ctx.stroke();
    }
  }, [points]);

  return (
    <Modal title={assignment.name ?? 'Draw Shape Game'} onClose={onClose}>
      <div className="space-y-4">
        {/* Game info */}
        <div>
          <p className="text-sm text-muted-foreground">
            {assignment.description ?? 'Draw the target shape as accurately as possible.'}
          </p>
        </div>

        {/* Target shape info */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 border border-muted-foreground/20 rounded flex items-center justify-center">
            {/* We could render the target shape here, but for simplicity we'll just show the shape name */}
            <span className="text-xs">{assignment.shape.toUpperCase()}</span>
          </div>
          <div>
            <h3 className="font-medium">Target: {assignment.shape.toUpperCase()}</h3>
            <p className="text-xs text-muted-foreground">Draw this shape</p>
          </div>
        </div>

        {/* Timer */}
        <div className="text-center">
          <div className="text-2xl font-bold">{timeLeft.toString().padStart(2, '0')}s</div>
          <p className="text-xs text-muted-foreground">Time left</p>
        </div>

        {/* Drawing canvas */}
        <div className="relative">
          <canvas
            ref={canvasRef}
            className="border border-muted-foreground/20 rounded-md cursor-crosshair"
            width={400}
            height={300}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          />
          {/* Instructions */}
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none text-muted-foreground/50 text-sm">
            <p>Click and drag to draw</p>
          </div>
        </div>

        {/* Buttons */}
        <div className="flex flex-col sm:flex-row sm:space-x-2 space-y-2 sm:space-y-0">
          <button
            onClick={clearCanvas}
            disabled={submitting}
            className="btn-secondary w-full sm:w-auto"
          >
            Clear
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting || timeLeft === 0}
            className="btn-primary w-full sm:w-auto"
          >
            {submitting ? 'Submitting...' : 'Submit'}
          </button>
        </div>

        {/* Result */}
        {result && (
          <div className="mt-4 p-4 bg-muted-foreground/5 rounded-md text-center">
            <h3 className="font-semibold">Result</h3>
            <p className="mt-2">
              Accuracy: <span className="font-bold">{result.accuracy.toFixed(2)}%</span>
            </p>
            <p className="mt-2">
              XP Earned: <span className="font-bold">{result.awardedXp}</span>
            </p>
          </div>
        )}
      </div>
    </Modal>
  );
}