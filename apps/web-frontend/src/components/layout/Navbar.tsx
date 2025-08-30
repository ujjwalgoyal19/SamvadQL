import { Button } from '@/components/ui/button';

interface NavbarProps {
  onLogout: () => void;
}

export default function Navbar({ onLogout }: NavbarProps) {
  return (
    <nav className="w-full flex items-center justify-between px-6 py-3 border-b">
      <div className="font-bold text-lg">Logo</div>
      <Button variant="outline" onClick={onLogout}>
        Logout
      </Button>
    </nav>
  );
}
