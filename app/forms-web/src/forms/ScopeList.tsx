import { Cell, RowTools } from "../components/fields";
import { useDoc } from "../lib/documentStore";
import { cx } from "../lib/cx";

/**
 * The bulleted "scope of work" list. Rows can be added and removed, and each
 * row can be a bullet, a bold bullet, or an unbulleted line -- all three occur
 * in the reference documents.
 */
export function ScopeList({ list = "scope" }: { list?: string }) {
  const { rows } = useDoc();

  return (
    <ul className="bullets">
      {rows(list).map((row, i) => {
        const style = row.style ?? "bullet";
        return (
          <li
            key={i}
            className={cx(
              "row",
              style === "plain" && "bullets__item--plain",
              style === "bullet-bold" && "bold",
            )}
          >
            <RowTools list={list} index={i} />
            {style !== "plain" && (
              <span className="bullets__dot" contentEditable={false}>
                &bull;
              </span>
            )}
            <Cell
              list={list}
              index={i}
              field="text"
              variant="block"
              multiline
              placeholder="Describe the work…"
            />
          </li>
        );
      })}
    </ul>
  );
}
