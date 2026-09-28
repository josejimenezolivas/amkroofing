/** The "Initials / Date" strip, page number and running label at the foot of
 *  every agreement page. Two x-positions occur in the source, so the second
 *  pair is nudged on the pages that use the wider spacing. */
export function PageFooter({
  page,
  label,
  high = false,
  wide = false,
  cont = false,
}: {
  page?: number;
  label?: string;
  /** Page 1 sits the strip ~10pt higher than the rest. */
  high?: boolean;
  wide?: boolean;
  cont?: boolean;
}) {
  const textTop = high ? 731.9 : 742.15;
  const ruleTop = textTop - 2.6;
  const second = wide ? [473.9, 510.1] : [469.4, 505.6];
  const slots: Array<[x: number, ruleX: number, w: number, text: string]> = [
    [400.5, 398.2, 29.5, "Initials"],
    [436.7, 434.5, 21.4, "Date"],
    [second[0], second[0] - 2.3, 29.5, "Initials"],
    [second[1], second[1] - 2.2, 21.4, "Date"],
  ];

  return (
    <>
      {cont && <div className="terms__cont">Cont&rsquo;</div>}
      {label && <div className="foot__label">{label}</div>}
      {page !== undefined && <div className="foot__page">Page {page}</div>}
      {slots.map(([x, ruleX, w, text], i) => (
        <span key={i}>
          <span
            className="foot__initial-rule"
            style={{ left: `${ruleX}pt`, top: `${ruleTop}pt`, width: `${w}pt` }}
          />
          <span className="foot__initial" style={{ left: `${x}pt`, top: `${textTop}pt` }}>
            {text}
          </span>
        </span>
      ))}
    </>
  );
}
