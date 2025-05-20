"use client";

import { useEffect, useState } from "react";
import { io } from "socket.io-client";
import Pagination from "./pagination";
import ReviewsTable, { Review } from "./reviews-table";
import ExportButtons from "./export-buttons";
import { Icon } from "@iconify/react/dist/iconify.js";

export default function Reviews({ url }: { url: string }) {
  const RECORD_PER_LOAD = 25;

  const [reviews, setReviews] = useState([] as Review[]);
  const [range, setRange] = useState(RECORD_PER_LOAD);
  const [page, setPage] = useState(1);
  const [isPending, setIsPending] = useState(true);

  useEffect(() => {
    setIsPending(true);
    const socket = io(process.env.NEXT_PUBLIC_SERVER_URL);
    socket.emit("ask_reviews", { url, range: [range - RECORD_PER_LOAD, range] });
    socket.on("review", (data) => setReviews((reviews) => [...reviews, data]));

    return () => {
      socket.disconnect();
    };
  }, [url, range]);

  useEffect(() => {
    if (reviews.length === range) {
      setIsPending(false);
    }
  }, [reviews, range]);

  return (
    <div className="container px-4 xl:px-20">
      <h2 className="text-2xl font-bold text-gradient mb-4">Reviews</h2>
      <ExportButtons reviews={reviews} />
      <ReviewsTable reviews={reviews.slice((page - 1) * 10, page * 10)} />
      <div className="flex justify-between">
        <div>
          Showing {(page - 1) * 10 + 1} to {Math.min(page * 10, reviews.length)} of {reviews.length} items
        </div>
        <button
          disabled={isPending}
          onClick={() => setRange(range + RECORD_PER_LOAD)}
          className="bg-formground px-4 py-2 rounded hover:bg-primary transition cursor-pointer"
        >
          {isPending ? `Loading more ${range - reviews.length} review(s)` : "Load more"}
          {isPending && <Icon icon="eos-icons:bubble-loading" width="24" height="24" className="inline ml-3" />}
        </button>
        <Pagination page={page} total={Math.ceil(reviews.length / 10)} setPage={setPage} />
      </div>
    </div>
  );
}
