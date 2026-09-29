import { useEffect, useRef, type ReactNode } from "react";

interface ConfirmDialogProps {
  title: string;
  confirmLabel: string;
  children: ReactNode;
  onConfirm: () => void;
  /** Also called on Escape or a click outside the dialog. */
  onCancel: () => void;
}

/** A themed, modal yes/no question. Cancel has focus, so Enter never destroys anything. */
export function ConfirmDialog({ title, confirmLabel, children, onConfirm, onCancel }: ConfirmDialogProps) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    ref.current?.showModal();
  }, []);

  return (
    <dialog
      ref={ref}
      className="confirm"
      aria-labelledby="confirm-title"
      onClose={onCancel}
      onClick={(e) => e.target === e.currentTarget && ref.current?.close()}
    >
      <div className="confirm__body">
        <h2 id="confirm-title" className="confirm__title">
          {title}
        </h2>
        <p className="confirm__message">{children}</p>
        <div className="confirm__actions">
          <button type="button" autoFocus onClick={() => ref.current?.close()}>
            Cancel
          </button>
          <button type="button" className="confirm__danger" onClick={onConfirm}>
            {confirmLabel}
          </button>
        </div>
      </div>
    </dialog>
  );
}
