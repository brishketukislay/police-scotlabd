import { useEffect, useState } from "react";
import { api } from "../../api";
import Modal from "../Modal";

export default function EconomyModal({onClose,pushToast}:{onClose:()=>void;pushToast:(s:string,t?:any)=>void}) {
  const [v,setV]=useState<any>(null);
  const [busy,setBusy]=useState(false);
  useEffect(()=>{api.economy().then(setV).catch(e=>pushToast(e.message,"warning"))},[]);
  if(!v)return <Modal title="Economy settings" onClose={onClose}><p className="muted">Loading…</p></Modal>;
  const set=(k:string,x:any)=>setV((a:any)=>({...a,[k]:x}));
  const save=async()=>{
    setBusy(true);
    try{
      await api.updateEconomy({jackpot_target_xp:Number(v.jackpot_target_xp),max_group_penalty_percent:Number(v.max_group_penalty_percent),max_staff_multiplier:Number(v.max_staff_multiplier),weekly_growth_cap_multiplier:Number(v.weekly_growth_cap_multiplier),group_penalties_enabled:!!v.group_penalties_enabled,multipliers_enabled:!!v.multipliers_enabled});
      pushToast("Economy saved");
      onClose();
    }catch(e:any){
      pushToast(e.message,"warning");
    }finally{
      setBusy(false);
    }
  };
  return <Modal title="Economy settings" onClose={onClose}>
    <div className="form-grid">
      <label>Jackpot target XP<input type="number" value={v.jackpot_target_xp} onChange={e=>set("jackpot_target_xp",e.target.value)}/></label>
      <label>Max group penalty %<input type="number" value={v.max_group_penalty_percent} onChange={e=>set("max_group_penalty_percent",e.target.value)}/></label>
      <label>Max staff multiplier<input type="number" step="0.1" value={v.max_staff_multiplier} onChange={e=>set("max_staff_multiplier",e.target.value)}/></label>
      <label>Weekly growth cap multiplier<input type="number" step="0.1" value={v.weekly_growth_cap_multiplier} onChange={e=>set("weekly_growth_cap_multiplier",e.target.value)}/></label>
      <label>Group penalties<select value={String(!!v.group_penalties_enabled)} onChange={e=>set("group_penalties_enabled",e.target.value==="true")}><option value="true">Enabled</option><option value="false">Disabled</option></select></label>
      <label>Multipliers<select value={String(!!v.multipliers_enabled)} onChange={e=>set("multipliers_enabled",e.target.value==="true")}><option value="true">Enabled</option><option value="false">Disabled</option></select></label>
    </div>
    <button className="primary-btn wide" disabled={busy} onClick={save}>{busy?"Saving…":"Save economy"}</button>
  </Modal>;
}
