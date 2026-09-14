function Stat({icon, label, value, delta}: {icon?: any; label: string; value: string; delta: string}) {
  return (
    <div className="stat">
      <div className="stat-icon">{icon}</div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{delta}</small>
      </div>
    </div>
  );
}

export default Stat;