import { useEffect, useState } from "react";
import { Check } from "lucide-react";
import { api } from "../../api";
import Modal from "../Modal";
import RotateIcon from "../RotateIcon";

export default function PointRequestsModal({onClose,pushToast,refresh}:{onClose:()=>void;pushToast:(s:string,t?:any)=>void;refresh:()=>Promise<void>}) {
  const [rows,setRows]=useState<any[]>([]);
  const [busy,setBusy]=useState<number|null>(null);
  const load=async()=>{
    try{
      setRows(await api.pointRequests("pending"));
    }catch(e:any){
      pushToast(e.message,"warning");
    }
  };
  useEffect(()=>{load()},[]);
  const decide=async(r:any,approved:boolean)=>{
    let amount=r.requested_xp;
    let note="";
    if(approved){
      const x=window.prompt(`Approve XP for ${r.gamertag}`,String(r.requested_xp));
      if(x===null)return;
      amount=Number(x);
      if(!Number.isFinite(amount)||amount<1||amount>5000){
        pushToast("XP must be between 1 and 5,000","warning");
        return;
      }
      note=window.prompt("Optional review note","")||"";
    }else note=window.prompt("Reason for rejection","")||"Request declined by youth worker.";
    setBusy(r.id);
    try{
      if(approved)await api.approvePointRequest(r.id,{approved_xp:amount,review_note:note||null});
      else await api.rejectPointRequest(r.id,{review_note:note});
      pushToast(approved?`+${amount.toLocaleString()} XP approved`:`Request #${r.id} rejected`);
      await load();
      await refresh();
    }catch(e:any){
      pushToast(e.message,"warning");
    }finally{
      setBusy(null);
    }
  };
  return <Modal title="Points requests" onClose={onClose}>
    <div className="panel inset">
      <div className="panel-head">
        <h3>Pending review</h3>
        <button className="ghost-btn" onClick={load}><RotateIcon/></button>
      </div>
      {rows.length===0?<p className="muted">Nothing waiting for review.</p>:rows.map(r=><div className="request-card" key={r.id}>
        <div className="request-card-head">
          <div><b>{r.gamertag}</b><small>Request #{r.id} · {r.created_at?new Date(r.created_at).toLocaleString():""}</small></div>
          <strong>+{r.requested_xp.toLocaleString()} XP</strong>
        </div>
        <p>{r.reason}</p>
        <div className="nom-actions">
          <button className="primary-btn" disabled={busy===r.id} onClick={()=>decide(r,true)}><Check size={15}/> Approve</button>
          <button className="ghost-btn" disabled={busy===r.id} onClick={()=>decide(r,false)}>Reject</button>
        </div>
      </div>)}
    </div>
  </Modal>
}
