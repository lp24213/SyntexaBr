import { redirect } from "next/navigation";
import { encryptedPath } from "../lib/routes";

export default function HomePage() {
  redirect(encryptedPath("chat"));
}
