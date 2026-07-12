import AppRouter from "@/routes";
import { Toaster } from "@/components/ui/sonner";

function App() {
  return (
    <>
      <AppRouter />
      <Toaster />
    </>
  );
}

export default App;