import { useState } from "react";
import { ArrowUpRight } from "lucide-react";

function Login({onLogin,onPublic,error}:{onLogin:(u:string,p:string)=>void;onPublic:()=>void;error:string}) {
  const [u, setU] = useState("");
  const [p, setP] = useState("");

  return (
    <div className="login-screen">
      <div className="login-card">
        <div className="brand centered">
          <div className="brand-mark">Q</div>
          <div>
            <strong>QUEST<span>HUB</span></strong>
            <small>CUMBERNAULD CLIMB</small>
          </div>
        </div>
        <div className="eyebrow">NEW FRONTEND / API CONNECTED</div>
        <h1>Enter the climb.</h1>
        <p>Use an account from the supplied FastAPI backend, or preview the public dashboard.</p>
        {error && <div className="api-error">{error}</div>}
        <label>
          Username
          <input
            value={u}
            onChange={e => setU(e.target.value)}
            placeholder="admin / youthworker / player01"
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={p}
            onChange={e => setP(e.target.value)}
            placeholder="Password"
            onKeyDown={e => e.key === "Enter" && onLogin(u, p)}
          />
        </label>
        <button className="primary-btn wide" onClick={() => onLogin(u, p)}>
          Sign in <ArrowUpRight size={15} />
        </button>
        <button className="ghost-btn wide" onClick={onPublic}>
          View public dashboard
        </button>
        <small className="login-note">
          Sessions use the backend's HttpOnly cookie. No token is stored in localStorage.
        </small>
      </div>
    </div>
  );
}

export default Login;