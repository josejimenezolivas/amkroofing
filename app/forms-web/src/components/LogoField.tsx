import { useRef, type CSSProperties } from "react";

import defaultLogo from "../assets/amk-logo.png?inline";
import { useDoc } from "../lib/documentStore";
import { cx } from "../lib/cx";

import "./logo.css";

/**
 * The company mark. Click it to swap in your own artwork; the image is stored
 * with the document as a data URL, so it travels into the PDF and Word export
 * the same way the built-in logo does.
 */
export function LogoField({
  className,
  style,
  alt = "Company logo",
}: {
  className?: string;
  style?: CSSProperties;
  alt?: string;
}) {
  const { data, setImage, readOnly } = useDoc();
  const input = useRef<HTMLInputElement>(null);
  const custom = data.images?.logo;

  const choose = (file: File | undefined) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => setImage("logo", String(reader.result));
    reader.readAsDataURL(file);
  };

  return (
    <>
      <img
        className={cx("logo", !readOnly && "logo--editable", className)}
        style={style}
        src={custom || defaultLogo}
        alt={alt}
        title={readOnly ? undefined : "Click to replace the logo"}
        onClick={readOnly ? undefined : () => input.current?.click()}
      />
      {!readOnly && (
        <input
          ref={input}
          type="file"
          accept="image/png,image/jpeg,image/svg+xml,image/webp"
          className="logo__input"
          onChange={(e) => {
            choose(e.target.files?.[0]);
            e.target.value = "";
          }}
        />
      )}
    </>
  );
}
