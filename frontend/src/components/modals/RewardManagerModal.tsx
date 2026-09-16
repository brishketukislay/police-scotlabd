import { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { api } from "../../api";
import Modal from "../Modal";

export default function RewardManagerModal({onClose,pushToast}:{onClose:()=>void;pushToast:(s:string,t?:any)=>void}) {
  const [games,setGames]=useState<any[]>([]);
  const [targets,setTargets]=useState<any>({players:[],groups:[]});
  const [form,setForm]=useState<any>({name:"Spin the Wheel",description:"",game_type:"wheel",prize_values:"500,1000,2000",starts_at:"",ends_at:"",active:true,show_upcoming:true});
  const [target,setTarget]=useState("player");
  const [targetId,setTargetId]=useState("");
  const load=async()=>{
    try{
      const [g,t]=await Promise.all([api.adminRewardGames(),api.rewardGameTargets()]);
      setGames(g);
      setTargets(t);
    }catch(e:any){
      pushToast(e.message,"warning");
    }
  };
  useEffect(()=>{load()},[]);
  const set=(k:string,x:any)=>setForm((a:any)=>({...a,[k]:x}));
  const create=async()=>{
    try{
      await api.createRewardGame({...form,prize_values:form.prize_values.split(",").map((x:string)=>Number(x.trim())).filter((x:number)=>Number.isFinite(x)),starts_at:form.starts_at||null,ends_at:form.ends_at||null});
      pushToast("Reward game created");
      await load();
    }catch(e:any){
      pushToast(e.message,"warning");
    }
  };
  const grant=async(game:any)=>{
    if(!targetId)return;
    try{
      await api.grantRewardGame(game.id,target==="player"?{player_id:Number(targetId)}:{group_id:Number(targetId)});
      pushToast("Reward entitlement granted");
    }catch(e:any){
      pushToast(e.message,"warning");
    }
  };
  const toggle=async(g:any)=>{
    try{
      await api.updateRewardGame(g.id,{active:!g.active});
      pushToast(g.active?"Reward game paused":"Reward game activated");
      await load();
    }catch(e:any){
      pushToast(e.message,"warning");
    }
  };
  return <Modal title="Reward games" onClose={onClose}>
    <div className="form-grid">
      <label>Name<input value={form.name} onChange={e=>set("name",e.target.value)}/></label>
      <label>Description<textarea value={form.description} onChange={e=>set("description",e.target.value)}/></label>
      <label>Prize values (XP, comma separated)<input value={form.prize_values} onChange={e=>set("prize_values",e.target.value)} placeholder="500,1000,2000"/></label>
      <label>Starts at<input type="datetime-local" value={form.starts_at} onChange={e=>set("starts_at",e.target.value)}/></label>
      <label>Ends at<input type="datetime-local" value={form.ends_at} onChange={e=>set("ends_at",e.target.value)}/></label>
    </div>
    <button className="primary-btn wide" onClick={create}><Plus size={15}/> Create reward game</button>
    <div className="panel inset" style={{marginTop:12}}>
      <div className="panel-head">
        <h3>Grant entitlement</h3>
      </div>
      <div className="form-grid">
        <label>Target<select value={target} onChange={e=>{setTarget(e.target.value);setTargetId("")}}><option value="player">Player</option><option value="group">Group</option></select></label>
        <label>{target==="player" ? "Player" : "Group"}<select value={targetId} onChange={e=>setTargetId(e.target.value)}><option value="">Select…</option>{target==="player" ? targets.players.map((p:any)=><option key={p.id} value={p.id}>{p.gamertag}</option>) : targets.groups.map((g:any)=><option key={g.id} value={g.id}>{g.name}</option>)}</select></label>
      </div>
      {games.map((g)=>(<div className="setting-line" key={g.id}>
        <span><b>{g.name}</b><small style={{display:"block",color:"#70808e"}}>{g.active?"Active":"Paused"} · {g.available_entitlements} available · prizes hidden from players</small></span>
        <div className="nom-actions">
          <button className="ghost-btn" onClick={()=>toggle(g)}>{g.active?"Pause":"Activate"}</button>
          <button className="secondary-btn" disabled={!targetId||!g.active} onClick={()=>grant(g)}>Grant</button>
        </div>
      </div>))}
    </div>
  </Modal>;
}
