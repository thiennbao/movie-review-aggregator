import { Icon } from "@iconify/react/dist/iconify.js";

interface Props {
  page: number;
  total: number;
  setPage: (page: number) => void;
}

export default function Pagination({ page, total, setPage }: Props) {
  const range = calcRange(page, total);

  return (
    <div className="flex gap-1 *:min-w-8 *:h-8 *:px-2 *:flex *:justify-center *:items-center *:rounded-md *:cursor-pointer *:transition *:hover:bg-primary *:hover:text-background">
      <div onClick={() => setPage(Math.max(page - 1, 1))} className="bg-formground">
        <Icon icon="icon-park-solid:left-one" />
      </div>
      {range.map((page_idx, index) => (
        <div
          key={`${page_idx}${index}`}
          onClick={() => setPage(Number(page_idx) || page)}
          className={page == page_idx ? "bg-gradient text-background" : "bg-formground"}
        >
          {page_idx}
        </div>
      ))}
      <div className="bg-formground">
        <Icon onClick={() => setPage(Math.min(page + 1, total))} icon="icon-park-solid:right-one" />
      </div>
    </div>
  );
}

function calcRange(page: number, total: number) {
  let range: (string | number)[] = [];
  if (total <= 9) {
    range = Array.from({ length: total }, (_, i) => i + 1);
  } else {
    const left = Math.max(1, page - 2);
    const right = Math.min(total, page + 2);
    if (left > 1) range.push(1);
    if (left > 2) range.push("...");
    if (right < 6) {
      range.push(1, 2, 3, 4, 5, 6);
    } else if (left > total - 5) {
      range.push(total - 5, total - 4, total - 3, total - 2, total - 1, total);
    } else {
      range.push(...Array.from({ length: right - left + 1 }, (_, i) => left + i));
    }
    if (right < total - 1) range.push("...");
    if (right < total) range.push(total);
  }
  return range;
}
