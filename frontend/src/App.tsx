import { ThemeProvider } from "next-themes";
import AppRouter from "@/routes";
import { Toaster } from "@/components/ui/sonner";

function App() {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <AppRouter />
      <Toaster />
    </ThemeProvider>
  );
}

export default App;