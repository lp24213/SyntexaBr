import ChatPage from "../../../../app/chat/page";

export async function generateStaticParams() {
  return [
    { locale: "pt-BR" },
    { locale: "en-US" },
    { locale: "es-ES" },
    { locale: "zh-CN" },
  ];
}

export default function LocaleChatPage({ params }) {
  return <ChatPage />;
}
