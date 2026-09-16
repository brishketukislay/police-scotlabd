import { useEffect, useState } from "react";
import { QRCodeCanvas } from "qrcode.react";
import { api } from "../../api";
import Modal from "../Modal";

export default function PlayerQrModal({onClose,pushToast}:{onClose:()=>void;pushToast:(s:string,t?:any)=>void}) {
  const [token,setToken]=useState("");
  const [busy,setBusy]=useState(true);
  const load=async()=>{
    setBusy(true);
    try{
      const r=await api.rotatePlayerQr();
      setToken(r.token);
    }catch(e:any){
      pushToast(e.message,"warning");
    }finally{
      setBusy(false);
    }
  };
  useEffect(()=>{load()},[]);
  const value=token?`${window.location.origin}/request-points?token=${encodeURIComponent(token)}`:"";
  return <Modal title="My Quest QR" onClose={onClose}>
    <div className="qr-modal">{busy?<div className="loader-ring"/>:token?<><div className="qr-frame"><QRCodeCanvas value={value} size={230}/></div><h3>Show this code</h3><p className="muted">The code does not reveal the player's name. Scanning opens the extra-XP request form.</p><button className="ghost-btn wide" onClick={load}>Rotate QR</button></>:<p className="muted">Unable to generate your QR.</p>}</div>
  </Modal>
}
