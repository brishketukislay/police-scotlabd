import { Check } from "lucide-react";

function PointRequests({data, openPointRequests, pushToast, refresh}: {data: any; openPointRequests: () => void; pushToast: (s: string, t?: any) => void; refresh: () => Promise<void>}) {
  const rows = data?.pointRequests ?? [];
  return (
    <div className="page">
      <div className="section-heading">
        <div>
          <span className="eyebrow">STAFF REVIEW QUEUE</span>
          <h2>Points requests</h2>
        </div>
        <button className="primary-btn" onClick={openPointRequests}>
          <Check size={16} /> Review requests
        </button>
      </div>
      <div className="panel">
        <div className="panel-head">
          <h3>{rows.length} pending request{rows.length === 1 ? "" : "s"}</h3>
          <span className="status at-risk">Approval required</span>
        </div>
        {rows.length === 0 ? (
          <p className="muted">No points requests are waiting for review.</p>
        ) : (
          rows.map((r: any) => (
            <div className="setting-line" key={r.id}>
              <div>
                <b>{r.gamertag}</b>
                <small style={{display: "block", color: "#70808e"}}>
                  +{r.requested_xp.toLocaleString()} XP · {r.reason}
                </small>
              </div>
              <button className="secondary-btn" onClick={openPointRequests}>
                Review
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default PointRequests;