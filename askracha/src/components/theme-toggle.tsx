"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

export function ThemeToggle() {
  // useTheme hook provides the current theme and a function to set the theme
  const { theme, setTheme } = useTheme();
  // State to track if the component is mounted to prevent hydration mismatches
  const [mounted, setMounted] = useState(false);

  // Set mounted to true once the component has mounted on the client side
  useEffect(() => {
    setMounted(true);
  }, []);

  // Render a placeholder div while the component is not yet mounted to avoid UI flickering
  if (!mounted) {
    return (
      <div className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground h-10 w-10 animate-pulse bg-muted" />
    );
  }

  // Function to toggle between the three themes: light, dark, and storacha
  const toggleTheme = () => {
    if (theme === "light") {
      setTheme("dark");
    } else if (theme === "dark") {
      setTheme("storacha"); // Transition from dark to the custom 'storacha' theme
    } else {
      setTheme("light"); // Transition from 'storacha' back to light
    }
  };

  // Render the button based on the current theme
  return (
    <button
      onClick={toggleTheme}
      className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground h-10 w-10"
    >
      {/* Display appropriate icon based on the current theme */}
      {theme === "dark" ? (
        <Moon className="w-5 h-5" /> // Moon icon for dark theme
      ) : theme === "light" ? (
        <Sun className="w-5 h-5" /> // Sun icon for light theme
      ) : (
        // You can choose a different icon for the 'storacha' theme,
        // or reuse one of the existing ones. Here, Moon is reused.
        <Moon className="w-5 h-5" /> // Moon icon for storacha theme
      )}
      <span className="sr-only">Toggle theme</span>
    </button>
  );
}
