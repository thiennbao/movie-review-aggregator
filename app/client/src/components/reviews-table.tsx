import { Icon } from "@iconify/react/dist/iconify.js";

export interface Review {
  id: number;
  url: string;
  user: string;
  date: string;
  content: string;
  results: [
    {
      aspects: string[];
      opinions: string[];
      polarities: string[];
      positions_aspects: number[];
      positions_opinions: number[][];
      content: string;
    }
  ];
}

const polarityColors: { [key: string]: string } = {
  negative: "bg-red-500/50",
  neutral: "bg-amber-500/50",
  positive: "bg-emerald-500/50",
};

export default function ReviewsTable({ reviews }: { reviews: Review[] }) {
  return (
    <div className="my-8 w-full text-left divide-y-1 divide-primary/50 text-sm">
      <div className="grid grid-cols-20 font-bold text-gradient *:p-4">
        <div>#</div>
        <div className="col-span-2">User</div>
        <div className="col-span-2">Date</div>
        <div className="col-span-15">Review</div>
      </div>
      {reviews.map((review, index) => (
        <div key={index} className="grid grid-cols-20 *:m-4">
          <div>{index + 1}</div>
          <div className="col-span-2">{review.user}</div>
          <div className="col-span-2">{review.date}</div>
          <div className="col-span-15 text-justify">
            {review.results.map((result, index) => (
              <span key={index} className={`rounded px-1 relative group ${result.polarities[0] !== "none" && "bg-formground"} mr-1`}>
                {result.content}
                {result.aspects.map((aspect: string, index: number) => (
                  <span key={index} className={`${polarityColors[result.polarities[index]]} px-1 ml-1 rounded`}>
                    {result.polarities[index] === "positive" && (
                      <Icon icon="mingcute:happy-fill" width="16" height="16" className="inline align-middle mr-1" />
                    )}
                    {result.polarities[index] === "neutral" && (
                      <Icon icon="garden:face-neutral-fill-16" width="14" height="14" className="inline align-middle mr-1" />
                    )}
                    {result.polarities[index] === "negative" && (
                      <Icon icon="mingcute:unhappy-fill" width="16" height="16" className="inline align-middle mr-1" />
                    )}
                    Aspect: {aspect}. Opinion: {result.opinions[index]}
                  </span>
                ))}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
