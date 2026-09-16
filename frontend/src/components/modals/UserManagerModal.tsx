import { useState } from "react";
import { Plus } from "lucide-react";
import { api } from "../../api";
import Modal from "../Modal";

export default function UserManagerModal({users,onClose,refresh,pushToast}:{users:any[];onClose:()=>void;refresh:()=>Promise<void>;pushToast:(s:string,t?:any)=>void}) {
  const [editing,setEditing]=useState<any>(null);
  const [form,setForm]=useState<any>({username:"",password:"",role:"player",display_name:"",gamertag:"",avatar:"avatar-01",group_id:"",public_visible:true});
  const [busy,setBusy]=useState(false);
  const set=(k:string,v:any)=>setForm((x:any)=>({...x,[k]:v}));
  const open=(u:any)=>{setEditing(u);setForm({username:u.username,password:"",role:u.role,display_name:u.display_name??"",gamertag:u.player?.gamertag??"",avatar:u.player?.avatar??"avatar-01",group_id:u.player?.group_id??"",public_visible:u.player?.public_visible??true})};
  const create=()=>{setEditing(null);setForm({username:"",password:"",role:"player",display_name:"",gamertag:"",avatar:"avatar-01",group_id:"",public_visible:true})};
  const save=async()=>{
    setBusy(true);
    try{
      const body:any={username:form.username,role:form.role,display_name:form.display_name||null};
      if(form.password)body.password=form.password;
      if(form.role==="player"){body.gamertag=form.gamertag;body.avatar=form.avatar;body.public_visible=!!form.public_visible;if(form.group_id!=="")body.group_id=Number(form.group_id)}
      if(editing)await api.updateUser(editing.id,body);
      else await api.createUser({...body,password:form.password,active:true});
      pushToast(editing?"Account updated":"User created");
      await refresh();
      if(!editing)create();
    }catch(e:any){
      pushToast(e.message,"warning");
    }finally{
      setBusy(false);
    }
  };
  const action=async(u:any,kind:string)=>{try{if(kind==="pause")await api.pauseUser(u.id);if(kind==="reactivate")await api.reactivateUser(u.id);if(kind==="suspend"&&u.player)await api.suspendPlayer(u.player.id);if(kind==="unsuspend"&&u.player)await api.unsuspendPlayer(u.player.id);pushToast(kind+" complete");await refresh();}catch(e:any){pushToast(e.message,"warning");}};
  return <Modal title="Manage accounts" onClose={onClose}>
    <div className="user-manager">
      <div className="section-heading">
        <span className="eyebrow">ADMIN ONLY</span>
        <button className="primary-btn" onClick={create}><Plus size={15}/> New user</button>
      </div>
      <div className="form-grid">
        <label>Username<input value={form.username} onChange={e=>set("username",e.target.value)} /></label>
        <label>Role<select value={form.role} onChange={e=>set("role",e.target.value)}><option value="player">Young person</option><option value="youth_worker">Youth worker</option><option value="admin">Admin</option></select></label>
        <label>Password {editing&&<small>(leave blank to keep current)</small>}<input type="password" value={form.password} onChange={e=>set("password",e.target.value)} placeholder="Minimum 10 characters" /></label>
        {form.role==="player"&&<><label>Gamertag<input value={form.gamertag} onChange={e=>set("gamertag",e.target.value)} /></label><label>Group ID<input type="number" value={form.group_id} onChange={e=>set("group_id",e.target.value)} placeholder="Optional" /></label><label>Avatar<input value={form.avatar} onChange={e=>set("avatar",e.target.value)}/></label></>}
      </div>
      <button className="primary-btn wide" disabled={busy||!form.username||(!editing&&!form.password)} onClick={save}>{busy?"Saving…":editing?"Save changes":"Create user"}</button>
      <div className="panel inset">
        <div className="panel-head">
          <h3>Accounts</h3>
          <span className="count-pill">{users.length}</span>
        </div>
        {users.map((u:any)=><div className="setting-line" key={u.id}>
          <div><b>{u.username}</b><small style={{display:"block",color:"#70808e"}}>{u.role} · {u.player?.gamertag??u.display_name??"Staff account"}</small></div>
          <div className="nom-actions">
            <span className={`status ${u.active?"":"inactive"}`}>{u.active?"Active":"Paused"}</span>
            <button className="ghost-btn" onClick={()=>open(u)}>Edit</button>
            {u.active ? (
  <button className="ghost-btn" onClick={() => action(u, "pause")}>
    Pause
  </button>
) : (
  <button className="ghost-btn" onClick={() => action(u, "reactivate")}>
    Reactivate
  </button>
)}
{u.player && (
  u.player.suspended ? (
    <button className="ghost-btn" onClick={() => action(u, "unsuspend")}>
      Unsuspend
    </button>
  ) : (
    <button className="ghost-btn" onClick={() => action(u, "suspend")}>
      Suspend
    </button>
  )
)}
          </div>
        </div>)}
      </div>
    </div>
  </Modal>
}
