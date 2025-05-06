import * as xlsx from "xlsx";
import { Review } from "./reviews-table";
import Papa from "papaparse";

export default function ExportButtons({ reviews }: { reviews: Review[] }) {
  return (
    <div className="flex gap-2 *:text-background *:px-4 *:py-1 *:rounded *:cursor-pointer">
      <button onClick={() => handleCopy(reviews)} className="bg-primary">
        Copy
      </button>
      <button onClick={() => handleExcel(reviews)} className="bg-secondary">
        Excel
      </button>
      <button onClick={() => handleCsv(reviews)} className="bg-secondary">
        CSV
      </button>
    </div>
  );
}

const handleCopy = (reviews: Review[]) => {
  const text = JSON.stringify(reviews, null, 2);
  navigator.clipboard.writeText(text);
};

const handleExcel = (reivews: Review[]) => {
  const worksheet = xlsx.utils.json_to_sheet(reivews);
  const workbook = xlsx.utils.book_new();
  xlsx.utils.book_append_sheet(workbook, worksheet, "Sheet1");
  xlsx.writeFile(workbook, "data.xlsx");
  console.log(workbook);
};

const handleCsv = (reviews: Review[]) => {
  const csv = Papa.unparse(reviews);
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "data.csv";
  a.click();
};
