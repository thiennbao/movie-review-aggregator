"use client";

import { useEffect, useState } from "react";
import { io } from "socket.io-client";
import Pagination from "./pagination";
import ReviewsTable, { Review } from "./reviews-table";
import ExportButtons from "./export-buttons";

export default function Reviews({ url }: { url: string }) {
  const [reviews, setReviews] = useState([] as Review[]);
  const [page, setPage] = useState(1);

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
      <ExportButtons reviews={reviews} />
      <ReviewsTable reviews={reviews.slice((page - 1) * 10, page * 10)} />
      <div className="flex justify-between">
        <div>
          Showing {(page - 1) * 10 + 1} to {Math.min(page * 10, reviews.length)} of {reviews.length} items
        </div>
        <Pagination page={page} total={Math.ceil(reviews.length / 10)} setPage={setPage} />
      </div>
    </div>
  );
}
