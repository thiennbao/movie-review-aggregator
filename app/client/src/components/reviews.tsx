"use client";

import { Icon } from "@iconify/react/dist/iconify.js";
import { useEffect, useState } from "react";
import { io } from "socket.io-client";

interface Review {
  user: string;
  date: string;
  aspects: [{ term: string; content: string; polarity: string }];
}

const termColors: { [key: string]: string } = {
  plot: "bg-red-500/50",
  character: "bg-amber-500/50",
  sound: "bg-emerald-500/50",
};

export default function Reviews({ url }: { url: string }) {
  const [reviews, setReviews] = useState([] as Review[]);

  useEffect(() => {
    const socket = io("localhost:5000");
    socket.emit("ask_reviews", url);
    socket.on("review", (data) => setReviews((reviews) => [...reviews, data]));
    return () => {
      socket.disconnect();
    };
  }, [url]);

  return (
    <div className="w-3/4 m-auto">
      <h2 className="text-2xl font-bold text-gradient mb-4">Reviews</h2>
      <div>Some button here</div>
      <div className="w-full text-left divide-y-1 divide-primary/50 text-sm">
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
              {review.aspects.map((aspect, index) => (
                <span key={index} className={`${termColors[aspect.term]} rounded px-1 relative group`}>
                  {aspect.content}
                  {aspect.term && (
                    <span className="bg-inherit absolute bottom-full left-0 p-2 rounded-xl hidden group-hover:block">
                      {aspect.polarity === "positive" && <Icon icon="mingcute:happy-fill" width="24" height="24" />}
                      {aspect.polarity === "neutral" && <Icon icon="garden:face-neutral-fill-16" width="24" height="24" />}
                      {aspect.polarity === "negative" && <Icon icon="mingcute:unhappy-fill" width="24" height="24" />}
                    </span>
                  )}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
