import TeamsSidebar from "../components/TeamsSidebar";
import ChannelList from "../components/ChannelList";
import ChatArea from "../components/ChatArea";

export default function MainLayout() {
  return (
    <div className="flex h-screen w-screen overflow-hidden">
      <TeamsSidebar />
      <ChannelList />
      <ChatArea />
    </div>
  );
}
