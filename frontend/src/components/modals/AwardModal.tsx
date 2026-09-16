import { useState } from "react";
import { Plus } from "lucide-react";
import { api } from "../../api";
import Modal from "../Modal";

export default function AwardModal({players,selected,setSelected,onClose,pushToast}:{players:any[];selected:any;setSelected:(p:any)=>void;onClose:()=>void;pushToast:(s:string,t?:any)=>void}) {
  const [pick,setPick]=useState(selected?.id??players[0]?.id??"");
  const [amount,setAmount]=useState(500);
  const [reason,setReason]=useState("Positive participation");
  return <Modal title="Award Points" onClose={onClose}>
    <div className="form-grid">
      <label>Player<select value={pick} onChange={e=>{setPick(Number(e.target.value));setSelected(players.find(p=>p.id===Number(e.target.value)))}}>{players.map(p=><option key={p.id} value={p.id}>{p.gamertag}</option>)}</select></label>
      <label>Amount<input type="number" value={amount} onChange={e=>setAmount(Number(e.target.value))}/></label>
      <label>Reason<textarea value={reason} onChange={e=>setReason(e.target.value)}/></label>
    </div>
    <button className="primary-btn wide" onClick={async()=>{try{await api.awardXp(Number(pick),amount,reason);pushToast(`+${amount.toLocaleString()} XP awarded`);onClose();}catch(e:any){pushToast(e.message,"warning");}}}><Plus size={17}/> Award XP</button>
  </Modal>;
}
