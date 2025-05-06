import { Icon } from "@iconify/react/dist/iconify.js";

export default function Footer() {
  return (
    <div className="flex flex-wrap justify-center items-center gap-2 my-10">
      <span>This website is made with</span>
      <Icon icon="solar:heart-bold" className="text-2xl text-primary" />
      <span>by some random HCMUS students</span>
    </div>
  );
}
