import Modal from "../Modal";

export default function DrawingGameManagerModal({onClose}:{onClose:()=>void}) {
  return <Modal title="Drawing Games Manager" onClose={onClose}>
    <p className="muted">Drawing games management coming soon.</p>
  </Modal>;
}
