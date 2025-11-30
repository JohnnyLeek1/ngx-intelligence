import { Moon, Sun, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useTheme } from '@/providers/ThemeProvider';

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          <span className="sr-only">Toggle theme</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem
          onClick={() => setTheme('light')}
          aria-checked={theme === 'light'}
        >
          <div className="flex items-center justify-between w-full">
            <span className={theme === 'light' ? 'font-semibold' : ''}>Light</span>
            {theme === 'light' && <Check className="h-4 w-4 ml-2" />}
          </div>
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => setTheme('dark')}
          aria-checked={theme === 'dark'}
        >
          <div className="flex items-center justify-between w-full">
            <span className={theme === 'dark' ? 'font-semibold' : ''}>Dark</span>
            {theme === 'dark' && <Check className="h-4 w-4 ml-2" />}
          </div>
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => setTheme('system')}
          aria-checked={theme === 'system'}
        >
          <div className="flex items-center justify-between w-full">
            <span className={theme === 'system' ? 'font-semibold' : ''}>System</span>
            {theme === 'system' && <Check className="h-4 w-4 ml-2" />}
          </div>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
