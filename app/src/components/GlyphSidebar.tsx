import type { GlyphBbox } from '../types';

interface Props {
  keys: string[];
  bboxes: Record<string, GlyphBbox | null>;
  selected: string | null;
  canonStatus: Record<string, boolean>;
  onSelect: (key: string) => void;
}

export function GlyphSidebar({ keys, bboxes, selected, canonStatus, onSelect }: Props) {
  return (
    <div className="panel sidebar">
      <h2>glyphs</h2>
      <ul>
        {keys.map((k) => {
          const bbox = bboxes[k];
          const hasBbox = bbox !== null;
          const hasCanon = canonStatus[k] === true;
          return (
            <li
              key={k}
              className={`${selected === k ? 'selected' : ''} ${hasCanon ? 'has-canon' : ''}`.trim()}
              onClick={() => onSelect(k)}
            >
              <span className="status">{hasCanon ? '☑' : hasBbox ? '☐' : '–'}</span>
              <span>{k}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
