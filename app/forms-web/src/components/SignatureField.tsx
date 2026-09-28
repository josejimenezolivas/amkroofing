import { useEffect, useRef, useState } from "react";

import { useDoc } from "../lib/documentStore";

const PAD_WIDTH = 640;
const PAD_HEIGHT = 200;

/**
 * A signature slot sized in points so it drops straight onto a ruled line.
 * Drawing happens in a modal at 2x resolution; the result is stored as a
 * transparent PNG data URL, which survives HTML serialization for export.
 */
export function SignatureField({
  name,
  width,
  height,
  label,
}: {
  name: string;
  width: number;
  height: number;
  label: string;
}) {
  const { data, setSignature, readOnly } = useDoc();
  const [open, setOpen] = useState(false);
  const value = data.signatures[name];

  return (
    <>
      <span
        className="signature"
        style={{ width: `${width}pt`, height: `${height}pt` }}
      >
        {value ? (
          <img className="signature__img" src={value} alt={label} />
        ) : null}
        {!readOnly && (
          <button
            type="button"
            className="signature__btn"
            onClick={() => setOpen(true)}
          >
            {value ? "Re-sign" : "Sign"}
          </button>
        )}
      </span>
      {open && (
        <SignatureModal
          label={label}
          onCancel={() => setOpen(false)}
          onClear={() => {
            setSignature(name, "");
            setOpen(false);
          }}
          onSave={(url) => {
            setSignature(name, url);
            setOpen(false);
          }}
        />
      )}
    </>
  );
}

function SignatureModal({
  label,
  onSave,
  onClear,
  onCancel,
}: {
  label: string;
  onSave: (dataUrl: string) => void;
  onClear: () => void;
  onCancel: () => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const drawing = useRef(false);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.scale(2, 2);
    ctx.lineWidth = 2.2;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.strokeStyle = "#111827";
  }, []);

  const pointAt = (e: React.PointerEvent<HTMLCanvasElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    return {
      x: ((e.clientX - rect.left) / rect.width) * PAD_WIDTH,
      y: ((e.clientY - rect.top) / rect.height) * PAD_HEIGHT,
    };
  };

  const ctxOf = () => canvasRef.current?.getContext("2d") ?? null;

  return (
    <div className="modal" role="dialog" aria-label={`Sign: ${label}`}>
      <div className="modal__panel">
        <h2 className="modal__title">{label}</h2>
        <canvas
          ref={canvasRef}
          className="modal__canvas"
          width={PAD_WIDTH * 2}
          height={PAD_HEIGHT * 2}
          style={{ width: PAD_WIDTH, height: PAD_HEIGHT }}
          onPointerDown={(e) => {
            e.currentTarget.setPointerCapture(e.pointerId);
            const ctx = ctxOf();
            if (!ctx) return;
            const { x, y } = pointAt(e);
            ctx.beginPath();
            ctx.moveTo(x, y);
            drawing.current = true;
            setDirty(true);
          }}
          onPointerMove={(e) => {
            if (!drawing.current) return;
            const ctx = ctxOf();
            if (!ctx) return;
            const { x, y } = pointAt(e);
            ctx.lineTo(x, y);
            ctx.stroke();
          }}
          onPointerUp={() => {
            drawing.current = false;
          }}
        />
        <p className="modal__hint">Draw your signature above.</p>
        <div className="modal__actions">
          <button
            type="button"
            onClick={() => {
              const canvas = canvasRef.current;
              const ctx = ctxOf();
              if (canvas && ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
              setDirty(false);
            }}
          >
            Clear pad
          </button>
          <button type="button" onClick={onClear}>
            Remove signature
          </button>
          <span className="modal__spacer" />
          <button type="button" onClick={onCancel}>
            Cancel
          </button>
          <button
            type="button"
            className="primary"
            disabled={!dirty}
            onClick={() => {
              const canvas = canvasRef.current;
              if (canvas) onSave(canvas.toDataURL("image/png"));
            }}
          >
            Apply signature
          </button>
        </div>
      </div>
    </div>
  );
}
